from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.services.auth import (
    user_display_name,
    requires_email_verification_for_device,
    make_telegram_link_token,
)
from bot.services.devices import (
    count_devices,
    days_left_for,
    list_devices,
    user_daily_cost,
)
from bot.services.users import count_referrals, get_user_by_cabinet_token, get_user_by_id


def get_session_user_id(request: Request) -> int | None:
    uid = request.session.get("user_id")
    return int(uid) if uid else None


def login_session(request: Request, user: User) -> None:
    request.session["user_id"] = user.id


def logout_session(request: Request) -> None:
    request.session.pop("user_id", None)


async def get_user_from_session(
    request: Request,
    session: AsyncSession,
) -> User | None:
    user_id = get_session_user_id(request)
    if not user_id:
        return None
    return await get_user_by_id(session, user_id)


async def require_session_user(
    request: Request,
    db: AsyncSession,
) -> User | RedirectResponse:
    user = await get_user_from_session(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    return user


def cabinet_base_path(user: User, via_session: bool) -> str:
    if via_session:
        return "/cabinet"
    return f"/cabinet/{user.cabinet_token}"


def onboarding_base_path(user: User, via_session: bool) -> str:
    if via_session:
        return "/cabinet/onboarding"
    return f"/cabinet/{user.cabinet_token}/onboarding"


def needs_onboarding(user: User) -> bool:
    return not user.onboarding_completed


async def complete_onboarding(session: AsyncSession, user: User) -> bool:
    """Returns False if user has no devices."""
    from bot.services.devices import count_devices

    if await count_devices(session, user) < 1:
        return False
    user.onboarding_completed = True
    await session.commit()
    return True


async def build_cabinet_context(
    request: Request,
    user: User,
    db: AsyncSession,
    *,
    via_session: bool = False,
) -> dict:
    refs = await count_referrals(db, user)
    devices = await list_devices(db, user)
    cost = await user_daily_cost(db, user)
    left = await days_left_for(db, user)
    base = cabinet_base_path(user, via_session)

    ref_web = settings.register_url(ref=user.id)
    bot_username = getattr(settings, "bot_username", None) or "anfikvpnbot"
    ref_tg = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}" if user.telegram_id else None

    show_channel_bonus = settings.channel_bonus_enabled and not user.channel_bonus_paid
    channel_link_bot_url = None
    if show_channel_bonus and not user.telegram_id:
        token = make_telegram_link_token(user.id)
        channel_link_bot_url = f"https://t.me/{bot_username}?start=link_{token}"

    return {
        "user": user,
        "display_name": user_display_name(user),
        "days_left": left,
        "daily_price": settings.daily_price_rub,
        "daily_cost": cost,
        "devices": devices,
        "device_count": len(devices),
        "referrals": refs,
        "referral_bonus": settings.referral_bonus_rub,
        "referral_web_link": ref_web,
        "referral_tg_link": ref_tg,
        "payment_card": settings.payment_card,
        "payment_bank": settings.payment_bank,
        "payment_holder": settings.payment_holder,
        "cabinet_base": base,
        "onboarding_base": onboarding_base_path(user, via_session),
        "via_session": via_session,
        "has_password": bool(user.password_hash),
        "has_telegram": bool(user.telegram_id),
        "requires_email_verification": requires_email_verification_for_device(user),
        "login_url": settings.login_url(),
        "register_url": settings.register_url(),
        "show_channel_bonus": show_channel_bonus,
        "channel_url": settings.channel_url,
        "channel_bonus_rub": settings.channel_bonus_rub,
        "channel_link_bot_url": channel_link_bot_url,
    }
