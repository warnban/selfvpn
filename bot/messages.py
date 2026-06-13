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


def amneziawg_import_steps(platform: str = "") -> str:
    if platform == "android":
        return (
            "<b>📱 Android — так проще всего:</b>\n"
            "1. Нажми кнопку <b>«🌐 Скачать через браузер»</b> ниже\n"
            "2. Файл сохранится в папку <b>Загрузки</b> на телефоне\n"
            "3. AmneziaWG → ➕ → «Импорт из файла» → <b>Загрузки</b> → "
            "<code>daddyvpn_….conf</code>\n\n"
            "⚠️ Файл <i>из Telegram</i> часто лежит в подпапке "
            "<b>Загрузки/Telegram</b> — AmneziaWG её не показывает. "
            "Поэтому лучше скачивать через браузер."
        )
    if platform in ("ios", "mac"):
        return (
            "1. Нажми «🌐 Скачать через браузер» или открой файл из Telegram\n"
            "2. Сохрани <code>.conf</code> в «Файлы» / Files\n"
            "3. AmneziaWG → ➕ → «Import from file» → выбери файл\n"
            "4. Подключись к VPN"
        )
    return (
        "1. Установи <b>AmneziaWG</b> (ссылки ниже)\n"
        "2. Скачай <code>.conf</code> через кнопку «🌐 Скачать через браузер»\n"
        "3. AmneziaWG → ➕ → «Импорт из файла» → выбери файл\n"
        "4. Подключись к VPN"
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


def vpn_key_instructions(device_name: str = "", platform: str = "") -> str:
    title = f"✅ <b>Устройство «{device_name}» готово!</b>" if device_name else "✅ <b>VPN готов!</b>"
    return (
        f"{title}\n\n"
        "📎 Файл <code>.conf</code> — вложение выше.\n"
        "На Android надёжнее скачать через кнопку <b>«🌐 Скачать через браузер»</b>.\n\n"
        f"{amneziawg_import_steps(platform)}\n\n"
        "⚠️ Один файл — для одного устройства.\n\n"
        f"Нет приложения? {app_download_links_short_html()}"
    )
