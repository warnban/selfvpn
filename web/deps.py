from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.session import async_session
from bot.services.vpn_config import public_vpn_link

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["branded_vpn_link"] = public_vpn_link


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
