"""REST API for the DaddyVPN Android app."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Payment, User
from bot.services import cardlink as cardlink_service
from bot.services.app_settings import get_deposit_multiplier, get_min_topup
from bot.services.freekassa import (
    FREEKASSA_METHOD_CARD,
    FREEKASSA_METHOD_SBP,
    FREEKASSA_METHOD_USDT_TRC20,
    FREEKASSA_MIN_USDT,
    FREEKASSA_PAY_METHOD_LABELS,
    FREEKASSA_PAY_METHODS,
    FreekassaApiError,
    create_payment_order,
    min_amount_rub_for_pay_method,
    payment_email_for_user,
)
from bot.database.session import async_session
from bot.services.devices import (
    add_device,
    count_devices,
    days_left_for,
    get_device,
    get_device_config,
    list_devices,
    platform_label,
    public_vpn_link_for_device,
    remove_device,
    replace_device_vpn_config,
    user_daily_cost,
)
from bot.services.auth import (
    can_unlink_telegram,
    make_telegram_link_token,
    telegram_link_url,
    unlink_telegram_from_user,
    user_display_name,
)
from bot.services.users import (
    cancel_pending_cardlink_for_user,
    cancel_pending_freekassa_for_user,
    create_payment_request,
    get_user_by_cabinet_token,
    list_user_payments,
    reject_payment,
)
from bot.services.vpn_config import extract_vpn_link, public_vpn_link

router = APIRouter(prefix="/api/mobile/v1", tags=["mobile"])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Требуется Authorization: Bearer <cabinet_token>")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Пустой токен")
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    return user


class BootstrapResponse(BaseModel):
    brand_name: str
    daily_price_rub: float
    max_devices: int
    support_tg_url: str
    api_base_url: str


class UserResponse(BaseModel):
    first_name: str | None
    username: str | None
    balance_rub: float
    days_left: int
    daily_cost_rub: float
    device_count: int
    max_devices: int
    cabinet_token: str


class DeviceResponse(BaseModel):
    id: int
    name: str
    platform: str
    platform_label: str
    has_vpn: bool


class CreateDeviceRequest(BaseModel):
    platform: str = Field(default="android", max_length=16)
    name: str | None = Field(default=None, max_length=64)


class RegisterDeviceRequest(BaseModel):
    device_name: str = Field(max_length=64)
    platform: str = Field(default="android", max_length=16)
    app_version: str = Field(default="", max_length=32)


class RegisterDeviceResponse(BaseModel):
    device_id: int
    device_name: str
    platform: str


class VpnConfigResponse(BaseModel):
    device_id: int
    device_name: str
    vpn_link: str | None
    vpn_config: str | None


class ReplaceVpnConfigRequest(BaseModel):
    device_id: int = Field(gt=0)


class UserProfileResponse(BaseModel):
    user_id: int
    name: str
    email: str | None
    auth_provider: str
    telegram_linked: bool
    telegram_id: int | None
    telegram_username: str | None
    can_unlink_telegram: bool
    cabinet_url: str


class TelegramStatusResponse(BaseModel):
    linked: bool
    telegram_id: int | None
    telegram_username: str | None
    auth_provider: str
    can_unlink: bool


class TelegramLinkResponse(BaseModel):
    bot_username: str
    link_url: str
    link_token: str
    expires_in_hours: int = 24


class TelegramUnlinkResponse(BaseModel):
    ok: bool
    telegram_linked: bool


class UserBalanceResponse(BaseModel):
    balance_rub: float
    currency: str = "RUB"


class UserSubscriptionResponse(BaseModel):
    status: str
    end_date: str | None
    days_left: int
    daily_cost_rub: float
    device_count: int
    max_devices: int


class PaymentAmountPreset(BaseModel):
    days: int
    amount_rub: float


class PaymentMethodItem(BaseModel):
    id: int
    label: str
    min_amount_rub: float


class PaymentMethodsResponse(BaseModel):
    online_payment_enabled: bool
    payment_provider: str
    daily_price_rub: float
    min_topup_rub: float
    deposit_multiplier: float
    min_usdt: float
    amount_presets: list[PaymentAmountPreset]
    methods: list[PaymentMethodItem]


class CreatePaymentRequest(BaseModel):
    pay_method: int
    days: int | None = Field(default=None, ge=1, le=365)
    amount_rub: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_amount_or_days(self) -> "CreatePaymentRequest":
        if self.days is None and self.amount_rub is None:
            raise ValueError("Укажите days или amount_rub")
        return self


class CreatePaymentResponse(BaseModel):
    payment_id: int
    payment_url: str
    amount_rub: float
    days_purchased: int


class PaymentHistoryItem(BaseModel):
    id: int
    amount_rub: float
    days_purchased: int | None
    status: str
    source: str
    created_at: str
    processed_at: str | None


class PaymentHistoryResponse(BaseModel):
    items: list[PaymentHistoryItem]


async def _subscription_payload(session: AsyncSession, user: User) -> UserSubscriptionResponse:
    days_left = await days_left_for(session, user)
    device_count = await count_devices(session, user)
    daily_cost = await user_daily_cost(session, user)
    if device_count <= 0:
        status = "inactive"
    elif days_left <= 0:
        status = "expired"
    else:
        status = "active"
    end_date = (date.today() + timedelta(days=days_left)).isoformat() if days_left > 0 else None
    return UserSubscriptionResponse(
        status=status,
        end_date=end_date,
        days_left=days_left,
        daily_cost_rub=daily_cost,
        device_count=device_count,
        max_devices=settings.max_devices,
    )


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap() -> BootstrapResponse:
    return BootstrapResponse(
        brand_name=settings.brand_name,
        daily_price_rub=settings.daily_price_rub,
        max_devices=settings.max_devices,
        support_tg_url=settings.support_tg_url(),
        api_base_url=settings.web_base_url.rstrip("/"),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> UserResponse:
    device_count = await count_devices(session, user)
    return UserResponse(
        first_name=user.first_name,
        username=user.username,
        balance_rub=user.balance_rub,
        days_left=await days_left_for(session, user),
        daily_cost_rub=await user_daily_cost(session, user),
        device_count=device_count,
        max_devices=settings.max_devices,
        cabinet_token=user.cabinet_token,
    )


@router.get("/user/profile", response_model=UserProfileResponse)
async def user_profile(user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=user.id,
        name=user_display_name(user),
        email=user.email,
        auth_provider=user.auth_provider,
        telegram_linked=bool(user.telegram_id),
        telegram_id=user.telegram_id,
        telegram_username=user.username if user.telegram_id else None,
        can_unlink_telegram=can_unlink_telegram(user),
        cabinet_url=settings.cabinet_url(user.cabinet_token),
    )


@router.get("/user/telegram", response_model=TelegramStatusResponse)
async def user_telegram_status(user: User = Depends(get_current_user)) -> TelegramStatusResponse:
    return TelegramStatusResponse(
        linked=bool(user.telegram_id),
        telegram_id=user.telegram_id,
        telegram_username=user.username if user.telegram_id else None,
        auth_provider=user.auth_provider,
        can_unlink=can_unlink_telegram(user),
    )


@router.get("/user/telegram/link", response_model=TelegramLinkResponse)
async def user_telegram_link(user: User = Depends(get_current_user)) -> TelegramLinkResponse:
    if user.telegram_id:
        raise HTTPException(status_code=400, detail="Telegram уже привязан")
    token = make_telegram_link_token(user.id)
    return TelegramLinkResponse(
        bot_username=settings.bot_username,
        link_url=telegram_link_url(user.id),
        link_token=token,
    )


@router.post("/user/telegram/unlink", response_model=TelegramUnlinkResponse)
async def user_telegram_unlink(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TelegramUnlinkResponse:
    error = await unlink_telegram_from_user(session, user)
    if error:
        raise HTTPException(status_code=400, detail=error)
    await session.refresh(user)
    return TelegramUnlinkResponse(ok=True, telegram_linked=bool(user.telegram_id))


@router.get("/user/balance", response_model=UserBalanceResponse)
async def user_balance(user: User = Depends(get_current_user)) -> UserBalanceResponse:
    return UserBalanceResponse(balance_rub=user.balance_rub)


@router.get("/user/subscription", response_model=UserSubscriptionResponse)
async def user_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserSubscriptionResponse:
    return await _subscription_payload(session, user)


def _mobile_pay_method_ids() -> list[int]:
    if settings.active_payment_provider == "cardlink":
        return [FREEKASSA_METHOD_SBP, FREEKASSA_METHOD_CARD]
    return sorted(FREEKASSA_PAY_METHODS)


def _resolve_payment_days_and_amount(*, days: int | None, amount_rub: float | None) -> tuple[int, float]:
    if days is not None:
        resolved_days = days
    else:
        daily = settings.daily_price_rub
        resolved_days = max(1, min(365, round(float(amount_rub) / daily)))
    amount = settings.price_for_days(resolved_days)
    return resolved_days, amount


def _payment_history_item(payment: Payment) -> PaymentHistoryItem:
    return PaymentHistoryItem(
        id=payment.id,
        amount_rub=payment.amount_rub,
        days_purchased=payment.days_purchased,
        status=payment.status,
        source=payment.source,
        created_at=payment.created_at.isoformat() if payment.created_at else "",
        processed_at=payment.processed_at.isoformat() if payment.processed_at else None,
    )


@router.get("/payments/methods", response_model=PaymentMethodsResponse)
async def payment_methods(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentMethodsResponse:
    del user
    min_topup = await get_min_topup(session)
    deposit_multiplier = await get_deposit_multiplier(session)
    day_presets = sorted({10, 14, 15, 30, 45, 60, 90, 180})
    amount_presets = [
        PaymentAmountPreset(days=days, amount_rub=settings.price_for_days(days))
        for days in day_presets
    ]
    methods = [
        PaymentMethodItem(
            id=method_id,
            label=FREEKASSA_PAY_METHOD_LABELS[method_id],
            min_amount_rub=min_amount_rub_for_pay_method(
                method_id,
                min_topup,
                usdt_rub_rate=settings.usdt_rub_rate,
            ),
        )
        for method_id in _mobile_pay_method_ids()
    ]
    return PaymentMethodsResponse(
        online_payment_enabled=settings.online_payment_enabled,
        payment_provider=settings.active_payment_provider,
        daily_price_rub=settings.daily_price_rub,
        min_topup_rub=min_topup,
        deposit_multiplier=deposit_multiplier,
        min_usdt=FREEKASSA_MIN_USDT,
        amount_presets=amount_presets,
        methods=methods,
    )


@router.post("/payments/create", response_model=CreatePaymentResponse)
async def create_payment(
    body: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CreatePaymentResponse:
    if not settings.online_payment_enabled:
        raise HTTPException(status_code=503, detail="Онлайн-оплата временно недоступна")

    allowed_methods = _mobile_pay_method_ids()
    if body.pay_method not in allowed_methods:
        raise HTTPException(status_code=400, detail="Недоступный способ оплаты")

    days, amount = _resolve_payment_days_and_amount(days=body.days, amount_rub=body.amount_rub)
    min_topup = await get_min_topup(session)
    min_effective = min_amount_rub_for_pay_method(
        body.pay_method,
        min_topup,
        usdt_rub_rate=settings.usdt_rub_rate,
    )
    if amount < min_effective:
        raise HTTPException(
            status_code=400,
            detail=f"Минимальная сумма для выбранного способа — {min_effective:.0f} ₽",
        )

    if settings.active_payment_provider == "cardlink":
        if not settings.cardlink_enabled:
            raise HTTPException(status_code=503, detail="Онлайн-оплата временно недоступна")
        await cancel_pending_cardlink_for_user(session, user)
        payment = await create_payment_request(
            session,
            user,
            amount,
            days,
            source="cardlink",
        )
        try:
            payment_url = await cardlink_service.create_bill(
                amount,
                str(payment.id),
                description=f"Пополнение баланса · {days} дн.",
                payer_email=cardlink_service.payer_email_for_user(user),
                payment_method=cardlink_service.payment_method_from_freekassa(body.pay_method),
            )
        except cardlink_service.CardlinkApiError as exc:
            await reject_payment(session, payment, "Ошибка создания счёта Cardlink")
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        if not settings.freekassa_enabled:
            raise HTTPException(status_code=503, detail="Онлайн-оплата временно недоступна")
        if body.pay_method not in FREEKASSA_PAY_METHODS:
            raise HTTPException(status_code=400, detail="Недоступный способ оплаты")
        await cancel_pending_freekassa_for_user(session, user)
        payment = await create_payment_request(
            session,
            user,
            amount,
            days,
            source="freekassa",
        )
        client_ip = settings.freekassa_client_ip_fallback or "127.0.0.1"
        try:
            payment_url = await create_payment_order(
                amount,
                str(payment.id),
                payment_email_for_user(user),
                client_ip,
                body.pay_method,
            )
        except FreekassaApiError as exc:
            await reject_payment(session, payment, "Ошибка создания заказа Freekassa")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return CreatePaymentResponse(
        payment_id=payment.id,
        payment_url=payment_url,
        amount_rub=amount,
        days_purchased=days,
    )


@router.get("/payments/history", response_model=PaymentHistoryResponse)
async def payment_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentHistoryResponse:
    payments = await list_user_payments(session, user)
    return PaymentHistoryResponse(items=[_payment_history_item(payment) for payment in payments])


@router.get("/devices", response_model=list[DeviceResponse])
async def devices(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> list[DeviceResponse]:
    rows = await list_devices(session, user)
    return [
        DeviceResponse(
            id=d.id,
            name=d.name,
            platform=d.platform,
            platform_label=platform_label(d.platform),
            has_vpn=bool(d.vpn_link or d.vpn_config),
        )
        for d in rows
    ]


@router.post("/devices", response_model=DeviceResponse, status_code=201)
async def create_device(
    body: CreateDeviceRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeviceResponse:
    try:
        device = await add_device(session, user, body.platform, body.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DeviceResponse(
        id=device.id,
        name=device.name,
        platform=device.platform,
        platform_label=platform_label(device.platform),
        has_vpn=bool(device.vpn_link or device.vpn_config),
    )


@router.post("/devices/register", response_model=RegisterDeviceResponse, status_code=201)
async def register_device(
    body: RegisterDeviceRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RegisterDeviceResponse:
    try:
        device = await add_device(session, user, body.platform, body.device_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RegisterDeviceResponse(
        device_id=device.id,
        device_name=device.name,
        platform=device.platform,
    )


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    removed = await remove_device(session, user, device_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return {"ok": True}


@router.get("/devices/{device_id}/vpn", response_model=VpnConfigResponse)
async def device_vpn(
    device_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> VpnConfigResponse:
    device = await get_device(session, user, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    config = get_device_config(device)
    link = public_vpn_link_for_device(device)
    if not link and config:
        link = public_vpn_link(extract_vpn_link({"config": config}), device.panel_server_id)
    if not link and not config:
        raise HTTPException(status_code=404, detail="VPN-ключ недоступен")
    return VpnConfigResponse(
        device_id=device.id,
        device_name=device.name,
        vpn_link=link,
        vpn_config=config or None,
    )


@router.post("/vpn/replace-config", response_model=VpnConfigResponse)
async def replace_vpn_config(
    body: ReplaceVpnConfigRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> VpnConfigResponse:
    try:
        device = await replace_device_vpn_config(session, user, body.device_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    config = get_device_config(device)
    if not config:
        raise HTTPException(status_code=500, detail="Не удалось получить VPN-конфигурацию")

    link = public_vpn_link_for_device(device)
    if not link and config:
        link = public_vpn_link(extract_vpn_link({"config": config}), device.panel_server_id)

    return VpnConfigResponse(
        device_id=device.id,
        device_name=device.name,
        vpn_link=link,
        vpn_config=config,
    )
