from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import secrets
from datetime import datetime

from sqlalchemy import select, text

from bot.config import settings
from bot.database.models import AppSetting, Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"timeout": 15},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_sqlite(conn)
    async with async_session() as session:
        from bot.services.app_settings import ensure_app_settings_defaults

        await ensure_app_settings_defaults(session)


async def _migrate_sqlite(conn) -> None:
    """Добавляет новые колонки в существующую SQLite-базу без Alembic."""
    if "sqlite" not in settings.database_url:
        return

    def _rebuild_users_telegram_nullable(sync_conn, inspector) -> None:
        if "users" not in inspector.get_table_names():
            return
        info = sync_conn.execute(text("PRAGMA table_info(users)")).fetchall()
        tg = next((row for row in info if row[1] == "telegram_id"), None)
        if not tg or tg[3] == 0:
            return

        existing = {row[1] for row in info}
        columns = [
            "id",
            "telegram_id",
            "username",
            "first_name",
            "display_name",
            "email",
            "password_hash",
            "email_verified",
            "auth_provider",
            "balance_rub",
            "referrer_id",
            "vpn_client_id",
            "vpn_link",
            "vpn_active",
            "cabinet_token",
            "referral_bonus_paid",
            "created_at",
            "last_billed_at",
        ]
        copy_cols = [c for c in columns if c in existing]
        if "id" not in copy_cols:
            return

        sync_conn.execute(text("PRAGMA foreign_keys=OFF"))
        sync_conn.execute(
            text(
                """
                CREATE TABLE users__new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    display_name VARCHAR(255),
                    email VARCHAR(255),
                    password_hash VARCHAR(255),
                    email_verified BOOLEAN DEFAULT 0,
                    auth_provider VARCHAR(16) DEFAULT 'telegram',
                    balance_rub FLOAT DEFAULT 0.0,
                    referrer_id INTEGER,
                    vpn_client_id VARCHAR(128),
                    vpn_link TEXT,
                    vpn_active BOOLEAN DEFAULT 0,
                    cabinet_token VARCHAR(64),
                    referral_bonus_paid BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    last_billed_at DATETIME
                )
                """
            )
        )
        col_list = ", ".join(copy_cols)
        sync_conn.execute(text(f"INSERT INTO users__new ({col_list}) SELECT {col_list} FROM users"))
        sync_conn.execute(text("DROP TABLE users"))
        sync_conn.execute(text("ALTER TABLE users__new RENAME TO users"))
        sync_conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_id ON users (telegram_id)"))
        sync_conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        sync_conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_cabinet_token ON users (cabinet_token)"))
        sync_conn.execute(text("PRAGMA foreign_keys=ON"))

    def run_migrations(sync_conn):
        from sqlalchemy import inspect, text

        inspector = inspect(sync_conn)
        if "users" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "cabinet_token" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN cabinet_token VARCHAR(64)"))
            if "vpn_link" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN vpn_link TEXT"))
            if "display_name" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(255)"))
            if "email" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
            if "password_hash" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            if "email_verified" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
            if "auth_provider" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(16) DEFAULT 'telegram'"))
            if "channel_bonus_paid" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN channel_bonus_paid BOOLEAN DEFAULT 0"))
            if "onboarding_completed" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0"))
                if "devices" in inspector.get_table_names():
                    sync_conn.execute(
                        text(
                            "UPDATE users SET onboarding_completed = 1 "
                            "WHERE id IN (SELECT DISTINCT user_id FROM devices)"
                        )
                    )
            if "partner_enabled" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN partner_enabled BOOLEAN DEFAULT 0"))
            if "partner_commission_pct" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN partner_commission_pct FLOAT DEFAULT 0"))
            if "partner_balance_rub" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN partner_balance_rub FLOAT DEFAULT 0"))
            if "partner_paid_out_total_rub" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN partner_paid_out_total_rub FLOAT DEFAULT 0"))
            _rebuild_users_telegram_nullable(sync_conn, inspector)
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
            if "stars_amount" not in cols:
                sync_conn.execute(text("ALTER TABLE payments ADD COLUMN stars_amount INTEGER"))
            if "telegram_charge_id" not in cols:
                sync_conn.execute(text("ALTER TABLE payments ADD COLUMN telegram_charge_id VARCHAR(255)"))

        # Перенос старого единичного VPN из users в таблицу devices
        if "devices" in inspector.get_table_names():
            dcols = {c["name"] for c in inspector.get_columns("devices")}
            if "vpn_config" not in dcols:
                sync_conn.execute(text("ALTER TABLE devices ADD COLUMN vpn_config TEXT"))
            if "panel_server_id" not in dcols:
                sync_conn.execute(text("ALTER TABLE devices ADD COLUMN panel_server_id INTEGER"))

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
