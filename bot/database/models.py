from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_provider: Mapped[str] = mapped_column(String(16), default="telegram")

    balance_rub: Mapped[float] = mapped_column(Float, default=0.0)
    referrer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    vpn_client_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vpn_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    vpn_active: Mapped[bool] = mapped_column(Boolean, default=False)
    cabinet_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    referral_bonus_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    channel_bonus_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_billed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    referrer: Mapped["User | None"] = relationship("User", remote_side=[id], foreign_keys=[referrer_id])
    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    referrals: Mapped[list["Referral"]] = relationship(
        back_populates="referrer", foreign_keys="Referral.referrer_id"
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(64), default="Устройство")
    platform: Mapped[str] = mapped_column(String(16), default="other")
    vpn_client_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vpn_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    vpn_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    panel_server_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="devices")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_rub: Mapped[float] = mapped_column(Float)
    days_purchased: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stars_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    telegram_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="telegram")
    status: Mapped[str] = mapped_column(String(32), default=PaymentStatus.PENDING.value)
    screenshot_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="payments")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bonus_rub: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    referrer: Mapped["User"] = relationship(back_populates="referrals", foreign_keys=[referrer_id])
