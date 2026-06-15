import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from bot.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    if not settings.smtp_enabled:
        logger.warning("SMTP не настроен — письмо не отправлено: %s", subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_address
    msg["To"] = to

    plain = text_body or _html_to_plain(html_body)
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.smtp_use_ssl:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=True,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
        return True
    except Exception as exc:
        logger.exception("Ошибка отправки email на %s: %s", to, exc)
        return False


def _html_to_plain(html: str) -> str:
    import re

    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _email_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru"><body style="font-family:sans-serif;background:#0d0f12;color:#e8eaed;padding:24px">
<div style="max-width:480px;margin:0 auto;background:#151820;border-radius:12px;padding:24px">
<h1 style="color:#39e87a;font-size:20px;margin:0 0 16px">{title}</h1>
{body}
<p style="color:#6b7280;font-size:12px;margin-top:24px">{settings.brand_name}</p>
</div></body></html>"""


async def send_verification_email(to: str, verify_url: str) -> bool:
    body = (
        f'<p style="color:#aaa">Подтвердите email, чтобы пользоваться личным кабинетом.</p>'
        f'<p><a href="{verify_url}" style="display:inline-block;background:#39e87a;color:#0a1a10;'
        f'padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">'
        f"Подтвердить email</a></p>"
        f'<p style="color:#666;font-size:13px">Ссылка действует 3 дня.</p>'
    )
    return await send_email(to, f"Подтвердите email — {settings.brand_name}", _email_shell("Подтверждение email", body))


async def send_password_reset_email(to: str, reset_url: str) -> bool:
    body = (
        f'<p style="color:#aaa">Запрошен сброс пароля. Если это не вы — проигнорируйте письмо.</p>'
        f'<p><a href="{reset_url}" style="display:inline-block;background:#39e87a;color:#0a1a10;'
        f'padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">'
        f"Сбросить пароль</a></p>"
        f'<p style="color:#666;font-size:13px">Ссылка действует 1 час.</p>'
    )
    return await send_email(to, f"Сброс пароля — {settings.brand_name}", _email_shell("Сброс пароля", body))


async def send_notification_email(to: str, subject: str, message: str) -> bool:
    body = f'<p style="color:#ccc;white-space:pre-line">{message}</p>'
    return await send_email(to, f"{subject} — {settings.brand_name}", _email_shell(subject, body))
