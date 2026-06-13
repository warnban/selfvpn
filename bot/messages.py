"""Тексты бота — единое место для UX-копирайта."""

AMNEZIAWG_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.awg"
AMNEZIAWG_APPLE = "https://apps.apple.com/app/amneziawg/id6478942365"
AMNEZIAWG_WINDOWS = "https://github.com/amnezia-vpn/amneziawg-windows-client/releases/latest"
AMNEZIAWG_SITE = "https://amnezia.org"


def app_download_links_html() -> str:
    return (
        f'   • <a href="{AMNEZIAWG_ANDROID}">Android</a>\n'
        f'   • <a href="{AMNEZIAWG_APPLE}">iPhone / iPad</a>\n'
        f'   • <a href="{AMNEZIAWG_APPLE}">macOS</a> (App Store)\n'
        f'   • <a href="{AMNEZIAWG_WINDOWS}">Windows</a>'
    )


def app_download_links_short_html() -> str:
    return (
        f'<a href="{AMNEZIAWG_ANDROID}">Android</a> · '
        f'<a href="{AMNEZIAWG_APPLE}">iPhone/iPad</a> · '
        f'<a href="{AMNEZIAWG_APPLE}">macOS</a> · '
        f'<a href="{AMNEZIAWG_WINDOWS}">Windows</a>'
    )


def amneziawg_import_steps() -> str:
    return (
        "1. Установи <b>AmneziaWG</b> (ссылки ниже)\n"
        "2. Открой приложение → нажми <b>➕</b>\n"
        "3. Выбери <b>«Импорт из файла»</b> / «Import from file»\n"
        "4. Укажи полученный файл <code>.conf</code>\n"
        "5. Подключись к VPN"
    )


def new_user_welcome(
    name: str,
    brand_name: str,
    cabinet_link: str,
    *,
    trial_days: int,
    trial_balance: float,
    daily_price: float,
    referral_ok: bool = False,
) -> str:
    text = (
        f"👋 Привет, <b>{name}</b>!\n"
        f"Добро пожаловать в <b>{brand_name}</b>.\n\n"
        f"🛡 <b>Что это:</b> быстрый VPN для телефона и компьютера. "
        f"Платишь только за дни, когда пользуешься — без подписок и лишних кнопок.\n\n"
        f"🎁 Пробный доступ: <b>{trial_days} дня</b> ({trial_balance:.0f} ₽ на балансе)\n"
        f"📅 Тариф: <b>{daily_price:.0f} ₽/сутки</b> за каждое устройство\n"
    )
    if referral_ok:
        text += "👥 Реферальная ссылка сработала — спасибо!\n"
    text += (
        "\n<b>📲 Как подключить:</b>\n"
        "1️⃣ Скачай <b>AmneziaWG</b>:\n"
        f"{app_download_links_html()}\n"
        "2️⃣ В боте: «📱 Мои устройства» → добавь устройство → получишь файл <code>.conf</code>\n"
        f"3️⃣ {amneziawg_import_steps()}\n\n"
        f"🌐 <b>Личный кабинет</b> (баланс, оплата, ключи):\n"
        f'<a href="{cabinet_link}">{cabinet_link}</a>'
    )
    return text


def amnezia_setup_steps() -> str:
    return (
        "<b>📲 Как подключить VPN</b>\n\n"
        "1️⃣ Скачай приложение <b>AmneziaWG</b>:\n"
        f"{app_download_links_html()}\n\n"
        "2️⃣ Открой «📱 Мои устройства» → «➕ Добавить устройство» — получишь файл <code>.conf</code>\n\n"
        f"3️⃣ {amneziawg_import_steps()}\n\n"
        "💡 Сохрани личный кабинет в закладки — там баланс и ключи, если Telegram недоступен."
    )


def vpn_key_instructions(device_name: str = "") -> str:
    title = f"✅ <b>Устройство «{device_name}» готово!</b>" if device_name else "✅ <b>VPN готов!</b>"
    return (
        f"{title}\n\n"
        "📎 Файл конфигурации <b>.conf</b> — в этом сообщении.\n\n"
        "<b>Как подключить в AmneziaWG:</b>\n"
        f"{amneziawg_import_steps()}\n\n"
        "⚠️ Один файл — для одного устройства. Для другого телефона/ПК добавь ещё устройство.\n\n"
        f"Нет приложения? {app_download_links_short_html()}"
    )
