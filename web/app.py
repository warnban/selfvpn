from collections.abc import AsyncGenerator
import json
import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, User
from bot.database.session import init_db
from bot.services.notify import notify_balance_credited, notify_payment_approved, notify_payment_rejected
from bot.services.devices import (
    add_device,
    get_device,
    get_device_config,
    platform_label,
    remove_device,
)
from bot.services.app_settings import (
    ALLOWED_DEPOSIT_MULTIPLIERS,
    get_deposit_multiplier,
    get_min_topup,
    get_stars_per_day,
    set_deposit_multiplier,
    set_min_topup,
    set_stars_per_day,
)
from bot.services.users import (
    admin_credit_balance,
    approve_payment,
    create_payment_request,
    cancel_pending_freekassa_for_user,
    cancel_pending_cardlink_for_user,
    get_user_by_cabinet_token,
    get_user_by_id,
    list_all_users,
    list_top_referrers,
    count_all_referrals,
    reject_payment,
)
from bot.services.partners import (
    build_admin_partner_stats,
    record_partner_payout,
    set_partner_config,
)

from bot.services.freekassa import (
    FreekassaApiError,
    FREEKASSA_METHOD_SBP,
    FREEKASSA_PAY_METHODS,
    create_payment_order,
    get_client_ip,
    is_freekassa_ip,
    payment_email_for_user,
    resolve_payment_client_ip,
    verify_notification_signature,
)
from bot.services import cardlink as cardlink_service
from bot.services.auth import user_display_name, admin_user_subtitle
from bot.messages import (
    AMNEZIA_ANDROID,
    AMNEZIA_WINDOWS,
    AMNEZIA_WG_APPLE,
    app_download_label,
    app_download_url,
)
from bot.services.vpn_config import safe_conf_filename
from web.auth_routes import router as auth_router
from web.cabinet_helpers import (
    build_cabinet_context,
    cabinet_base_path,
    complete_onboarding,
    get_user_from_session,
    login_session,
    needs_onboarding,
    onboarding_base_path,
)
from web.deps import get_db, templates
from web.mobile_api import router as mobile_router

logger = logging.getLogger(__name__)

app = FastAPI(title="SelfVPN Cabinet")
app.include_router(mobile_router)
app.include_router(auth_router)
app.add_middleware(SessionMiddleware, secret_key=settings.web_secret_key)


@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    import logging
    import time

    access_log = logging.getLogger("selfvpn.access")
    path = request.url.path
    if path.startswith("/auth/") or path.startswith("/cabinet"):
        started = time.monotonic()
        access_log.info("→ %s %s", request.method, path)
        response = await call_next(request)
        access_log.info(
            "← %s %s %s (%.2fs)",
            request.method,
            path,
            response.status_code,
            time.monotonic() - started,
        )
        return response
    return await call_next(request)

templates.env.globals["brand_name"] = settings.brand_name
templates.env.globals["support_tg"] = settings.support_tg_handle
templates.env.globals["support_tg_url"] = settings.support_tg_url()
templates.env.globals["amnezia_android"] = AMNEZIA_ANDROID
templates.env.globals["amnezia_windows"] = AMNEZIA_WINDOWS
templates.env.globals["amnezia_wg_apple"] = AMNEZIA_WG_APPLE
templates.env.globals["app_download_url"] = app_download_url
templates.env.globals["app_download_label"] = app_download_label
templates.env.globals["platform_label"] = platform_label
templates.env.globals["user_display_name"] = user_display_name
templates.env.globals["admin_user_subtitle"] = admin_user_subtitle
templates.env.globals["max_devices"] = settings.max_devices
templates.env.globals["support_phone_tel"] = "89169046701"
templates.env.globals["support_phone_display"] = "+7 (916) 904-67-01"

static_path = Path(__file__).parent / "static"
(static_path / "css").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
uploads_path = Path(settings.uploads_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


def _pwa_short_name() -> str:
    name = (settings.brand_name or "Кабинет").strip()
    return name if len(name) <= 12 else "Кабинет"


@app.get("/manifest.webmanifest")
async def web_app_manifest():
    manifest = {
        "id": "/cabinet",
        "name": settings.brand_name,
        "short_name": _pwa_short_name(),
        "description": f"Личный кабинет {settings.brand_name}",
        "start_url": "/cabinet",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#0d0f12",
        "theme_color": "#0d0f12",
        "lang": "ru",
        "icons": [
            {
                "src": "/static/pwa/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            },
            {
                "src": "/static/pwa/icon-maskable.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "maskable",
            },
        ],
    }
    return Response(
        content=json.dumps(manifest, ensure_ascii=False),
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/sw.js")
async def service_worker():
    sw_path = static_path / "js" / "sw.js"
    return Response(
        content=sw_path.read_text(encoding="utf-8"),
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache",
            "Service-Worker-Allowed": "/",
        },
    )


def _payment_redirect_cabinet(user: User, query: str) -> str:
    return f"/cabinet/{user.cabinet_token}{query}"


async def _render_cabinet(
    request: Request,
    user: User,
    session: AsyncSession,
    *,
    via_session: bool,
    admin_preview: bool = False,
):
    ctx = await build_cabinet_context(request, user, session, via_session=via_session)
    ctx["bonus_status"] = request.query_params.get("bonus")
    ctx["admin_preview"] = admin_preview
    return templates.TemplateResponse(request, "cabinet.html", ctx)


async def _render_onboarding(
    request: Request,
    user: User,
    session: AsyncSession,
    *,
    via_session: bool,
):
    ctx = await build_cabinet_context(request, user, session, via_session=via_session)
    if ctx["device_count"] > 0:
        try:
            step = int(request.query_params.get("step", "2"))
        except (TypeError, ValueError):
            step = 2
        ctx["onboarding_step"] = max(2, min(3, step))
    else:
        ctx["onboarding_step"] = 1
    return templates.TemplateResponse(request, "onboarding.html", ctx)


def _redirect_after_device_add(user: User, *, via_session: bool, err: str | None = None) -> str:
    from urllib.parse import quote

    if needs_onboarding(user):
        base = onboarding_base_path(user, via_session)
        if err:
            return f"{base}?err={quote(err)}&step=1"
        return f"{base}?step=2&created=1"
    base = cabinet_base_path(user, via_session)
    if err:
        return f"{base}?err={quote(err)}"
    return f"{base}?created=1#devices"


def is_admin(request: Request) -> bool:
    return request.session.get("admin") is True


def _maybe_login_cabinet_user(request: Request, user: User) -> None:
    if not is_admin(request):
        login_session(request, user)


@app.on_event("startup")
async def startup() -> None:
    await init_db()


landing_path = Path(__file__).parent / "landing"
landing_index = landing_path / "index.html"


@app.get("/health")
async def health() -> PlainTextResponse:
    return PlainTextResponse("ok")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt() -> PlainTextResponse:
    base = settings.web_base_url.rstrip("/")
    return PlainTextResponse(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                "Disallow: /admin",
                "Disallow: /cabinet",
                "Disallow: /auth",
                "Disallow: /payment",
                "",
                f"Sitemap: {base}/sitemap.xml",
            ]
        )
    )


@app.get("/sitemap.xml")
async def sitemap_xml() -> Response:
    base = settings.web_base_url.rstrip("/")
    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"  <url><loc>{base}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
        f"  <url><loc>{base}/about</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    referer = request.headers.get("referer") or ""
    back_url = ""
    if referer and "/about" not in referer.rstrip("/").split("?")[0]:
        if any(part in referer for part in ("/cabinet/", "/pay", "/payment/", "/admin")):
            back_url = referer
    return templates.TemplateResponse(
        request,
        "about.html",
        {"back_url": back_url},
    )


CABINET_RESERVED = frozenset({"pay", "profile", "devices", "add", "onboarding"})


def _is_cabinet_token(value: str) -> bool:
    return value not in CABINET_RESERVED and len(value) >= 16


@app.get("/cabinet", response_class=HTMLResponse)
async def cabinet_session(request: Request, session: AsyncSession = Depends(get_db)):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login?next=/cabinet", status_code=303)
    if needs_onboarding(user):
        return RedirectResponse("/cabinet/onboarding", status_code=303)
    return await _render_cabinet(request, user, session, via_session=True)


@app.get("/cabinet/onboarding", response_class=HTMLResponse)
async def cabinet_session_onboarding(request: Request, session: AsyncSession = Depends(get_db)):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login?next=/cabinet/onboarding", status_code=303)
    if not needs_onboarding(user):
        return RedirectResponse("/cabinet", status_code=303)
    return await _render_onboarding(request, user, session, via_session=True)


@app.post("/cabinet/onboarding/complete")
async def cabinet_session_onboarding_complete(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    if not await complete_onboarding(session, user):
        from urllib.parse import quote

        return RedirectResponse(
            "/cabinet/onboarding?err=" + quote("Сначала добавьте устройство"),
            status_code=303,
        )
    return RedirectResponse("/cabinet", status_code=303)


@app.post("/cabinet/devices/add")
async def cabinet_session_device_add(
    request: Request,
    platform: str = Form("other"),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    base = cabinet_base_path(user, via_session=True)
    try:
        await add_device(session, user, platform)
    except Exception as exc:
        from urllib.parse import quote

        return RedirectResponse(_redirect_after_device_add(user, via_session=True, err=str(exc)[:120]), status_code=303)
    return RedirectResponse(_redirect_after_device_add(user, via_session=True), status_code=303)


@app.post("/cabinet/{token}/devices/add")
async def cabinet_device_add(
    token: str,
    platform: str = Form("other"),
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    try:
        await add_device(session, user, platform)
    except Exception as exc:
        return RedirectResponse(
            _redirect_after_device_add(user, via_session=False, err=str(exc)[:120]),
            status_code=303,
        )
    return RedirectResponse(_redirect_after_device_add(user, via_session=False), status_code=303)


@app.post("/cabinet/devices/{device_id}/remove")
async def cabinet_session_device_remove(
    request: Request,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    await remove_device(session, user, device_id)
    if needs_onboarding(user):
        return RedirectResponse("/cabinet/onboarding#connect", status_code=303)
    return RedirectResponse("/cabinet#devices", status_code=303)


@app.post("/cabinet/{token}/devices/{device_id}/remove")
async def cabinet_device_remove(
    token: str,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    await remove_device(session, user, device_id)
    if needs_onboarding(user):
        return RedirectResponse(f"/cabinet/{token}/onboarding#connect", status_code=303)
    return RedirectResponse(f"/cabinet/{token}#devices", status_code=303)


async def _handle_channel_bonus(session, user, redirect_to: str):
    from bot.services.channel import (
        GRANT_GRANTED,
        grant_channel_bonus,
    )
    from bot.services.notify import notify_balance_credited

    result = await grant_channel_bonus(session, user)
    if result == GRANT_GRANTED:
        try:
            await notify_balance_credited(
                user.telegram_id,
                settings.channel_bonus_rub,
                user.balance_rub,
                comment="Бонус за подписку на канал",
                user=user,
            )
        except Exception:
            logger.exception("Failed to notify about channel bonus")
    sep = "&" if "?" in redirect_to else "?"
    return RedirectResponse(f"{redirect_to}{sep}bonus={result}#balance", status_code=303)


@app.post("/cabinet/channel-bonus/check")
async def cabinet_session_channel_bonus(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    return await _handle_channel_bonus(session, user, "/cabinet")


@app.post("/cabinet/{token}/channel-bonus/check")
async def cabinet_channel_bonus(
    token: str,
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    return await _handle_channel_bonus(session, user, f"/cabinet/{token}")


@app.get("/cabinet/devices/{device_id}/conf")
async def cabinet_session_device_conf(
    request: Request,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return PlainTextResponse("Unauthorized", status_code=401)
    return await _device_conf_response(session, user, device_id)


@app.get("/cabinet/{token}/devices/{device_id}/conf")
async def cabinet_device_conf(
    token: str,
    device_id: int,
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return PlainTextResponse("Not found", status_code=404)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return PlainTextResponse("Not found", status_code=404)
    return await _device_conf_response(session, user, device_id)


async def _device_conf_response(session: AsyncSession, user: User, device_id: int):
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


def _pay_context(user: User, *, deposit_multiplier: float = 1.0, min_topup: float = 0.0) -> dict:
    return {
        "user": user,
        "daily_price": settings.daily_price_rub,
        "presets": [10, 14, 30, 60, 90],
        "payment_card": settings.payment_card,
        "payment_bank": settings.payment_bank,
        "payment_holder": settings.payment_holder,
        "freekassa_enabled": settings.freekassa_enabled,
        "online_payment_enabled": settings.online_payment_enabled,
        "payment_provider": settings.active_payment_provider,
        "cabinet_base": cabinet_base_path(user, via_session=not user.cabinet_token),
        "deposit_multiplier": deposit_multiplier,
        "min_topup": min_topup,
    }


@app.get("/cabinet/pay", response_class=HTMLResponse)
async def cabinet_session_pay_form(request: Request, session: AsyncSession = Depends(get_db)):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login?next=/cabinet/pay", status_code=303)
    ctx = _pay_context(
        user,
        deposit_multiplier=await get_deposit_multiplier(session),
        min_topup=await get_min_topup(session),
    )
    ctx["cabinet_base"] = "/cabinet"
    return templates.TemplateResponse(request, "pay.html", ctx)


@app.get("/cabinet/{token}/pay", response_class=HTMLResponse)
async def cabinet_pay_form(request: Request, token: str, session: AsyncSession = Depends(get_db)):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet/pay", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    ctx = _pay_context(
        user,
        deposit_multiplier=await get_deposit_multiplier(session),
        min_topup=await get_min_topup(session),
    )
    ctx["cabinet_base"] = f"/cabinet/{token}"
    return templates.TemplateResponse(request, "pay.html", ctx)


@app.post("/cabinet/pay")
async def cabinet_session_pay_submit(
    request: Request,
    days: int = Form(...),
    pay_method: int = Form(FREEKASSA_METHOD_SBP),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    return await _cabinet_pay_submit(
        request, user, days, session, pay_base="/cabinet", pay_method=pay_method
    )


@app.post("/cabinet/{token}/pay")
async def cabinet_pay_submit(
    request: Request,
    token: str,
    days: int = Form(...),
    pay_method: int = Form(FREEKASSA_METHOD_SBP),
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet/pay", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    return await _cabinet_pay_submit(
        request,
        user,
        days,
        session,
        pay_base=f"/cabinet/{token}",
        pay_method=pay_method,
    )


async def _cabinet_pay_submit(
    request: Request,
    user: User,
    days: int,
    session: AsyncSession,
    *,
    pay_base: str,
    pay_method: int,
):
    if days < 1 or days > 365:
        return RedirectResponse(f"{pay_base}/pay", status_code=303)

    amount = settings.price_for_days(days)

    min_topup = await get_min_topup(session)
    if amount < min_topup:
        return RedirectResponse(f"{pay_base}/pay?error=min", status_code=303)

    if settings.active_payment_provider == "cardlink":
        return await _cardlink_pay_submit(user, days, amount, session, pay_base=pay_base, pay_method=pay_method)

    if not settings.freekassa_enabled:
        return RedirectResponse(f"{pay_base}/pay", status_code=303)

    if pay_method not in FREEKASSA_PAY_METHODS:
        return RedirectResponse(f"{pay_base}/pay?error=method", status_code=303)

    await cancel_pending_freekassa_for_user(session, user)
    payment = await create_payment_request(
        session,
        user,
        amount,
        days,
        source="freekassa",
    )

    try:
        pay_url = await create_payment_order(
            amount,
            str(payment.id),
            payment_email_for_user(user),
            resolve_payment_client_ip(request),
            pay_method,
        )
    except FreekassaApiError as exc:
        logger.exception("Freekassa order creation failed for payment %s: %s", payment.id, exc)
        await reject_payment(session, payment, "Ошибка создания заказа Freekassa")
        return RedirectResponse(f"{pay_base}/pay?error=api", status_code=303)

    return RedirectResponse(pay_url, status_code=303)


async def _cardlink_pay_submit(
    user: User,
    days: int,
    amount: float,
    session: AsyncSession,
    *,
    pay_base: str,
    pay_method: int,
):
    if not settings.cardlink_enabled:
        return RedirectResponse(f"{pay_base}/pay", status_code=303)

    await cancel_pending_cardlink_for_user(session, user)
    payment = await create_payment_request(
        session,
        user,
        amount,
        days,
        source="cardlink",
    )

    try:
        pay_url = await cardlink_service.create_bill(
            amount,
            str(payment.id),
            description=f"Пополнение баланса · {days} дн.",
            payer_email=cardlink_service.payer_email_for_user(user),
            payment_method=cardlink_service.payment_method_from_freekassa(pay_method),
        )
    except cardlink_service.CardlinkApiError as exc:
        logger.exception("Cardlink bill creation failed for payment %s: %s", payment.id, exc)
        await reject_payment(session, payment, "Ошибка создания счёта Cardlink")
        return RedirectResponse(f"{pay_base}/pay?error=api", status_code=303)

    return RedirectResponse(pay_url, status_code=303)


@app.get("/cabinet/{token}", response_class=HTMLResponse)
async def cabinet(request: Request, token: str, session: AsyncSession = Depends(get_db)):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": "Не найдено", "message": "Ссылка недействительна."},
            status_code=404,
        )
    _maybe_login_cabinet_user(request, user)
    if needs_onboarding(user):
        return RedirectResponse(f"/cabinet/{token}/onboarding", status_code=303)
    return await _render_cabinet(request, user, session, via_session=False)


@app.get("/cabinet/{token}/onboarding", response_class=HTMLResponse)
async def cabinet_token_onboarding(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": "Не найдено", "message": "Ссылка недействительна."},
            status_code=404,
        )
    _maybe_login_cabinet_user(request, user)
    if not needs_onboarding(user):
        return RedirectResponse(f"/cabinet/{token}", status_code=303)
    return await _render_onboarding(request, user, session, via_session=False)


@app.post("/cabinet/{token}/onboarding/complete")
async def cabinet_token_onboarding_complete(
    token: str,
    session: AsyncSession = Depends(get_db),
):
    if not _is_cabinet_token(token):
        return RedirectResponse("/cabinet", status_code=303)
    user = await get_user_by_cabinet_token(session, token)
    if not user:
        return RedirectResponse("/", status_code=303)
    if not await complete_onboarding(session, user):
        from urllib.parse import quote

        return RedirectResponse(
            f"/cabinet/{token}/onboarding?err=" + quote("Сначала добавьте устройство"),
            status_code=303,
        )
    return RedirectResponse(f"/cabinet/{token}", status_code=303)


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

    user, credited = await approve_payment(session, payment)
    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
        credited=credited,
        user=user,
    )
    return PlainTextResponse("YES")


def _payment_return_path(user: User, *, via_session: bool, outcome: str) -> str:
    """After Freekassa return: users still in onboarding land on /pay, not /cabinet."""
    query = f"?paid={outcome}"
    if needs_onboarding(user):
        if via_session:
            return f"/cabinet/pay{query}"
        return f"/cabinet/{user.cabinet_token}/pay{query}"
    if via_session:
        return f"/cabinet{query}"
    return f"/cabinet/{user.cabinet_token}{query}"


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success(request: Request, session: AsyncSession = Depends(get_db)):
    user = await get_user_from_session(request, session)
    if user:
        return RedirectResponse(_payment_return_path(user, via_session=True, outcome="ok"), status_code=303)
    token = await _resolve_cabinet_token(request, session)
    if token:
        user = await get_user_by_cabinet_token(session, token)
        if user:
            return RedirectResponse(
                _payment_return_path(user, via_session=False, outcome="ok"),
                status_code=303,
            )
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

    user = await get_user_from_session(request, session)
    if user:
        return RedirectResponse(_payment_return_path(user, via_session=True, outcome="fail"), status_code=303)
    token = await _resolve_cabinet_token(request, session)
    if token:
        user = await get_user_by_cabinet_token(session, token)
        if user:
            return RedirectResponse(
                _payment_return_path(user, via_session=False, outcome="fail"),
                status_code=303,
            )
        return RedirectResponse(f"/cabinet/{token}?paid=fail", status_code=303)
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        {"success": False, "title": "Оплата не прошла", "message": "Платёж отменён или произошла ошибка. Попробуйте снова из личного кабинета."},
    )


# ──────────────────────────── Cardlink ────────────────────────────

async def _cardlink_redirect_for_inv(
    request: Request,
    session: AsyncSession,
    inv_id: str | None,
    outcome: str,
):
    """Найти пользователя по InvId (= payment.id) и увести в кабинет с результатом."""
    user = await get_user_from_session(request, session)
    if not user and inv_id:
        try:
            payment = await session.get(Payment, int(inv_id))
        except (ValueError, TypeError):
            payment = None
        if payment:
            user = await session.get(User, payment.user_id)
    if user:
        via_session = bool(request.session.get("user_id"))
        return RedirectResponse(
            _payment_return_path(user, via_session=via_session, outcome=outcome),
            status_code=303,
        )
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        {
            "success": outcome == "ok",
            "title": "Оплата прошла" if outcome == "ok" else "Оплата не прошла",
            "message": (
                "Баланс пополнен. Вернитесь в личный кабинет по сохранённой ссылке."
                if outcome == "ok"
                else "Платёж отменён или произошла ошибка. Попробуйте снова из личного кабинета."
            ),
        },
    )


async def _cardlink_form_or_query(request: Request) -> dict:
    if request.method == "POST":
        return dict(await request.form())
    return dict(request.query_params)


@app.api_route("/cardlink/success", methods=["GET", "POST"], response_class=HTMLResponse)
async def cardlink_success(request: Request, session: AsyncSession = Depends(get_db)):
    params = await _cardlink_form_or_query(request)
    inv_id = params.get("InvId")
    return await _cardlink_redirect_for_inv(request, session, inv_id, "ok")


@app.api_route("/cardlink/fail", methods=["GET", "POST"], response_class=HTMLResponse)
async def cardlink_fail(request: Request, session: AsyncSession = Depends(get_db)):
    params = await _cardlink_form_or_query(request)
    inv_id = params.get("InvId")
    if inv_id:
        try:
            payment = await session.get(Payment, int(inv_id))
            if (
                payment
                and payment.source == "cardlink"
                and payment.status == PaymentStatus.PENDING.value
            ):
                await reject_payment(session, payment, "Оплата не завершена")
        except (ValueError, TypeError):
            pass
    return await _cardlink_redirect_for_inv(request, session, inv_id, "fail")


@app.api_route("/cardlink/result", methods=["GET", "POST"])
async def cardlink_result(request: Request, session: AsyncSession = Depends(get_db)):
    params = await _cardlink_form_or_query(request)
    inv_id = params.get("InvId", "")
    out_sum = params.get("OutSum", "")
    status = params.get("Status", "")
    signature = params.get("SignatureValue", "")

    # Проверочный/пустой запрос (модерация Cardlink) — отвечаем 200, не пытаясь обработать.
    if not settings.cardlink_enabled or not (inv_id and out_sum and signature):
        return PlainTextResponse("OK")

    if not cardlink_service.verify_payment_signature(out_sum, inv_id, signature):
        return PlainTextResponse("wrong sign", status_code=400)

    try:
        payment = await session.get(Payment, int(inv_id))
    except (ValueError, TypeError):
        return PlainTextResponse("bad order", status_code=400)

    if not payment or payment.source != "cardlink":
        return PlainTextResponse("order not found", status_code=404)

    if status != "SUCCESS":
        if payment.status == PaymentStatus.PENDING.value:
            await reject_payment(session, payment, f"Cardlink статус: {status}")
        return PlainTextResponse("OK")

    if payment.status == PaymentStatus.APPROVED.value:
        return PlainTextResponse("OK")

    if abs(float(out_sum) - payment.amount_rub) > 0.01:
        return PlainTextResponse("wrong amount", status_code=400)

    user, credited = await approve_payment(session, payment)
    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
        credited=credited,
        user=user,
    )
    return PlainTextResponse("OK")


@app.api_route("/cardlink/refund", methods=["GET", "POST"])
async def cardlink_refund(request: Request, session: AsyncSession = Depends(get_db)):
    form = await _cardlink_form_or_query(request)
    refund_id = form.get("Id", "")
    amount = form.get("Amount", "")
    currency = form.get("Currency", "")
    bill_id = form.get("BillId", "")
    payment_id = form.get("PaymentId", "")
    signature = form.get("SignatureValue", "")

    if not settings.cardlink_enabled or not signature:
        return PlainTextResponse("OK")

    if not cardlink_service.verify_refund_signature(
        amount, currency, bill_id, payment_id, refund_id, signature
    ):
        return PlainTextResponse("wrong sign", status_code=400)

    logger.info(
        "Cardlink refund: id=%s payment=%s bill=%s amount=%s status=%s",
        refund_id,
        payment_id,
        bill_id,
        amount,
        form.get("Status"),
    )
    return PlainTextResponse("OK")


@app.api_route("/cardlink/chargeback", methods=["GET", "POST"])
async def cardlink_chargeback(request: Request, session: AsyncSession = Depends(get_db)):
    form = await _cardlink_form_or_query(request)
    chargeback_id = form.get("Id", "")
    bill_id = form.get("BillId", "")
    payment_id = form.get("PaymentId", "")
    signature = form.get("SignatureValue", "")

    if not settings.cardlink_enabled or not signature:
        return PlainTextResponse("OK")

    if not cardlink_service.verify_chargeback_signature(
        bill_id, payment_id, chargeback_id, signature
    ):
        return PlainTextResponse("wrong sign", status_code=400)

    logger.warning(
        "Cardlink chargeback: id=%s payment=%s bill=%s status=%s",
        chargeback_id,
        payment_id,
        bill_id,
        form.get("Status"),
    )
    return PlainTextResponse("OK")


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
    total_referrals = await count_all_referrals(session)
    top_referrers = await list_top_referrers(session, limit=10)

    from bot.database.models import Device

    devices = (await session.execute(select(Device))).scalars().all()
    device_counts: dict[int, int] = {}
    for d in devices:
        device_counts[d.user_id] = device_counts.get(d.user_id, 0) + 1
    active_vpn = len(devices)
    stars_per_day = await get_stars_per_day(session)
    deposit_multiplier = await get_deposit_multiplier(session)
    min_topup = await get_min_topup(session)
    partner_stats = await build_admin_partner_stats(session, users)

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "users": users,
            "total_referrals": total_referrals,
            "top_referrers": top_referrers,
            "daily_price": settings.daily_price_rub,
            "referral_bonus": settings.referral_bonus_rub,
            "stars_per_day": stars_per_day,
            "deposit_multiplier": deposit_multiplier,
            "min_topup": min_topup,
            "allowed_multipliers": ALLOWED_DEPOSIT_MULTIPLIERS,
            "active_vpn": active_vpn,
            "device_counts": device_counts,
            "partner_stats": partner_stats,
        },
    )


@app.get("/admin/users/{user_id}/cabinet", response_class=HTMLResponse)
async def admin_view_user_cabinet(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    user = await get_user_by_id(session, user_id)
    if not user:
        return RedirectResponse("/admin", status_code=303)
    return await _render_cabinet(request, user, session, via_session=False, admin_preview=True)


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
        user=user,
    )
    return RedirectResponse("/admin?credited=1", status_code=303)


@app.post("/admin/users/{user_id}/partner")
async def admin_set_partner(
    request: Request,
    user_id: int,
    enabled: str = Form("0"),
    commission_pct: float = Form(0.0),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    user = await get_user_by_id(session, user_id)
    if not user:
        return RedirectResponse("/admin", status_code=303)

    await set_partner_config(
        session,
        user,
        enabled=enabled in ("1", "true", "on", "yes"),
        commission_pct=commission_pct,
    )
    return RedirectResponse("/admin?partner_saved=1#partners", status_code=303)


@app.post("/admin/users/{user_id}/partner-payout")
async def admin_partner_payout(
    request: Request,
    user_id: int,
    amount: float = Form(...),
    comment: str = Form(""),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    user = await get_user_by_id(session, user_id)
    if not user:
        return RedirectResponse("/admin", status_code=303)

    try:
        await record_partner_payout(session, user, amount, comment or None)
    except ValueError as exc:
        from urllib.parse import quote

        return RedirectResponse(
            f"/admin?partner_error={quote(str(exc)[:120])}#partners",
            status_code=303,
        )
    return RedirectResponse("/admin?partner_paid=1#partners", status_code=303)


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

    user, credited = await approve_payment(session, payment)
    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
        credited=credited,
        user=user,
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
        await notify_payment_rejected(user.telegram_id, user=user)
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


@app.post("/admin/settings/promo")
async def admin_update_promo(
    request: Request,
    deposit_multiplier: float = Form(...),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    await set_deposit_multiplier(session, deposit_multiplier)
    return RedirectResponse("/admin?promo_saved=1#promo", status_code=303)


@app.post("/admin/settings/min-topup")
async def admin_update_min_topup(
    request: Request,
    min_topup_rub: float = Form(...),
    session: AsyncSession = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    await set_min_topup(session, min_topup_rub)
    return RedirectResponse("/admin?min_saved=1#promo", status_code=303)


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
