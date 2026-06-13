from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import secrets
from datetime import datetime

from sqlalchemy import select, text

from bot.config import settings
from bot.database.models import Base

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_sqlite(conn)


async def _migrate_sqlite(conn) -> None:
    """Добавляет новые колонки в существующую SQLite-базу без Alembic."""
    if "sqlite" not in settings.database_url:
        return

    def run_migrations(sync_conn):
        from sqlalchemy import inspect, text

        inspector = inspect(sync_conn)
        if "users" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "cabinet_token" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN cabinet_token VARCHAR(64)"))
            if "vpn_link" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN vpn_link TEXT"))
            rows = sync_conn.execute(text("SELECT id FROM users WHERE cabinet_token IS NULL OR cabinet_token = ''")).fetchall()
            for (user_id,) in rows:
                sync_conn.execute(
                    text("UPDATE users SET cabinet_token = :token WHERE id = :id"),
                    {"token": secrets.token_urlsafe(24), "id": user_id},
                )
        if "payments" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("payments")}
            if "days_purchased" not in cols:
                sync_conn.execute(text("ALTER TABLE payments ADD COLUMN days_purchased INTEGER"))
            if "source" not in cols:
                sync_conn.execute(text("ALTER TABLE payments ADD COLUMN source VARCHAR(16) DEFAULT 'telegram'"))
            if "screenshot_path" not in cols:
                sync_conn.execute(text("ALTER TABLE payments ADD COLUMN screenshot_path VARCHAR(512)"))

        # Перенос старого единичного VPN из users в таблицу devices
        if "devices" in inspector.get_table_names() and "users" in inspector.get_table_names():
            ucols = {c["name"] for c in inspector.get_columns("users")}
            if "vpn_client_id" in ucols:
                migrated = sync_conn.execute(
                    text("SELECT user_id FROM devices")
                ).fetchall()
                migrated_ids = {row[0] for row in migrated}
                legacy = sync_conn.execute(
                    text(
                        "SELECT id, vpn_client_id, vpn_link FROM users "
                        "WHERE vpn_client_id IS NOT NULL AND vpn_client_id != ''"
                    )
                ).fetchall()
                for user_id, client_id, link in legacy:
                    if user_id in migrated_ids:
                        continue
                    sync_conn.execute(
                        text(
                            "INSERT INTO devices (user_id, name, platform, vpn_client_id, vpn_link, created_at) "
                            "VALUES (:uid, :name, :platform, :cid, :link, :created)"
                        ),
                        {
                            "uid": user_id,
                            "name": "Моё устройство",
                            "platform": "other",
                            "cid": client_id,
                            "link": link,
                            "created": datetime.utcnow().isoformat(sep=" "),
                        },
                    )

    await conn.run_sync(run_migrations)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
