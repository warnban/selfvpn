"""Тексты бота — единое место для UX-копирайта."""

AMNEZIA_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
AMNEZIA_WG_APPLE = "https://apps.apple.com/app/amneziawg/id6478942365"
# Старый алиас — ссылка на iOS (в инструкциях используем AmneziaWG)
AMNEZIA_IOS = AMNEZIA_WG_APPLE
AMNEZIA_SITE = "https://amnezia.org"


def _steps_key_android() -> str:
    return (
        "1️⃣ Скачай <a href=\"{android}\">Amnezia</a> из Google Play\n"
        "2️⃣ Нажми кнопку <b>Ключ</b> ниже и скопируй его\n"
        "3️⃣ В Amnezia: ➕ → «Вставить ключ» → вставь → <b>Подключить</b>"
    ).format(android=AMNEZIA_ANDROID)


def _steps_conf_apple() -> str:
    return (
        "1️⃣ Скачай <a href=\"{apple}\">AmneziaWG</a> из App Store\n"
        "2️⃣ Нажми кнопку <b>Conf-файл</b> ниже — придёт файл .conf\n"
        "3️⃣ В AmneziaWG: «Добавить туннель» → «Из файла или архива» → выбери файл"
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
        "<b>Android / Windows</b>\n"
        f"{_steps_key_android()}\n\n"
        "<b>iPhone / iPad / Mac</b>\n"
        f"{_steps_conf_apple()}"
    )


def device_connect_choice(device_name: str = "", platform: str = "") -> str:
    title = f"✅ <b>«{device_name}» готово!</b>" if device_name else "✅ <b>Устройство готово!</b>"
    if platform in ("ios", "mac"):
        steps = _steps_conf_apple()
        hint = "Нажми <b>📄 Conf-файл</b> ниже 👇"
    else:
        steps = _steps_key_android()
        hint = "Нажми <b>🔑 Ключ</b> ниже 👇"
    return f"{title}\n\n{hint}\n\n{steps}"


def vpn_key_instructions(vpn_link: str, device_name: str = "") -> str:
    title = f"🔑 <b>Ключ для «{device_name}»</b>" if device_name else "🔑 <b>Ключ подключения</b>"
    return (
        f"{title}\n\n"
        f"<code>{vpn_link}</code>\n\n"
        "<b>Что делать дальше:</b>\n"
        "1️⃣ Скопируй ключ (нажми на него)\n"
        "2️⃣ Открой приложение <b>Amnezia</b>\n"
        "3️⃣ ➕ → «Вставить ключ» → вставь → <b>Подключить</b>\n\n"
        f'<a href="{AMNEZIA_ANDROID}">📱 Скачать Amnezia (Android)</a>'
    )


def vpn_conf_instructions(device_name: str = "") -> str:
    title = f"📄 <b>Файл настроек для «{device_name}»</b>" if device_name else "📄 <b>Файл настроек</b>"
    return (
        f"{title}\n\n"
        "<b>Что делать дальше:</b>\n"
        "1️⃣ Сохрани файл .conf (он прикреплён выше)\n"
        "2️⃣ Открой приложение <b>AmneziaWG</b>\n"
        "3️⃣ «Добавить туннель» → «Из файла или архива» → выбери этот файл\n\n"
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
