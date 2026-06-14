from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import AppSetting

STARS_PER_DAY_KEY = "stars_per_day"


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
    row = await session.get(AppSetting, STARS_PER_DAY_KEY)
    if not row:
        session.add(AppSetting(key=STARS_PER_DAY_KEY, value=str(settings.stars_per_day)))
        await session.commit()
