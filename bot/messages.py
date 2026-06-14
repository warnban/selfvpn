"""Тексты бота — единое место для UX-копирайта."""

AMNEZIA_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
AMNEZIA_WG_APPLE = "https://apps.apple.com/app/amneziawg/id6478942365"
# Старый алиас — Amnezia VPN на iOS (не используем в инструкциях)
AMNEZIA_IOS = AMNEZIA_WG_APPLE
AMNEZIA_SITE = "https://amnezia.org"


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
        f"<b>{brand_name}</b> · на балансе <b>{trial_balance:.0f} ₽</b> (~{trial_days} дн.)\n"
        f"Тариф: <b>{daily_price:.0f} ₽/сутки</b> за устройство\n"
    )
    if referral_ok:
        text += "👥 Пришли по реф-ссылке — спасибо!\n"
    text += (
        "\n<b>Как подключить:</b>\n"
        "1. Открой кабинет → добавь устройство\n"
        "2. Скачай приложение:\n"
        f'   • Android — <a href="{AMNEZIA_ANDROID}">Amnezia VPN</a>\n'
        f'   • iPhone / Mac — <a href="{AMNEZIA_WG_APPLE}">AmneziaWG</a>\n'
        "3. В кабинете:\n"
        "   • Android — вкладка <b>Ключ</b> → скопируй\n"
        "   • iPhone / Mac — вкладка <b>Conf</b> → скачай файл\n"
        "4. В приложении:\n"
        "   • Android: ➕ → «Вставить ключ»\n"
        "   • iPhone / Mac: «Добавить туннель» → «Из файла или архива» → выбери conf\n\n"
        f'🌐 <a href="{cabinet_link}">Личный кабинет</a>'
    )
    return text


def amnezia_setup_steps() -> str:
    return (
        "<b>Как подключить VPN</b>\n\n"
        "<b>Android</b> — <a href=\"{android}\">Amnezia VPN</a>\n"
        "Кабинет → устройство → <b>Ключ</b> → ➕ → «Вставить ключ»\n\n"
        "<b>iPhone / Mac</b> — <a href=\"{apple}\">AmneziaWG</a>\n"
        "Кабинет → устройство → <b>Conf</b> → скачай файл → "
        "«Добавить туннель» → «Из файла или архива»"
    ).format(android=AMNEZIA_ANDROID, apple=AMNEZIA_WG_APPLE)


def device_connect_choice(device_name: str = "") -> str:
    title = f"✅ <b>«{device_name}» готово</b>" if device_name else "✅ <b>Устройство готово</b>"
    return (
        f"{title}\n\n"
        "Android — нажми <b>Ключ</b> (Amnezia VPN)\n"
        "iPhone / Mac — нажми <b>Conf</b> (AmneziaWG)"
    )


def vpn_key_instructions(vpn_link: str, device_name: str = "") -> str:
    title = f"🔑 <b>Ключ для «{device_name}»</b>" if device_name else "🔑 <b>Ключ подключения</b>"
    return (
        f"{title}\n\n"
        f"<code>{vpn_link}</code>\n\n"
        "<b>Amnezia VPN (Android):</b>\n"
        "➕ → «Вставить ключ» → вставь ключ → Подключить\n\n"
        f'<a href="{AMNEZIA_ANDROID}">Скачать Amnezia VPN</a>'
    )


def vpn_conf_instructions(device_name: str = "") -> str:
    title = f"📄 <b>Conf для «{device_name}»</b>" if device_name else "📄 <b>Conf-файл</b>"
    return (
        f"{title}\n\n"
        "<b>AmneziaWG (iPhone / Mac):</b>\n"
        "«Добавить туннель» → «Добавить туннель из файла или архива» → выбери этот .conf\n\n"
        f'<a href="{AMNEZIA_WG_APPLE}">Скачать AmneziaWG</a>'
    )
