"""Тексты бота — единое место для UX-копирайта."""

AMNEZIA_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
AMNEZIA_WINDOWS = (
    "https://github.com/amnezia-vpn/amnezia-client/releases/download/"
    "4.8.19.0/AmneziaVPN_4.8.19.0_x64.exe"
)
AMNEZIA_WG_APPLE = "https://apps.apple.com/app/amneziawg/id6478942365"
# Старый алиас — ссылка на iOS (в инструкциях используем AmneziaWG)
AMNEZIA_IOS = AMNEZIA_WG_APPLE
AMNEZIA_SITE = "https://amnezia.org"


def app_download_url(platform: str) -> str:
    if platform in ("ios", "mac"):
        return AMNEZIA_WG_APPLE
    if platform == "windows":
        return AMNEZIA_WINDOWS
    return AMNEZIA_ANDROID


def app_download_label(platform: str) -> str:
    if platform in ("ios", "mac"):
        return "Скачать AmneziaWG (App Store)"
    if platform == "windows":
        return "Скачать Amnezia для Windows"
    return "Скачать Amnezia (Google Play)"


def _steps_key_android() -> str:
    return (
        "1️⃣ Установи приложение <a href=\"{android}\">Amnezia</a> из Google Play\n"
        "2️⃣ Нажми кнопку <b>🔑 Ключ</b> ниже и скопируй его\n"
        "3️⃣ Открой Amnezia → значок <b>«+»</b> вверху → «Вставить ключ из буфера»\n"
        "4️⃣ Нажми кнопку подключения — когда загорится «Подключено», всё работает"
    ).format(android=AMNEZIA_ANDROID)


def _steps_key_windows() -> str:
    return (
        "1️⃣ Скачай и установи <a href=\"{win}\">Amnezia для Windows</a> (файл .exe — запусти его)\n"
        "2️⃣ Нажми кнопку <b>🔑 Ключ</b> ниже и скопируй его\n"
        "3️⃣ Открой Amnezia → значок <b>«+»</b> → «Вставить ключ из буфера»\n"
        "4️⃣ Нажми кнопку подключения — когда загорится «Подключено», всё работает"
    ).format(win=AMNEZIA_WINDOWS)


def _steps_conf_apple() -> str:
    return (
        "1️⃣ Установи приложение <a href=\"{apple}\">AmneziaWG</a> из App Store\n"
        "2️⃣ Нажми кнопку <b>📄 Conf-файл</b> ниже — придёт файл .conf, сохрани его\n"
        "3️⃣ Открой AmneziaWG → «Добавить туннель» → «Из файла или архива» → выбери файл\n"
        "4️⃣ Включи переключатель — когда станет «Подключено», всё работает"
    ).format(apple=AMNEZIA_WG_APPLE)


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
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Добро пожаловать в <b>{brand_name}</b> — "
        f"персональный интернет-канал через VPS.\n"
        f"На балансе <b>{trial_balance:.0f} ₽</b> (~{trial_days} дн.)."
    )
    if referral_ok:
        text += "\n👥 Пришли по реф-ссылке — спасибо!"
    text += (
        "\n\n<b>Как подключиться за 3 шага:</b>\n"
        "1️⃣ Открой личный кабинет\n"
        "2️⃣ Добавь своё устройство (Android, iPhone…)\n"
        "3️⃣ Скопируй ключ или скачай файл → вставь в приложение\n\n"
        f"🌐 <a href=\"{cabinet_link}\">Открыть личный кабинет</a>\n\n"
        "<i>При первом входе — короткая настройка подключения, затем кабинет с балансом.</i>"
    )
    return text


def cabinet_intro(cabinet_link: str, *, device_count: int = 0, days_left: int = 0) -> str:
    if device_count == 0:
        body = (
            "Здесь баланс, оплата и настройка подключения.\n\n"
            "<b>С чего начать:</b>\n"
            "1️⃣ Нажми «Добавить устройство» и выбери свою платформу\n"
            "2️⃣ Получи ключ (Android / Windows) или файл .conf (iPhone / Mac)\n"
            "3️⃣ Вставь в приложение Amnezia — готово!\n\n"
            "📱 Android → приложение <b>Amnezia</b>\n"
            "🍎 iPhone / Mac → приложение <b>AmneziaWG</b>"
        )
    else:
        body = (
            f"Устройств: <b>{device_count}</b> · хватит на ~<b>{days_left}</b> дн.\n\n"
            "Чтобы подключить новое — добавь устройство в кабинете "
            "и следуй подсказкам на экране."
        )
    return f"🌐 <b>Личный кабинет</b>\n\n{body}\n\n<a href=\"{cabinet_link}\">{cabinet_link}</a>"


def amnezia_setup_steps() -> str:
    return (
        "<b>📖 Как подключиться</b>\n\n"
        "<b>Android</b>\n"
        f"{_steps_key_android()}\n\n"
        "<b>Windows</b>\n"
        f"{_steps_key_windows()}\n\n"
        "<b>iPhone / iPad / Mac</b>\n"
        f"{_steps_conf_apple()}"
    )


def device_connect_choice(device_name: str = "", platform: str = "") -> str:
    title = f"✅ <b>«{device_name}» готово!</b>" if device_name else "✅ <b>Устройство готово!</b>"
    if platform in ("ios", "mac"):
        steps = _steps_conf_apple()
        hint = "Нажми <b>📄 Conf-файл</b> ниже 👇"
    elif platform == "windows":
        steps = _steps_key_windows()
        hint = "Нажми <b>🔑 Ключ</b> ниже 👇"
    else:
        steps = _steps_key_android()
        hint = "Нажми <b>🔑 Ключ</b> ниже 👇"
    return f"{title}\n\n{hint}\n\n{steps}"


def vpn_key_instructions(vpn_link: str, device_name: str = "", platform: str = "") -> str:
    title = f"🔑 <b>Ключ для «{device_name}»</b>" if device_name else "🔑 <b>Ключ подключения</b>"
    if platform == "windows":
        download = f'<a href="{AMNEZIA_WINDOWS}">🖥 Скачать Amnezia для Windows</a>'
    else:
        download = f'<a href="{AMNEZIA_ANDROID}">📱 Скачать Amnezia (Android)</a>'
    return (
        f"{title}\n\n"
        f"<code>{vpn_link}</code>\n\n"
        "<b>Что делать дальше:</b>\n"
        "1️⃣ Скопируй ключ — просто нажми на него выше\n"
        "2️⃣ Установи и открой приложение <b>Amnezia</b> (ссылка ниже)\n"
        "3️⃣ Значок <b>«+»</b> вверху → «Вставить ключ из буфера»\n"
        "4️⃣ Нажми кнопку подключения — должно стать «Подключено»\n\n"
        f"{download}"
    )


def vpn_conf_instructions(device_name: str = "") -> str:
    title = f"📄 <b>Файл настроек для «{device_name}»</b>" if device_name else "📄 <b>Файл настроек</b>"
    return (
        f"{title}\n\n"
        "<b>Что делать дальше:</b>\n"
        "1️⃣ Сохрани файл .conf (он прикреплён выше)\n"
        "2️⃣ Установи и открой приложение <b>AmneziaWG</b> (ссылка ниже)\n"
        "3️⃣ «Добавить туннель» → «Из файла или архива» → выбери этот файл\n"
        "4️⃣ Включи переключатель — должно стать «Подключено»\n\n"
        f'<a href="{AMNEZIA_WG_APPLE}">🍎 Скачать AmneziaWG (iPhone / Mac)</a>'
    )


def devices_empty_hint() -> str:
    return (
        "У тебя пока нет устройств.\n\n"
        "<b>Как подключиться:</b>\n"
        "1️⃣ Нажми «➕ Добавить устройство»\n"
        "2️⃣ Выбери платформу (Android, iPhone…)\n"
        "3️⃣ Получи ключ или файл и вставь в приложение"
    )
