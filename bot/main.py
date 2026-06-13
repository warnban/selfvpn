import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings
from bot.database.session import init_db
from bot.handlers import devices, payment, user
from bot.middlewares.db import DbSessionMiddleware
from bot.services.billing import process_daily_billing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    try:
        await init_db()
        logger.info("База данных готова")

        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=MemoryStorage())
        dp.update.middleware(DbSessionMiddleware())

        dp.include_router(user.router)
        dp.include_router(devices.router)
        dp.include_router(payment.router)

        me = await bot.get_me()
        logger.info("Telegram bot: @%s (id=%s)", me.username, me.id)

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook сброшен, запуск polling")

        scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
        scheduler.add_job(
            process_daily_billing,
            CronTrigger(hour=settings.billing_hour, minute=0),
            id="daily_billing",
        )
        scheduler.start()
        logger.info("Биллинг запланирован на %s:00 MSK", settings.billing_hour)

        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Бот упал при запуске")
        raise


if __name__ == "__main__":
    asyncio.run(main())
