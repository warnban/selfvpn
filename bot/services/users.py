from datetime import datetime
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, Referral, User
from bot.services.panel import panel_client
from bot.services.vpn_config import prepare_panel_vpn, public_vpn_link

logger = logging.getLogger(__name__)


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_cabinet_token(session: AsyncSession, token: str) -> User | None:
    result = await session.execute(select(User).where(User.cabinet_token == token))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def list_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def register_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    referrer_telegram_id: int | None,
) -> tuple[User, bool]:
    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        if not existing.cabinet_token:
            existing.cabinet_token = secrets.token_urlsafe(24)
            await session.commit()
            await session.refresh(existing)
        return existing, False

    referrer: User | None = None
    if referrer_telegram_id and referrer_telegram_id != telegram_id:
        referrer = await get_user_by_telegram_id(session, referrer_telegram_id)

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        auth_provider="telegram",
        balance_rub=settings.trial_balance_rub,
        referrer_id=referrer.id if referrer else None,
        last_billed_at=datetime.utcnow(),
        cabinet_token=secrets.token_urlsafe(24),
    )
    session.add(user)
    await session.flush()

    if referrer:
        referral = Referral(
            referrer_id=referrer.id,
            referred_id=user.id,
            bonus_rub=settings.referral_bonus_rub,
        )
        session.add(referral)
        referrer.balance_rub += settings.referral_bonus_rub

    await session.commit()
    await session.refresh(user)
    return user, True


async def admin_credit_balance(
    session: AsyncSession,
    user: User,
    amount: float,
    comment: str | None = None,
) -> User:
    user.balance_rub += amount
    await session.commit()
    await session.refresh(user)
    return user


async def cancel_pending_freekassa_for_user(
    session: AsyncSession,
    user: User,
    *,
    comment: str = "Отменено — новая попытка оплаты",
) -> None:
    result = await session.execute(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.status == PaymentStatus.PENDING.value,
            Payment.source == "freekassa",
        )
    )
    payments = list(result.scalars().all())
    if not payments:
        return
    for payment in payments:
        payment.status = PaymentStatus.REJECTED.value
        payment.processed_at = datetime.utcnow()
        payment.admin_comment = comment
    await session.commit()


async def cancel_pending_stars_for_user(
    session: AsyncSession,
    user: User,
    *,
    comment: str = "Отменено — новый счёт Stars",
) -> None:
    result = await session.execute(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.status == PaymentStatus.PENDING.value,
            Payment.source == "stars",
        )
    )
    payments = list(result.scalars().all())
    if not payments:
        return
    for payment in payments:
        payment.status = PaymentStatus.REJECTED.value
        payment.processed_at = datetime.utcnow()
        payment.admin_comment = comment
    await session.commit()


async def create_payment_request(
    session: AsyncSession,
    user: User,
    amount: float,
    days: int,
    *,
    source: str = "telegram",
    stars_amount: int | None = None,
    screenshot_file_id: str | None = None,
    screenshot_path: str | None = None,
) -> Payment:
    payment = Payment(
        user_id=user.id,
        amount_rub=amount,
        days_purchased=days,
        stars_amount=stars_amount,
        source=source,
        screenshot_file_id=screenshot_file_id,
        screenshot_path=screenshot_path,
        status=PaymentStatus.PENDING.value,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def finalize_stars_payment(
    session: AsyncSession,
    payment: Payment,
    *,
    charge_id: str,
    stars_paid: int,
) -> User:
    user = await session.get(User, payment.user_id)
    if payment.status == PaymentStatus.APPROVED.value:
        if user:
            await session.refresh(user)
        return user

    payment.stars_amount = stars_paid
    payment.telegram_charge_id = charge_id
    return await approve_payment(session, payment)


async def approve_payment(session: AsyncSession, payment: Payment) -> User:
    payment.status = PaymentStatus.APPROVED.value
    payment.processed_at = datetime.utcnow()
    user = await session.get(User, payment.user_id)
    if user:
        user.balance_rub += payment.amount_rub
    await session.commit()
    if user:
        await session.refresh(user)
    return user


async def reject_payment(session: AsyncSession, payment: Payment, comment: str | None = None) -> None:
    payment.status = PaymentStatus.REJECTED.value
    payment.processed_at = datetime.utcnow()
    payment.admin_comment = comment
    await session.commit()


async def provision_vpn(session: AsyncSession, user: User) -> str:
    if user.vpn_client_id and user.vpn_active and user.vpn_link:
        return public_vpn_link(user.vpn_link)

    if user.balance_rub < settings.daily_price_rub:
        raise ValueError("Недостаточно средств на балансе")

    name = f"tg_{user.telegram_id}"
    try:
        result = await panel_client.create_client(name)
    except Exception:
        logger.exception("Panel create_client failed for %s", name)
        raise

    user.vpn_client_id = result.get("client_id") or result.get("clientId")
    user.vpn_active = True

    vpn_link, _ = prepare_panel_vpn(result)
    if not vpn_link:
        logger.error("Panel response without vpn link: %s", list(result.keys()))
        raise ValueError(f"Сервер не вернул ключ подключения. Ответ: {str(result)[:200]}")

    user.vpn_link = vpn_link
    await session.commit()
    return vpn_link


async def deactivate_vpn(session: AsyncSession, user: User) -> None:
    if not user.vpn_client_id:
        user.vpn_active = False
        user.vpn_link = None
        await session.commit()
        return
    try:
        await panel_client.remove_client(user.vpn_client_id)
    except Exception:
        pass
    user.vpn_client_id = None
    user.vpn_active = False
    user.vpn_link = None
    await session.commit()


async def count_referrals(session: AsyncSession, user: User) -> int:
    result = await session.execute(select(Referral).where(Referral.referrer_id == user.id))
    return len(result.scalars().all())


def days_left(user: User) -> int:
    if settings.daily_price_rub <= 0:
        return 0
    return int(user.balance_rub // settings.daily_price_rub)
