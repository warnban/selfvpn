from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.session import async_session

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
