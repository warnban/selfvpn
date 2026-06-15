import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Device, User
from bot.database.session import async_session
from bot.services.notify import notify_user
from bot.services.panel import panel_client

logger = logging.getLogger(__name__)


async def _devices_of(session: AsyncSession, user: User) -> list[Device]:
    result = await session.execute(
        select(Device).where(Device.user_id == user.id).order_by(Device.created_at.desc())
    )
    return list(result.scalars().all())


async def process_daily_billing() -> None:
    """Списывает тариф × число устройств. При нехватке удаляет устройства (новые первыми)."""
    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()
        now = datetime.utcnow()
        price = settings.daily_price_rub

        for user in users:
            if user.last_billed_at and now - user.last_billed_at < timedelta(hours=23):
                continue

            devices = await _devices_of(session, user)
            user.last_billed_at = now

            if not devices:
                continue

            removed: list[str] = []
            # Удаляем новейшие устройства, пока баланс не покрывает стоимость суток
            while devices and user.balance_rub < price * len(devices):
                victim = devices.pop(0)  # новейшее (сортировка desc)
                if victim.vpn_client_id:
                    try:
                        await panel_client.remove_client(victim.vpn_client_id)
                    except Exception as exc:
                        logger.warning("Не удалось удалить peer %s: %s", victim.vpn_client_id, exc)
                removed.append(victim.name)
                await session.delete(victim)

            if devices:
                user.balance_rub -= price * len(devices)

            if removed:
                await session.commit()
                names = ", ".join(removed)
                from bot.services.notify import notify_user

                await notify_user(
                    user,
                    "⚠️ Недостаточно средств на балансе.\n"
                    f"Отключены устройства: <b>{names}</b>\n\n"
                    f"💰 Баланс: {user.balance_rub:.0f} ₽\n"
                    "Пополни баланс и добавь устройства заново.",
                    subject="Недостаточно средств",
                )

        await session.commit()
        logger.info("Ежедневное списание завершено для %s пользователей", len(users))
