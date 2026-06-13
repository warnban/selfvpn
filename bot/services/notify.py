import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings

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


async def notify_balance_credited(telegram_id: int, amount: float, balance: float, comment: str | None = None) -> None:
    text = (
        f"✅ На ваш баланс начислено <b>{amount:.0f} ₽</b>\n"
        f"💰 Текущий баланс: <b>{balance:.0f} ₽</b>"
    )
    if comment:
        text += f"\n\n📝 {comment}"
    await send_user_message(telegram_id, text)


async def notify_payment_approved(telegram_id: int, amount: float, days: int, balance: float) -> None:
    await send_user_message(
        telegram_id,
        f"✅ Оплата подтверждена!\n"
        f"📦 Пакет: {days} дн.\n"
        f"💳 Сумма: {amount:.0f} ₽\n"
        f"💰 Баланс: {balance:.0f} ₽",
    )


async def notify_payment_rejected(telegram_id: int) -> None:
    await send_user_message(
        telegram_id,
        "❌ Платёж не подтверждён. Если это ошибка — напишите администратору.",
    )
