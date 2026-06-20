import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org"

# Статусы, означающие, что пользователь состоит в канале.
SUBSCRIBED_STATUSES = frozenset({"creator", "administrator", "member", "restricted"})

# Результаты grant_channel_bonus
GRANT_GRANTED = "granted"
GRANT_ALREADY = "already"
GRANT_NOT_SUBSCRIBED = "not_subscribed"
GRANT_NO_TELEGRAM = "no_telegram"
GRANT_DISABLED = "disabled"
GRANT_ERROR = "error"


async def is_channel_member(telegram_id: int) -> bool | None:
    """True/False — подписан/нет. None — не удалось проверить (ошибка API)."""
    if not settings.channel_bonus_enabled:
        return None

    url = f"{TELEGRAM_API_URL}/bot{settings.bot_token}/getChatMember"
    params = {
        "chat_id": f"@{settings.channel_username_clean}",
        "user_id": telegram_id,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
        body = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("Telegram getChatMember request failed")
        return None

    if not body.get("ok"):
        # user not found in chat → not a member; иначе настоящая ошибка
        description = str(body.get("description", "")).lower()
        if "not found" in description or "user not found" in description:
            return False
        logger.warning("getChatMember not ok: %s", body)
        return None

    result = body.get("result") or {}
    status = result.get("status")
    if status == "restricted":
        return bool(result.get("is_member"))
    return status in SUBSCRIBED_STATUSES


async def grant_channel_bonus(session: AsyncSession, user: User) -> str:
    """Проверяет подписку и единоразово начисляет бонус. Возвращает код результата."""
    if not settings.channel_bonus_enabled:
        return GRANT_DISABLED

    if user.channel_bonus_paid:
        return GRANT_ALREADY

    if not user.telegram_id:
        return GRANT_NO_TELEGRAM

    member = await is_channel_member(user.telegram_id)
    if member is None:
        return GRANT_ERROR
    if not member:
        return GRANT_NOT_SUBSCRIBED

    user.channel_bonus_paid = True
    user.balance_rub += settings.channel_bonus_rub
    await session.commit()
    await session.refresh(user)
    return GRANT_GRANTED
