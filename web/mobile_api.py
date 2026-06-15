"""REST API for the DaddyVPN Android app."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.database.session import async_session
from bot.services.devices import (
    add_device,
    count_devices,
    days_left_for,
    get_device,
    get_device_config,
    list_devices,
    platform_label,
    remove_device,
    user_daily_cost,
)
from bot.services.users import get_user_by_cabinet_token
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


class VpnConfigResponse(BaseModel):
    device_id: int
    device_name: str
    vpn_link: str | None
    vpn_config: str | None


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
    link = public_vpn_link(device.vpn_link)
    if not link and config:
        link = public_vpn_link(extract_vpn_link({"config": config}))
    if not link and not config:
        raise HTTPException(status_code=404, detail="VPN-ключ недоступен")
    return VpnConfigResponse(
        device_id=device.id,
        device_name=device.name,
        vpn_link=link,
        vpn_config=config or None,
    )
