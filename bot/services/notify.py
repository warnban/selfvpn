import logging
import re

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.models import User
from bot.services.email import send_notification_email

logger = logging.getLogger(__name__)


async def send_user_message(telegram_id: int, text: str) -> bool:
    if not settings.bot_token:
        return False
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await bot.send_message(telegram_id, text)
        return True
    except Exception as exc:
        logger.warning("Не удалось отправить сообщение %s: %s", telegram_id, exc)
        return False
    finally:
        await bot.session.close()


def _html_to_plain(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


async def notify_user(
    user: User,
    text: str,
    *,
    subject: str = "Уведомление",
) -> bool:
    if user.telegram_id:
        return await send_user_message(user.telegram_id, text)
    if user.email and user.email_verified:
        return await send_notification_email(user.email, subject, _html_to_plain(text))
    return False


async def notify_balance_credited(
    telegram_id: int | None,
    amount: float,
    balance: float,
    comment: str | None = None,
    *,
    user: User | None = None,
) -> None:
    text = (
        f"✅ На ваш баланс начислено <b>{amount:.0f} ₽</b>\n"
        f"💰 Текущий баланс: <b>{balance:.0f} ₽</b>"
    )
    if comment:
        text += f"\n\n📝 {comment}"
    if user:
        await notify_user(user, text, subject="Начисление на баланс")
    elif telegram_id:
        await send_user_message(telegram_id, text)


async def notify_payment_approved(
    telegram_id: int | None,
    amount: float,
    days: int,
    balance: float,
    *,
    credited: float | None = None,
    user: User | None = None,
) -> None:
    lines = [
        "✅ Оплата подтверждена!",
        f"📦 Пакет: {days} дн.",
        f"💳 Оплачено: {amount:.0f} ₽",
    ]
    if credited is not None and credited > amount + 0.01:
        bonus = credited - amount
        lines.append(f"🎁 Бонус акции: +{bonus:.0f} ₽")
        lines.append(f"➕ Зачислено: {credited:.0f} ₽")
    lines.append(f"💰 Баланс: {balance:.0f} ₽")
    text = "\n".join(lines)
    if user:
        await notify_user(user, text, subject="Оплата подтверждена")
    elif telegram_id:
        await send_user_message(telegram_id, text)


async def notify_payment_rejected(telegram_id: int | None, *, user: User | None = None) -> None:
    text = "❌ Платёж не подтверждён. Если это ошибка — напишите администратору."
    if user:
        await notify_user(user, text, subject="Платёж отклонён")
    elif telegram_id:
        await send_user_message(telegram_id, text)
