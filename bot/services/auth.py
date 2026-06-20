import re
import secrets
from dataclasses import dataclass

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Device, Payment, Referral, User
from bot.services.email import send_password_reset_email, send_verification_email

_token_serializer = URLSafeTimedSerializer(settings.web_secret_key)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> str | None:
    normalized = normalize_email(email)
    if not EMAIL_RE.match(normalized):
        return None
    return normalized


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LEN:
        return f"Пароль должен быть не короче {MIN_PASSWORD_LEN} символов"
    return None


def make_action_token(user_id: int, action: str) -> str:
    return _token_serializer.dumps({"uid": user_id, "action": action})


def load_action_token(token: str, action: str, max_age: int) -> int | None:
    try:
        data = _token_serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    if data.get("action") != action:
        return None
    uid = data.get("uid")
    return int(uid) if uid is not None else None


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    normalized = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized))
    return result.scalar_one_or_none()


def user_display_name(user: User) -> str:
    return (
        user.display_name
        or user.first_name
        or (user.email.split("@")[0] if user.email else None)
        or "пользователь"
    )


def admin_user_subtitle(user: User) -> str:
    """Secondary line in admin lists: @username, email, or internal id."""
    if user.username:
        if user.email:
            return f"@{user.username} · {user.email}"
        return f"@{user.username}"
    if user.email:
        verified = " ✓" if user.email_verified else ""
        return f"{user.email}{verified}"
    if user.telegram_id:
        return f"TG {user.telegram_id}"
    return f"ID {user.id}"


def requires_email_verification_for_device(user: User) -> bool:
    """Web-registered users must verify email before VPN keys can be created."""
    if user.email_verified:
        return False
    if user.telegram_id and user.auth_provider == "telegram":
        return False
    return True


async def register_web_user(
    session: AsyncSession,
    email: str,
    password: str,
    display_name: str | None = None,
    referrer_user_id: int | None = None,
) -> tuple[User | None, str | None]:
    from datetime import datetime

    normalized = validate_email(email)
    if not normalized:
        return None, "Некорректный email"

    pwd_err = validate_password(password)
    if pwd_err:
        return None, pwd_err

    existing = await get_user_by_email(session, normalized)
    if existing:
        return None, "Этот email уже зарегистрирован"

    referrer: User | None = None
    if referrer_user_id:
        referrer = await session.get(User, referrer_user_id)
        if referrer and referrer.id == referrer_user_id:
            pass
        else:
            referrer = None

    user = User(
        telegram_id=None,
        email=normalized,
        password_hash=hash_password(password),
        display_name=(display_name or "").strip()[:255] or None,
        email_verified=False,
        auth_provider="email",
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
    return user, None


async def authenticate_web_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> tuple[User | None, str | None]:
    normalized = validate_email(email)
    if not normalized:
        return None, "Некорректный email"

    user = await get_user_by_email(session, normalized)
    if not user or not user.password_hash:
        return None, "Неверный email или пароль"

    if not verify_password(password, user.password_hash):
        return None, "Неверный email или пароль"

    return user, None


async def send_user_verification_email(user: User) -> bool:
    if not user.email:
        return False
    token = make_action_token(user.id, "verify")
    url = f"{settings.web_base_url.rstrip('/')}/auth/verify/{token}"
    return await send_verification_email(user.email, url)


async def verify_user_email(session: AsyncSession, token: str) -> tuple[User | None, str | None]:
    user_id = load_action_token(token, "verify", max_age=60 * 60 * 24 * 3)
    if not user_id:
        return None, "Ссылка недействительна или устарела"

    user = await session.get(User, user_id)
    if not user:
        return None, "Пользователь не найден"

    user.email_verified = True
    if user.auth_provider == "email":
        pass
    elif user.email and not user.auth_provider.endswith("email"):
        user.auth_provider = "both"
    await session.commit()
    await session.refresh(user)
    return user, None


async def request_password_reset(session: AsyncSession, email: str) -> bool:
    normalized = validate_email(email)
    if not normalized:
        return False

    user = await get_user_by_email(session, normalized)
    if not user or not user.password_hash:
        return True

    token = make_action_token(user.id, "reset")
    url = f"{settings.web_base_url.rstrip('/')}/auth/reset/{token}"
    await send_password_reset_email(user.email, url)
    return True


async def reset_password(
    session: AsyncSession,
    token: str,
    new_password: str,
) -> tuple[User | None, str | None]:
    pwd_err = validate_password(new_password)
    if pwd_err:
        return None, pwd_err

    user_id = load_action_token(token, "reset", max_age=3600)
    if not user_id:
        return None, "Ссылка недействительна или устарела"

    user = await session.get(User, user_id)
    if not user:
        return None, "Пользователь не найден"

    user.password_hash = hash_password(new_password)
    await session.commit()
    await session.refresh(user)
    return user, None


async def change_password(
    session: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> str | None:
    if not user.password_hash:
        return "У аккаунта нет пароля"

    if not verify_password(current_password, user.password_hash):
        return "Неверный текущий пароль"

    pwd_err = validate_password(new_password)
    if pwd_err:
        return pwd_err

    user.password_hash = hash_password(new_password)
    await session.commit()
    return None


@dataclass
class LinkResult:
    """Итог привязки Telegram. error != None — привязка не выполнена."""

    error: str | None = None
    merged: bool = False
    moved_balance: float = 0.0
    moved_devices: int = 0


async def _merge_accounts(session: AsyncSession, primary: User, dup: User) -> LinkResult:
    """Сливает дубликат-аккаунт ``dup`` в основной ``primary`` и удаляет дубль.

    ``primary`` — это email/web-аккаунт, на котором пользователь копил баланс,
    поэтому он остаётся основным. Всё ценное из Telegram-аккаунта переносим к нему,
    баланс суммируем (чтобы не потерять реальные пополнения).
    """
    moved_balance = dup.balance_rub or 0.0
    primary.balance_rub = (primary.balance_rub or 0.0) + moved_balance

    # Устройства (VPN-ключи) и платежи переносим на основной аккаунт.
    device_res = await session.execute(
        update(Device).where(Device.user_id == dup.id).values(user_id=primary.id)
    )
    moved_devices = device_res.rowcount or 0
    await session.execute(
        update(Payment).where(Payment.user_id == dup.id).values(user_id=primary.id)
    )

    # Убираем взаимные реферальные связи между сливаемыми аккаунтами,
    # иначе после переноса получим запись "сам себя пригласил".
    await session.execute(
        delete(Referral).where(
            ((Referral.referrer_id == dup.id) & (Referral.referred_id == primary.id))
            | ((Referral.referrer_id == primary.id) & (Referral.referred_id == dup.id))
        )
    )

    # Кого пригласил дубль — теперь приглашения числятся за основным аккаунтом.
    await session.execute(
        update(Referral).where(Referral.referrer_id == dup.id).values(referrer_id=primary.id)
    )
    # Кто пригласил дубль (referred_id уникален): переносим только если у основного
    # такой записи ещё нет, иначе просто удаляем «лишнюю».
    primary_referred = await session.execute(
        select(Referral.id).where(Referral.referred_id == primary.id)
    )
    if primary_referred.scalar_one_or_none() is not None:
        await session.execute(delete(Referral).where(Referral.referred_id == dup.id))
    else:
        await session.execute(
            update(Referral).where(Referral.referred_id == dup.id).values(referred_id=primary.id)
        )

    # Пользователи, у которых дубль был реферером, теперь ссылаются на основной аккаунт.
    await session.execute(
        update(User)
        .where(User.referrer_id == dup.id, User.id != primary.id)
        .values(referrer_id=primary.id)
    )
    if primary.referrer_id == dup.id:
        primary.referrer_id = None
    elif not primary.referrer_id and dup.referrer_id and dup.referrer_id not in (primary.id, dup.id):
        primary.referrer_id = dup.referrer_id

    # Разовые бонусы и онбординг — считаем выполненными, если хотя бы где-то были.
    primary.channel_bonus_paid = primary.channel_bonus_paid or dup.channel_bonus_paid
    primary.referral_bonus_paid = primary.referral_bonus_paid or dup.referral_bonus_paid
    primary.onboarding_completed = primary.onboarding_completed or dup.onboarding_completed

    # Берём более свежую дату списания, чтобы не словить разовое «дописывание» за прошлое.
    if dup.last_billed_at and (
        not primary.last_billed_at or dup.last_billed_at > primary.last_billed_at
    ):
        primary.last_billed_at = dup.last_billed_at

    if not primary.display_name and dup.display_name:
        primary.display_name = dup.display_name
    if not primary.vpn_client_id and dup.vpn_client_id:
        primary.vpn_client_id = dup.vpn_client_id
        primary.vpn_link = dup.vpn_link
        primary.vpn_active = dup.vpn_active

    # Удаляем дубль ДО присвоения telegram_id основному — освобождаем unique-индекс.
    await session.execute(delete(User).where(User.id == dup.id))
    session.expunge(dup)

    return LinkResult(merged=True, moved_balance=moved_balance, moved_devices=moved_devices)


async def link_telegram_to_user(
    session: AsyncSession,
    user: User,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> LinkResult:
    if user.telegram_id:
        return LinkResult(error="Telegram уже привязан")

    existing = await session.execute(select(User).where(User.telegram_id == telegram_id))
    other = existing.scalar_one_or_none()

    result = LinkResult()
    if other and other.id != user.id:
        # У пользователя уже есть отдельный Telegram-аккаунт в боте — сливаем его сюда.
        result = await _merge_accounts(session, primary=user, dup=other)

    user.telegram_id = telegram_id
    if username:
        user.username = username
    if first_name and not user.first_name:
        user.first_name = first_name
    if user.auth_provider == "email":
        user.auth_provider = "both"
    await session.commit()
    await session.refresh(user)
    return result


def make_telegram_link_token(user_id: int) -> str:
    return make_action_token(user_id, "link_tg")


def load_telegram_link_user_id(token: str) -> int | None:
    return load_action_token(token, "link_tg", max_age=60 * 60 * 24)
