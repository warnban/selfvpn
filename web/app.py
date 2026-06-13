import uuid
from pathlib import Path

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, User
from bot.database.session import async_session, init_db
from bot.services.notify import notify_balance_credited, notify_payment_approved, notify_payment_rejected
from bot.services.devices import (
    add_device,
    count_devices,
    days_left_for,
    list_devices,
    platform_label,
    remove_device,
    user_daily_cost,
)
from bot.services.users import (
    admin_credit_balance,
    approve_payment,
    count_referrals,
    create_payment_request,
    get_user_by_cabinet_token,
    get_user_by_id,
    list_all_users,
    reject_payment,
)

from bot.messages import AMNEZIA_ANDROID, AMNEZIA_IOS

app = FastAPI(title="SelfVPN Cabinet")
app.add_middleware(SessionMiddleware, secret_key=settings.web_secret_key)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals["brand_name"] = settings.brand_name
templates.env.globals["amnezia_android"] = AMNEZIA_ANDROID
templates.env.globals["amnezia_ios"] = AMNEZIA_IOS
templates.env.globals["platform_label"] = platform_label
templates.env.globals["max_devices"] = settings.max_devices

static_path = Path(__file__).parent / "static"
(static_path / "css").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
uploads_path = Path(settings.uploads_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def is_admin(request: Request) -> bool:
    return request.session.get("admin") is True


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def index() -> RedirectResponse:
    return RedirectResponse("/admin/login")


@app.get("/cabinet/{token}", response_class=HTMLResponse)
async def cabinet(request: Request, token: str, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": "Не найдено", "message": "Ссылка недействительна."},
            status_code=404,
        )

    refs = await count_referrals(session, user)
    devices = await list_devices(session, user)
    cost = await user_daily_cost(session, user)
    left = await days_left_for(session, user)
    return templates.TemplateResponse(
        request,
        "cabinet.html",
        {
            "user": user,
            "days_left": left,
            "daily_price": settings.daily_price_rub,
            "daily_cost": cost,
            "devices": devices,
            "device_count": len(devices),
            "referrals": refs,
            "referral_bonus": settings.referral_bonus_rub,
            "payment_card": settings.payment_card,
            "payment_bank": settings.payment_bank,
            "payment_holder": settings.payment_holder,
        },
    )


@app.post("/cabinet/{token}/devices/add")
async def cabinet_device_add(
    token: str,
    platform: str = Form("other"),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    try:
        await add_device(session, user, platform)
    except Exception as exc:
        from urllib.parse import quote

        return RedirectResponse(f"/cabinet/{token}?err={quote(str(exc)[:120])}", status_code=303)
    return RedirectResponse(f"/cabinet/{token}#devices", status_code=303)


@app.post("/cabinet/{token}/devices/{device_id}/remove")
async def cabinet_device_remove(
    token: str,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    await remove_device(session, user, device_id)
    return RedirectResponse(f"/cabinet/{token}#devices", status_code=303)


@app.get("/cabinet/{token}/pay", response_class=HTMLResponse)
async def cabinet_pay_form(request: Request, token: str, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "pay.html",
        {
            "user": user,
            "daily_price": settings.daily_price_rub,
            "presets": [7, 14, 30, 60, 90],
            "payment_card": settings.payment_card,
            "payment_bank": settings.payment_bank,
            "payment_holder": settings.payment_holder,
        },
    )


@app.post("/cabinet/{token}/pay")
async def cabinet_pay_submit(
    token: str,
    days: int = Form(...),
    screenshot: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)

    if days < 1 or days > 365:
        return RedirectResponse(f"/cabinet/{token}/pay", status_code=303)

    amount = settings.price_for_days(days)
    ext = Path(screenshot.filename or "img.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = uploads_path / filename
    content = await screenshot.read()
    dest.write_bytes(content)

    await create_payment_request(
        session,
        user,
        amount,
        days,
        source="web",
        screenshot_path=f"/uploads/{filename}",
    )
    return RedirectResponse(f"/cabinet/{token}?paid=1", status_code=303)


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    if is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", {})


@app.post("/admin/login")
async def admin_login(request: Request, password: str = Form(...)):
    if password == settings.admin_web_password:
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login?error=1", status_code=303)


@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, session: AsyncSession = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    users = await list_all_users(session)
    pending = (
        await session.execute(select(Payment).where(Payment.status == PaymentStatus.PENDING.value))
    ).scalars().all()
    pending_rows = []
    for payment in pending:
        u = await session.get(User, payment.user_id)
        pending_rows.append({"payment": payment, "user": u})

    from bot.database.models import Device

    devices = (await session.execute(select(Device))).scalars().all()
    device_counts: dict[int, int] = {}
    for d in devices:
        device_counts[d.user_id] = device_counts.get(d.user_id, 0) + 1
    active_vpn = len(devices)

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "users": users,
            "pending_payments": pending_rows,
            "daily_price": settings.daily_price_rub,
            "active_vpn": active_vpn,
            "device_counts": device_counts,
        },
    )


@app.post("/admin/users/{user_id}/credit")
async def admin_credit(
    request: Request,
    user_id: int,
    amount: float = Form(...),
    comment: str = Form(""),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    user = await get_user_by_id(session, user_id)
    if not user or amount <= 0:
        return RedirectResponse("/admin", status_code=303)

    await admin_credit_balance(session, user, amount, comment or None)
    await notify_balance_credited(
        user.telegram_id,
        amount,
        user.balance_rub,
        comment or "Начисление администратором",
    )
    return RedirectResponse("/admin?credited=1", status_code=303)


@app.post("/admin/payments/{payment_id}/approve")
async def admin_approve_payment_web(
    request: Request,
    payment_id: int,
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    payment = await session.get(Payment, payment_id)
    if not payment or payment.status != PaymentStatus.PENDING.value:
        return RedirectResponse("/admin", status_code=303)

    user = await approve_payment(session, payment)
    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
    )
    return RedirectResponse("/admin?approved=1", status_code=303)


@app.post("/admin/payments/{payment_id}/reject")
async def admin_reject_payment_web(
    request: Request,
    payment_id: int,
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    payment = await session.get(Payment, payment_id)
    if not payment or payment.status != PaymentStatus.PENDING.value:
        return RedirectResponse("/admin", status_code=303)

    await reject_payment(session, payment)
    user = await session.get(User, payment.user_id)
    if user:
        await notify_payment_rejected(user.telegram_id)
    return RedirectResponse("/admin?rejected=1", status_code=303)
