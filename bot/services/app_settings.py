from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import AppSetting

STARS_PER_DAY_KEY = "stars_per_day"
DEPOSIT_MULTIPLIER_KEY = "deposit_multiplier"
MIN_TOPUP_KEY = "min_topup_rub"

# Допустимые множители акции: 1 = акция выключена (начисляем ровно сумму пополнения).
ALLOWED_DEPOSIT_MULTIPLIERS = (1.0, 2.0, 3.0)


async def get_deposit_multiplier(session: AsyncSession) -> float:
    """Множитель пополнения. 1.0 — акция выключена."""
    row = await session.get(AppSetting, DEPOSIT_MULTIPLIER_KEY)
    if row:
        try:
            value = float(row.value)
        except (TypeError, ValueError):
            return 1.0
        if value in ALLOWED_DEPOSIT_MULTIPLIERS:
            return value
        return max(1.0, min(value, 3.0))
    return 1.0


async def set_deposit_multiplier(session: AsyncSession, value: float) -> float:
    if value not in ALLOWED_DEPOSIT_MULTIPLIERS:
        value = max(1.0, min(float(value), 3.0))
    row = await session.get(AppSetting, DEPOSIT_MULTIPLIER_KEY)
    if row:
        row.value = str(value)
    else:
        session.add(AppSetting(key=DEPOSIT_MULTIPLIER_KEY, value=str(value)))
    await session.commit()
    return value


async def get_min_topup(session: AsyncSession) -> float:
    """Минимальная сумма пополнения в рублях."""
    row = await session.get(AppSetting, MIN_TOPUP_KEY)
    if row:
        try:
            return max(0.0, float(row.value))
        except (TypeError, ValueError):
            pass
    return float(settings.min_topup_rub)


async def set_min_topup(session: AsyncSession, value: float) -> float:
    value = max(0.0, min(float(value), 1_000_000.0))
    row = await session.get(AppSetting, MIN_TOPUP_KEY)
    if row:
        row.value = str(value)
    else:
        session.add(AppSetting(key=MIN_TOPUP_KEY, value=str(value)))
    await session.commit()
    return value


async def get_stars_per_day(session: AsyncSession) -> int:
    row = await session.get(AppSetting, STARS_PER_DAY_KEY)
    if row:
        try:
            return max(1, int(row.value))
        except ValueError:
            pass
    return settings.stars_per_day


async def set_stars_per_day(session: AsyncSession, value: int) -> int:
    value = max(1, min(value, 10_000))
    row = await session.get(AppSetting, STARS_PER_DAY_KEY)
    if row:
        row.value = str(value)
    else:
        session.add(AppSetting(key=STARS_PER_DAY_KEY, value=str(value)))
    await session.commit()
    return value


async def stars_for_days(session: AsyncSession, days: int) -> int:
    return (await get_stars_per_day(session)) * days


async def ensure_app_settings_defaults(session: AsyncSession) -> None:
    changed = False
    if not await session.get(AppSetting, STARS_PER_DAY_KEY):
        session.add(AppSetting(key=STARS_PER_DAY_KEY, value=str(settings.stars_per_day)))
        changed = True
    if not await session.get(AppSetting, DEPOSIT_MULTIPLIER_KEY):
        session.add(AppSetting(key=DEPOSIT_MULTIPLIER_KEY, value="1.0"))
        changed = True
    if not await session.get(AppSetting, MIN_TOPUP_KEY):
        session.add(AppSetting(key=MIN_TOPUP_KEY, value=str(float(settings.min_topup_rub))))
        changed = True
    if changed:
        await session.commit()
