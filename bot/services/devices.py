import base64
import logging
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Device, User
from bot.services.panel import panel_client

logger = logging.getLogger(__name__)

PLATFORM_LABELS = {
    "android": "📱 Android",
    "ios": "🍎 iPhone / iPad",
    "windows": "🖥 Windows",
    "mac": "💻 macOS",
    "other": "🔌 Другое",
}


def platform_label(platform: str) -> str:
    return PLATFORM_LABELS.get(platform, PLATFORM_LABELS["other"])


async def list_devices(session: AsyncSession, user: User) -> list[Device]:
    result = await session.execute(
        select(Device).where(Device.user_id == user.id).order_by(Device.created_at)
    )
    return list(result.scalars().all())


async def count_devices(session: AsyncSession, user: User) -> int:
    return len(await list_devices(session, user))


def daily_cost(device_count: int) -> float:
    return round(settings.daily_price_rub * device_count, 2)


async def user_daily_cost(session: AsyncSession, user: User) -> float:
    return daily_cost(await count_devices(session, user))


async def days_left_for(session: AsyncSession, user: User) -> int:
    count = await count_devices(session, user)
    # Без устройств показываем прогноз из расчёта на 1 устройство,
    # чтобы пользователь видел, что баланс не «сгорел».
    effective = count if count > 0 else 1
    cost = settings.daily_price_rub * effective
    if cost <= 0:
        return 0
    return int(user.balance_rub // cost)


def _extract_vpn_link(result: dict) -> str:
    link = result.get("vpn_link") or result.get("vpnLink")
    if not link and result.get("config"):
        link = "vpn://" + base64.b64encode(result["config"].encode()).decode()
    return link or ""


async def add_device(
    session: AsyncSession,
    user: User,
    platform: str,
    name: str | None = None,
) -> Device:
    current = await list_devices(session, user)

    if len(current) >= settings.max_devices:
        raise ValueError(f"Достигнут лимит устройств ({settings.max_devices}).")

    # Нужен баланс минимум на 1 сутки при новом количестве устройств
    new_count = len(current) + 1
    required = daily_cost(new_count)
    if user.balance_rub < required:
        raise ValueError(
            f"Недостаточно средств. Для {new_count} устройств(а) нужно "
            f"минимум {required:.0f} ₽ на балансе (хватит на 1 сутки)."
        )

    label = name or platform_label(platform).split(" ", 1)[-1]
    panel_name = f"tg{user.telegram_id}_{secrets.token_hex(3)}"

    try:
        result = await panel_client.create_client(panel_name)
    except Exception:
        logger.exception("Panel create_client failed for %s", panel_name)
        raise

    vpn_link = _extract_vpn_link(result)
    if not vpn_link:
        raise ValueError(f"Панель не вернула vpn://. Ответ: {str(result)[:200]}")

    device = Device(
        user_id=user.id,
        name=label[:64],
        platform=platform,
        vpn_client_id=result.get("client_id") or result.get("clientId"),
        vpn_link=vpn_link,
    )
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device


async def remove_device(session: AsyncSession, user: User, device_id: int) -> bool:
    device = await session.get(Device, device_id)
    if not device or device.user_id != user.id:
        return False

    if device.vpn_client_id:
        try:
            await panel_client.remove_client(device.vpn_client_id)
        except Exception as exc:
            logger.warning("Не удалось удалить peer %s: %s", device.vpn_client_id, exc)

    await session.delete(device)
    await session.commit()
    return True


async def get_device(session: AsyncSession, user: User, device_id: int) -> Device | None:
    device = await session.get(Device, device_id)
    if not device or device.user_id != user.id:
        return None
    return device
