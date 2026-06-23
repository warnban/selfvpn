import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from bot.config import settings
from bot.database.models import User

logger = logging.getLogger(__name__)

FREEKASSA_API_URL = "https://api.fk.life/v1/"
FREEKASSA_METHOD_SBP = 44
FREEKASSA_METHOD_CARD = 36
FREEKASSA_METHOD_MIR = 12
FREEKASSA_METHOD_USDT_TRC20 = 15
FREEKASSA_METHOD_TON = 45
FREEKASSA_MIN_USDT = 2.5
FREEKASSA_PAY_METHODS = frozenset({
    FREEKASSA_METHOD_SBP,
    FREEKASSA_METHOD_CARD,
    FREEKASSA_METHOD_MIR,
    FREEKASSA_METHOD_USDT_TRC20,
    FREEKASSA_METHOD_TON,
})
FREEKASSA_CRYPTO_METHODS = frozenset({
    FREEKASSA_METHOD_USDT_TRC20,
    FREEKASSA_METHOD_TON,
})
FREEKASSA_PAY_METHOD_LABELS: dict[int, str] = {
    FREEKASSA_METHOD_SBP: "СБП (НСПК)",
    FREEKASSA_METHOD_CARD: "Банковская карта (РФ)",
    FREEKASSA_METHOD_MIR: "Банковская карта МИР",
    FREEKASSA_METHOD_USDT_TRC20: "USDT TRC-20 (без комиссии)",
    FREEKASSA_METHOD_TON: "TON (без комиссии)",
}


def min_amount_rub_for_pay_method(
    pay_method: int,
    base_min_topup: float,
    *,
    usdt_rub_rate: float,
) -> float:
    """Минимальная сумма пополнения в ₽ для выбранного способа оплаты."""
    if pay_method == FREEKASSA_METHOD_USDT_TRC20:
        return max(base_min_topup, FREEKASSA_MIN_USDT * usdt_rub_rate)
    return base_min_topup

FREEKASSA_IPS = frozenset(
    {
        "168.119.157.136",
        "168.119.60.227",
        "178.154.197.79",
        "51.250.54.238",
    }
)


class FreekassaApiError(Exception):
    def __init__(self, message: str, *, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.response = response


def _md5(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()


def format_amount(amount: float) -> str:
    return f"{amount:.2f}"


def _api_signature_payload(data: dict[str, Any]) -> str:
    sorted_values = [str(data[key]) for key in sorted(data.keys())]
    return "|".join(sorted_values)


def _sign_api_request(data: dict[str, Any]) -> str:
    sign_payload = _api_signature_payload(data)
    return hmac.new(
        settings.freekassa_api_key.encode(),
        sign_payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def notification_signature(merchant_id: str, amount: str, order_id: str) -> str:
    raw = ":".join([merchant_id, amount, settings.freekassa_secret_2, order_id])
    return _md5(raw)


def verify_notification_signature(
    merchant_id: str,
    amount: str,
    order_id: str,
    signature: str,
) -> bool:
    expected = notification_signature(merchant_id, amount, order_id)
    return expected.lower() == signature.lower()


def is_freekassa_ip(client_ip: str) -> bool:
    return client_ip in FREEKASSA_IPS


def get_client_ip(request) -> str:
    forwarded = request.headers.get("x-real-ip")
    if forwarded:
        return forwarded.strip().split(",")[0].strip()

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.strip().split(",")[0].strip()

    if request.client:
        return request.client.host
    return ""


def resolve_payment_client_ip(request) -> str:
    ip = get_client_ip(request)
    if ip and ip not in {"127.0.0.1", "::1", "0.0.0.0"}:
        return ip

    if settings.freekassa_client_ip_fallback:
        return settings.freekassa_client_ip_fallback

    logger.warning("Freekassa payment IP fallback used: local or missing client IP (%s)", ip)
    return "72.56.124.163"


def payment_email_for_user(user: User) -> str:
    if user.email:
        return user.email
    if user.telegram_id:
        return f"{user.telegram_id}@telegram.org"
    return f"user{user.id}@telegram.org"


def _payment_location_from_response(body: dict[str, Any]) -> str:
    location = str(body.get("location") or body.get("Location") or "").strip()
    if location:
        return location

    order_id = body.get("orderId")
    order_hash = body.get("orderHash")
    if order_id and order_hash:
        return f"https://pay.freekassa.net/form/{order_id}/{order_hash}"

    return ""


async def create_payment_order(
    amount: float,
    payment_id: str,
    email: str,
    client_ip: str,
    payment_method: int,
    *,
    currency: str = "RUB",
) -> str:
    if payment_method not in FREEKASSA_PAY_METHODS:
        raise FreekassaApiError(f"unsupported payment method: {payment_method}")

    data: dict[str, Any] = {
        "shopId": settings.freekassa_merchant_id,
        "nonce": int(time.time() * 1000),
        "paymentId": payment_id,
        "i": payment_method,
        "email": email,
        "ip": client_ip,
        "amount": format_amount(amount),
        "currency": currency,
        "success_url": settings.payment_success_url(),
        "failure_url": settings.payment_fail_url(),
        "notification_url": settings.payment_notify_url(),
    }

    signature = _sign_api_request(data)
    request_body = {**data, "signature": signature}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{FREEKASSA_API_URL}orders/create",
                json=request_body,
            )
    except httpx.HTTPError as exc:
        logger.exception("Freekassa API request failed")
        raise FreekassaApiError("Freekassa API request failed") from exc

    try:
        body = response.json()
    except ValueError as exc:
        logger.error("Freekassa API invalid JSON: %s", response.text[:500])
        raise FreekassaApiError("Freekassa API returned invalid JSON") from exc

    if response.status_code >= 400 or body.get("type") != "success":
        message = body.get("message") or body.get("error") or f"HTTP {response.status_code}"
        logger.error("Freekassa create order failed: %s %s", message, body)
        raise FreekassaApiError(str(message), response=body)

    location = _payment_location_from_response(body)
    if not location:
        logger.error("Freekassa create order missing payment URL: %s", body)
        raise FreekassaApiError("Freekassa did not return payment URL", response=body)

    return location
