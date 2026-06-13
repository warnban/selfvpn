"""Тексты бота — единое место для UX-копирайта."""

AMNEZIA_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
AMNEZIA_IOS = "https://apps.apple.com/app/amneziavpn/id1600529900"
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
        "1️⃣ Скачай <b>AmneziaVPN</b>:\n"
        f'   • <a href="{AMNEZIA_ANDROID}">Android</a>\n'
        f'   • <a href="{AMNEZIA_IOS}">iPhone</a>\n'
        "2️⃣ В боте: «📱 Мои устройства» → добавь устройство → получишь ключ\n"
        "3️⃣ В Amnezia: ➕ → «Вставить ключ» → Подключить\n\n"
        f"🌐 <b>Личный кабинет</b> (баланс, оплата, ключи):\n"
        f'<a href="{cabinet_link}">{cabinet_link}</a>'
    )
    return text


def amnezia_setup_steps() -> str:
    return (
        "<b>📲 Как подключить VPN</b>\n\n"
        "1️⃣ Скачай приложение <b>AmneziaVPN</b>:\n"
        f'   • <a href="{AMNEZIA_ANDROID}">Android — Play Market</a>\n'
        f'   • <a href="{AMNEZIA_IOS}">iPhone — App Store</a>\n\n'
        "2️⃣ Открой «📱 Мои устройства» → «➕ Добавить устройство» — получишь ключ <code>vpn://...</code>\n\n"
        "3️⃣ В Amnezia: <b>➕ Добавить VPN</b> → "
        "<b>«Вставить ключ / Enter key»</b> → вставь ключ → Подключить\n\n"
        "💡 Сохрани личный кабинет в закладки — там баланс и ключ, если Telegram недоступен."
    )


def vpn_key_instructions(vpn_link: str, device_name: str = "") -> str:
    title = f"✅ <b>Устройство «{device_name}» готово!</b>" if device_name else "✅ <b>VPN готов!</b>"
    return (
        f"{title}\n\n"
        "<b>Ключ</b> (нажми, чтобы скопировать):\n"
        f"<code>{vpn_link}</code>\n\n"
        "<b>Дальше в приложении Amnezia:</b>\n"
        "1. Открой AmneziaVPN\n"
        "2. ➕ → «Вставить ключ» / «Enter key»\n"
        "3. Вставь ключ из сообщения выше\n"
        "4. Нажми «Подключить»\n\n"
        "⚠️ Один ключ — для одного устройства. Для другого телефона/ПК добавь ещё устройство.\n\n"
        f'Нет приложения? '
        f'<a href="{AMNEZIA_ANDROID}">Android</a> · '
        f'<a href="{AMNEZIA_IOS}">iOS</a>'
    )
