import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.services.auth import (
    authenticate_web_user,
    change_password,
    register_web_user,
    request_password_reset,
    reset_password,
    verify_user_email,
)
from bot.services.email import send_verification_for_user_id
from bot.services.users import get_user_by_cabinet_token
from web.cabinet_helpers import login_session, logout_session
from web.deps import get_db, templates

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)


def _safe_next_url(next_url: str | None) -> str:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/cabinet"


@router.get("/auth/login", response_class=HTMLResponse)
async def auth_login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/cabinet", status_code=303)
    return templates.TemplateResponse(
        request,
        "auth_login.html",
        {
            "error": request.query_params.get("error"),
            "message": request.query_params.get("msg"),
            "next": request.query_params.get("next", "/cabinet"),
        },
    )


@router.post("/auth/login")
async def auth_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/cabinet"),
    session: AsyncSession = Depends(get_db),
):
    user, err = await authenticate_web_user(session, email, password)
    if err or not user:
        from urllib.parse import quote

        return RedirectResponse(
            f"/auth/login?error={quote(err or 'Ошибка входа')}&next={quote(next)}",
            status_code=303,
        )
    login_session(request, user)
    return RedirectResponse(_safe_next_url(next), status_code=303)


@router.get("/auth/register", response_class=HTMLResponse)
async def auth_register_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/cabinet", status_code=303)
    ref = request.query_params.get("ref")
    ref_id = int(ref) if ref and ref.isdigit() else None
    return templates.TemplateResponse(
        request,
        "auth_register.html",
        {
            "error": request.query_params.get("error"),
            "ref": ref_id,
            "smtp_enabled": settings.smtp_enabled,
        },
    )


@router.post("/auth/register")
async def auth_register_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(""),
    ref: str = Form(""),
    session: AsyncSession = Depends(get_db),
):
    import logging
    from urllib.parse import quote

    logger = logging.getLogger(__name__)

    if not settings.smtp_enabled:
        return RedirectResponse(
            f"/auth/register?error={quote('Регистрация временно недоступна')}",
            status_code=303,
        )

    ref_id = int(ref) if ref.isdigit() else None
    try:
        user, err = await register_web_user(
            session,
            email=email,
            password=password,
            display_name=display_name or None,
            referrer_user_id=ref_id,
        )
    except Exception:
        logger.exception("Registration failed for %s", email)
        return RedirectResponse(
            f"/auth/register?error={quote('Ошибка сервера. Попробуйте позже или напишите в поддержку.')}",
            status_code=303,
        )

    if err or not user:
        qs = f"error={quote(err or 'Ошибка регистрации')}"
        if ref_id:
            qs += f"&ref={ref_id}"
        return RedirectResponse(f"/auth/register?{qs}", status_code=303)

    background_tasks.add_task(send_verification_for_user_id, user.id)

    login_session(request, user)
    return RedirectResponse("/cabinet?verify=sent", status_code=303)


@router.get("/auth/logout")
async def auth_logout(request: Request):
    logout_session(request)
    return RedirectResponse("/", status_code=303)


@router.get("/auth/forgot", response_class=HTMLResponse)
async def auth_forgot_form(request: Request):
    return templates.TemplateResponse(
        request,
        "auth_forgot.html",
        {
            "message": request.query_params.get("msg"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/auth/forgot")
async def auth_forgot_submit(
    request: Request,
    email: str = Form(...),
    session: AsyncSession = Depends(get_db),
):
    if not settings.smtp_enabled:
        return RedirectResponse("/auth/forgot?error=smtp", status_code=303)
    await request_password_reset(session, email)
    return RedirectResponse("/auth/forgot?msg=sent", status_code=303)


@router.get("/auth/reset/{token}", response_class=HTMLResponse)
async def auth_reset_form(request: Request, token: str):
    return templates.TemplateResponse(
        request,
        "auth_reset.html",
        {"token": token, "error": request.query_params.get("error")},
    )


@router.post("/auth/reset/{token}")
async def auth_reset_submit(
    request: Request,
    token: str,
    password: str = Form(...),
    password2: str = Form(...),
    session: AsyncSession = Depends(get_db),
):
    if password != password2:
        return RedirectResponse(f"/auth/reset/{token}?error=mismatch", status_code=303)
    user, err = await reset_password(session, token, password)
    if err or not user:
        from urllib.parse import quote

        return RedirectResponse(f"/auth/reset/{token}?error={quote(err or 'Ошибка')}", status_code=303)
    login_session(request, user)
    return RedirectResponse("/cabinet?msg=password_changed", status_code=303)


@router.get("/auth/verify/{token}")
async def auth_verify(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_db),
):
    user, err = await verify_user_email(session, token)
    if err or not user:
        return templates.TemplateResponse(
            request,
            "auth_message.html",
            {"title": "Ошибка", "message": err or "Не удалось подтвердить email", "success": False},
        )
    login_session(request, user)
    return RedirectResponse("/cabinet?verified=1", status_code=303)


def _safe_cabinet_redirect(next_url: str | None, fallback: str = "/cabinet") -> str:
    if next_url and next_url.startswith("/cabinet") and not next_url.startswith("//"):
        return next_url.split("?")[0]
    return fallback


@router.post("/auth/resend-verification")
async def auth_resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    cabinet_token: str = Form(""),
    next_url: str = Form("/cabinet"),
    session: AsyncSession = Depends(get_db),
):
    from web.cabinet_helpers import get_session_user_id, get_user_from_session

    user = await get_user_from_session(request, session)
    if not user and cabinet_token:
        user = await get_user_by_cabinet_token(session, cabinet_token)
    logger.info(
        "resend-verification: session=%s token=%s user=%s",
        bool(get_session_user_id(request)),
        bool(cabinet_token),
        user.id if user else None,
    )
    if not user or not user.email or user.email_verified:
        target = _safe_cabinet_redirect(next_url)
        return RedirectResponse(target, status_code=303)

    login_session(request, user)
    background_tasks.add_task(send_verification_for_user_id, user.id)
    target = _safe_cabinet_redirect(next_url)
    logger.info("resend-verification: redirect %s (email in background)", target)
    return RedirectResponse(f"{target}?verify=sent", status_code=303)


@router.get("/cabinet/profile", response_class=HTMLResponse)
async def cabinet_profile(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    from bot.services.auth import make_telegram_link_token
    from web.cabinet_helpers import build_cabinet_context, get_user_from_session

    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login?next=/cabinet/profile", status_code=303)

    ctx = await build_cabinet_context(request, user, session, via_session=True)
    ctx.update(
        {
            "message": request.query_params.get("msg"),
            "error": request.query_params.get("error"),
            "telegram_link_token": make_telegram_link_token(user.id) if not user.telegram_id else None,
            "bot_username": "anfikvpnbot",
        }
    )
    return templates.TemplateResponse(request, "profile.html", ctx)


@router.post("/cabinet/profile/password")
async def cabinet_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
    session: AsyncSession = Depends(get_db),
):
    from urllib.parse import quote

    from web.cabinet_helpers import get_user_from_session

    user = await get_user_from_session(request, session)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    if new_password != new_password2:
        return RedirectResponse("/cabinet/profile?error=mismatch", status_code=303)
    err = await change_password(session, user, current_password, new_password)
    if err:
        return RedirectResponse(f"/cabinet/profile?error={quote(err)}", status_code=303)
    return RedirectResponse("/cabinet/profile?msg=password_changed", status_code=303)
