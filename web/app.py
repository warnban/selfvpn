from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
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
    get_device,
    get_device_config,
    list_devices,
    platform_label,
    remove_device,
    user_daily_cost,
)
from bot.services.app_settings import get_stars_per_day, set_stars_per_day
from bot.services.users import (
    admin_credit_balance,
    approve_payment,
    count_referrals,
    create_payment_request,
    cancel_pending_freekassa_for_user,
    get_user_by_cabinet_token,
    get_user_by_id,
    list_all_users,
    reject_payment,
)

from bot.services.freekassa import (
    FREEKASSA_PAY_URL,
    get_client_ip,
    is_freekassa_ip,
    payment_form_fields,
    verify_notification_signature,
)
from bot.messages import AMNEZIA_ANDROID, AMNEZIA_WG_APPLE
from bot.services.vpn_config import safe_conf_filename

app = FastAPI(title="SelfVPN Cabinet")
app.add_middleware(SessionMiddleware, secret_key=settings.web_secret_key)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals["brand_name"] = settings.brand_name
templates.env.globals["support_tg"] = settings.support_tg_handle
templates.env.globals["support_tg_url"] = settings.support_tg_url()
templates.env.globals["amnezia_android"] = AMNEZIA_ANDROID
templates.env.globals["amnezia_wg_apple"] = AMNEZIA_WG_APPLE
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


landing_path = Path(__file__).parent / "landing"
landing_index = landing_path / "index.html"


@app.get("/health")
async def health() -> PlainTextResponse:
    return PlainTextResponse("ok")


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


@app.get("/cabinet/{token}/devices/{device_id}/conf")
async def cabinet_device_conf(
    token: str,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return PlainTextResponse("Not found", status_code=404)

    device = await get_device(session, user, device_id)
    if not device:
        return PlainTextResponse("Not found", status_code=404)

    config = get_device_config(device)
    if not config:
        return PlainTextResponse("Conf unavailable", status_code=404)

    filename = safe_conf_filename(device.name, device.id)
    return Response(
        content=config.encode("utf-8"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
            "freekassa_enabled": settings.freekassa_enabled,
        },
    )


@app.post("/cabinet/{token}/pay")
async def cabinet_pay_submit(
    request: Request,
    token: str,
    days: int = Form(...),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)

    if days < 1 or days > 365:
        return RedirectResponse(f"/cabinet/{token}/pay", status_code=303)

    if not settings.freekassa_enabled:
        return RedirectResponse(f"/cabinet/{token}/pay", status_code=303)

    amount = settings.price_for_days(days)
    await cancel_pending_freekassa_for_user(session, user)
    payment = await create_payment_request(
        session,
        user,
        amount,
        days,
        source="freekassa",
    )
    fields = payment_form_fields(
        amount,
        str(payment.id),
        cabinet_token=user.cabinet_token,
    )
    return templates.TemplateResponse(
        request,
        "pay_redirect.html",
        {
            "pay_url": FREEKASSA_PAY_URL,
            "fields": fields,
            "amount": amount,
            "days": days,
        },
    )


async def _resolve_cabinet_token(request: Request, session: AsyncSession) -> str | None:
    token = request.query_params.get("us_token")
    if token:
        return token

    order_id = request.query_params.get("MERCHANT_ORDER_ID") or request.query_params.get("o")
    if not order_id:
        return None

    try:
        payment = await session.get(Payment, int(order_id))
    except (ValueError, TypeError):
        return None
    if not payment:
        return None

    user = await session.get(User, payment.user_id)
    return user.cabinet_token if user else None


@app.api_route("/payment/notify", methods=["GET", "POST"])
async def payment_notify(request: Request, session: AsyncSession = Depends(get_db)):
    if not settings.freekassa_enabled:
        return PlainTextResponse("disabled", status_code=503)

    client_ip = get_client_ip(request)
    if not is_freekassa_ip(client_ip):
        return PlainTextResponse("hacking attempt!", status_code=403)

    params = dict(await request.form()) if request.method == "POST" else dict(request.query_params)
    merchant_id = params.get("MERCHANT_ID", "")
    amount = params.get("AMOUNT", "")
    order_id = params.get("MERCHANT_ORDER_ID", "")
    signature = params.get("SIGN", "")

    if not merchant_id or not amount or not order_id or not signature:
        return PlainTextResponse("missing params", status_code=400)

    if str(merchant_id) != str(settings.freekassa_merchant_id):
        return PlainTextResponse("wrong merchant", status_code=400)

    if not verify_notification_signature(merchant_id, amount, order_id, signature):
        return PlainTextResponse("wrong sign", status_code=400)

    try:
        payment = await session.get(Payment, int(order_id))
    except (ValueError, TypeError):
        return PlainTextResponse("bad order", status_code=400)

    if not payment:
        return PlainTextResponse("order not found", status_code=404)

    if payment.status == PaymentStatus.APPROVED.value:
        return PlainTextResponse("YES")

    if abs(float(amount) - payment.amount_rub) > 0.01:
        return PlainTextResponse("wrong amount", status_code=400)

    user = await approve_payment(session, payment)
    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
    )
    return PlainTextResponse("YES")


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success(request: Request, session: AsyncSession = Depends(get_db)):
    token = await _resolve_cabinet_token(request, session)
    if token:
        return RedirectResponse(f"/cabinet/{token}?paid=ok", status_code=303)
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        {"success": True, "title": "Оплата прошла", "message": "Баланс пополнен. Вернитесь в личный кабинет по сохранённой ссылке."},
    )


@app.get("/payment/fail", response_class=HTMLResponse)
async def payment_fail(request: Request, session: AsyncSession = Depends(get_db)):
    order_id = request.query_params.get("MERCHANT_ORDER_ID") or request.query_params.get("o")
    if order_id:
        try:
            payment = await session.get(Payment, int(order_id))
            if (
                payment
                and payment.source == "freekassa"
                and payment.status == PaymentStatus.PENDING.value
            ):
                await reject_payment(session, payment, "Оплата не завершена")
        except (ValueError, TypeError):
            pass

    token = await _resolve_cabinet_token(request, session)
    if token:
        return RedirectResponse(f"/cabinet/{token}?paid=fail", status_code=303)
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        {"success": False, "title": "Оплата не прошла", "message": "Платёж отменён или произошла ошибка. Попробуйте снова из личного кабинета."},
    )


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
        await session.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.PENDING.value,
                Payment.source.notin_(["freekassa", "stars"]),
            )
        )
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
    stars_per_day = await get_stars_per_day(session)

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "users": users,
            "pending_payments": pending_rows,
            "daily_price": settings.daily_price_rub,
            "stars_per_day": stars_per_day,
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
    if payment.source in ("freekassa", "stars"):
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
    if payment.source in ("freekassa", "stars"):
        return RedirectResponse("/admin", status_code=303)

    await reject_payment(session, payment)
    user = await session.get(User, payment.user_id)
    if user:
        await notify_payment_rejected(user.telegram_id)
    return RedirectResponse("/admin?rejected=1", status_code=303)


@app.post("/admin/settings/stars")
async def admin_update_stars(
    request: Request,
    stars_per_day: int = Form(...),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    await set_stars_per_day(session, stars_per_day)
    return RedirectResponse("/admin?stars_saved=1", status_code=303)


if landing_index.is_file():
    app.mount(
        "/",
        StaticFiles(directory=str(landing_path), html=True),
        name="landing",
    )
else:
    @app.get("/", response_class=HTMLResponse)
    async def index() -> RedirectResponse:
        return RedirectResponse("/admin/login")
