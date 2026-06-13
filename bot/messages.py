"""Тексты бота — единое место для UX-копирайта."""

AMNEZIA_ANDROID = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
AMNEZIA_IOS = "https://apps.apple.com/app/amneziavpn/id1600529900"
AMNEZIA_SITE = "https://amnezia.org"


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
