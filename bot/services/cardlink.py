import hashlib
import logging
from typing import Any

import httpx

from bot.config import settings
from bot.database.models import User

logger = logging.getLogger(__name__)

CARDLINK_API_URL = "https://cardlink.link/api/v1/"

# payment_method в Cardlink: BANK_CARD | SBP. Маппинг со способов оплаты на форме.
CARDLINK_METHOD_SBP = "SBP"
CARDLINK_METHOD_BANK_CARD = "BANK_CARD"


class CardlinkApiError(Exception):
    def __init__(self, message: str, *, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.response = response


def _md5_upper(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest().upper()


def payment_signature(out_sum: str, inv_id: str) -> str:
    """Подпись для Success/Fail редиректа и Result postback.

    strtoupper(md5(OutSum . ":" . InvId . ":" . apiToken))
    """
    return _md5_upper(f"{out_sum}:{inv_id}:{settings.cardlink_api_token}")


def verify_payment_signature(out_sum: str, inv_id: str, signature: str) -> bool:
    if not signature:
        return False
    return payment_signature(out_sum, inv_id) == signature.upper()


def refund_signature(amount: str, currency: str, bill_id: str, payment_id: str, refund_id: str) -> str:
    """strtoupper(md5(Amount . ":" . Currency . ":" . BillId . ":" . PaymentId . ":" . Id . ":" . apiToken))"""
    return _md5_upper(
        f"{amount}:{currency}:{bill_id}:{payment_id}:{refund_id}:{settings.cardlink_api_token}"
    )


def verify_refund_signature(
    amount: str, currency: str, bill_id: str, payment_id: str, refund_id: str, signature: str
) -> bool:
    if not signature:
        return False
    return refund_signature(amount, currency, bill_id, payment_id, refund_id) == signature.upper()


def chargeback_signature(bill_id: str, payment_id: str, chargeback_id: str) -> str:
    """strtoupper(md5(BillId . ":" . PaymentId . ":" . Id . ":" . apiToken))"""
    return _md5_upper(f"{bill_id}:{payment_id}:{chargeback_id}:{settings.cardlink_api_token}")


def verify_chargeback_signature(
    bill_id: str, payment_id: str, chargeback_id: str, signature: str
) -> bool:
    if not signature:
        return False
    return chargeback_signature(bill_id, payment_id, chargeback_id) == signature.upper()


def payment_method_from_freekassa(pay_method: int) -> str | None:
    """Способы с формы Freekassa → способ Cardlink. None = пользователь выберет сам."""
    if pay_method in (44, 42):
        return CARDLINK_METHOD_SBP
    if pay_method in (36, 12):
        return CARDLINK_METHOD_BANK_CARD
    return None


def payer_email_for_user(user: User) -> str | None:
    if user.email:
        return user.email
    return None


def _payment_url_from_response(body: dict[str, Any]) -> str:
    return str(body.get("link_page_url") or body.get("link_url") or "").strip()


async def create_bill(
    amount: float,
    order_id: str,
    *,
    description: str | None = None,
    payer_email: str | None = None,
    payment_method: str | None = None,
    custom: str | None = None,
) -> str:
    """Создаёт счёт в Cardlink и возвращает ссылку на оплату (link_page_url)."""
    data: dict[str, Any] = {
        "amount": f"{amount:.2f}",
        "shop_id": settings.cardlink_shop_id,
        "order_id": order_id,
        "type": "normal",
        "currency_in": "RUB",
        "locale": "ru",
        "success_url": settings.cardlink_success_url(),
        "fail_url": settings.cardlink_fail_url(),
    }
    if description:
        data["description"] = description
    if payer_email:
        data["payer_data[email]"] = payer_email
    if payment_method:
        data["payment_method"] = payment_method
    if custom:
        data["custom"] = custom

    headers = {"Authorization": f"Bearer {settings.cardlink_api_token}"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{CARDLINK_API_URL}bill/create",
                data=data,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        logger.exception("Cardlink API request failed")
        raise CardlinkApiError("Cardlink API request failed") from exc

    try:
        body = response.json()
    except ValueError as exc:
        logger.error("Cardlink API invalid JSON: %s", response.text[:500])
        raise CardlinkApiError("Cardlink API returned invalid JSON") from exc

    success = str(body.get("success")).lower() == "true"
    if response.status_code >= 400 or not success:
        message = body.get("message") or body.get("error") or f"HTTP {response.status_code}"
        logger.error("Cardlink create bill failed: %s %s", message, body)
        raise CardlinkApiError(str(message), response=body)

    pay_url = _payment_url_from_response(body)
    if not pay_url:
        logger.error("Cardlink create bill missing payment URL: %s", body)
        raise CardlinkApiError("Cardlink did not return payment URL", response=body)

    return pay_url
