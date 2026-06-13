import hashlib
import logging

from bot.config import settings

logger = logging.getLogger(__name__)

FREEKASSA_PAY_URL = "https://pay.fk.money/"

FREEKASSA_IPS = frozenset(
    {
        "168.119.157.136",
        "168.119.60.227",
        "178.154.197.79",
        "51.250.54.238",
    }
)


def _md5(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()


def format_amount(amount: float) -> str:
    return f"{amount:.2f}"


def payment_form_signature(amount: float, order_id: str, currency: str = "RUB") -> str:
    raw = ":".join(
        [
            str(settings.freekassa_merchant_id),
            format_amount(amount),
            settings.freekassa_secret_1,
            currency,
            order_id,
        ]
    )
    return _md5(raw)


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
        return forwarded.strip()
    if request.client:
        return request.client.host
    return ""


def payment_form_fields(
    amount: float,
    order_id: str,
    *,
    cabinet_token: str,
    currency: str = "RUB",
) -> dict[str, str]:
    return {
        "m": str(settings.freekassa_merchant_id),
        "oa": format_amount(amount),
        "currency": currency,
        "o": order_id,
        "s": payment_form_signature(amount, order_id, currency),
        "lang": "ru",
        "us_token": cabinet_token,
    }
