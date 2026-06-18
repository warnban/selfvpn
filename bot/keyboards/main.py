from urllib.parse import quote

from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.messages import AMNEZIA_ANDROID, AMNEZIA_WG_APPLE

BTN_CABINET = "🌐 Личный кабинет"
BTN_TOPUP = "⭐ Пополнить"
BTN_INVITE = "👥 Пригласить"
BTN_ABOUT = "ℹ️ О сервисе"
BTN_SUPPORT = "🆘 Поддержка"
BTN_ADMIN = "⚙️ ADM PANEL"
BTN_NEWS = "📢 Новость"

# Старые подписи кнопок — для совместимости с устаревшими клавиатурами
LEGACY_MENU_BUTTONS = frozenset({
    "📱 Мои устройства",
    "💰 Баланс",
    "💳 Пополнить",
    "👥 Рефералы",
    "ℹ️ Помощь",
    "🔐 Подключить",
    "Подключить",
    "🔐 Подключить VPN",
    "Подключить VPN",
})


def main_menu(*, is_admin: bool = False) -> ReplyKeyboardMarkup:
    from bot.config import settings

    rows = [
        [KeyboardButton(text=BTN_CABINET), KeyboardButton(text=BTN_TOPUP)],
        [KeyboardButton(text=BTN_INVITE)],
    ]
    about_url = f"{settings.web_base_url.rstrip('/')}/about"
    if about_url.startswith("https://"):
        rows.append([KeyboardButton(text=BTN_ABOUT, url=about_url)])
    else:
        rows.append([KeyboardButton(text=BTN_ABOUT)])
    support_url = settings.support_tg_url()
    if support_url:
        rows.append([KeyboardButton(text=BTN_SUPPORT, url=support_url)])
    else:
        rows.append([KeyboardButton(text=BTN_SUPPORT)])
    if is_admin:
        rows.append([KeyboardButton(text=BTN_ADMIN), KeyboardButton(text=BTN_NEWS)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def menu_for(telegram_id: int) -> ReplyKeyboardMarkup:
    from bot.config import is_admin

    return main_menu(is_admin=is_admin(telegram_id))


def news_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить всем", callback_data="news_send"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="news_cancel"),
            ]
        ]
    )


def invite_kb(ref_link: str) -> InlineKeyboardMarkup:
    share_url = (
        "https://t.me/share/url?"
        f"url={quote(ref_link, safe='')}"
        f"&text={quote('Стабильный интернет — попробуй', safe='')}"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    copy_text=CopyTextButton(text=ref_link),
                ),
            ],
            [InlineKeyboardButton(text="📤 Поделиться", url=share_url)],
        ]
    )


def app_download_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Android", url=AMNEZIA_ANDROID),
                InlineKeyboardButton(text="🍎 iPhone", url=AMNEZIA_WG_APPLE),
            ],
        ]
    )


def device_created_kb(device_id: int) -> InlineKeyboardMarkup:
    """Показывается после создания устройства: выбор способа подключения."""
    rows = [
        [
            InlineKeyboardButton(text="🔑 Получить ключ", callback_data=f"dev_key:{device_id}"),
            InlineKeyboardButton(text="📄 Скачать файл", callback_data=f"dev_conf:{device_id}"),
        ],
        [
            InlineKeyboardButton(text="📱 Amnezia (Android)", url=AMNEZIA_ANDROID),
            InlineKeyboardButton(text="🍎 AmneziaWG (Apple)", url=AMNEZIA_WG_APPLE),
        ],
        [InlineKeyboardButton(text="➕ Добавить ещё", callback_data="dev_add")],
        [InlineKeyboardButton(text="📱 К моим устройствам", callback_data="dev_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def devices_kb(devices: list) -> InlineKeyboardMarkup:
    """Список устройств: ключ / conf + удаление."""
    rows = []
    for d in devices:
        rows.append(
            [
                InlineKeyboardButton(text=f"🔑 {d.name}", callback_data=f"dev_key:{d.id}"),
                InlineKeyboardButton(text="📄 Файл", callback_data=f"dev_conf:{d.id}"),
            ]
        )
        rows.append([InlineKeyboardButton(text=f"🗑 Удалить «{d.name}»", callback_data=f"dev_del:{d.id}")])
    rows.append([InlineKeyboardButton(text="➕ Добавить устройство", callback_data="dev_add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def platform_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Android", callback_data="dev_new:android"),
                InlineKeyboardButton(text="🍎 iPhone/iPad", callback_data="dev_new:ios"),
            ],
            [
                InlineKeyboardButton(text="🖥 Windows", callback_data="dev_new:windows"),
                InlineKeyboardButton(text="💻 macOS", callback_data="dev_new:mac"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="dev_list")],
        ]
    )


def device_del_confirm_kb(device_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"dev_delok:{device_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="dev_list"),
            ]
        ]
    )


def stars_days_selection_kb(stars_per_day: int) -> InlineKeyboardMarkup:
    from bot.config import settings

    presets = [7, 14, 30, 60, 90]
    rows = []
    row = []
    for days in presets:
        stars = stars_per_day * days
        rub = settings.price_for_days(days)
        row.append(
            InlineKeyboardButton(
                text=f"{days} дн. — {stars} ⭐ ({rub:.0f} ₽)",
                callback_data=f"stars_days:{days}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="stars_days:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def days_selection_kb() -> InlineKeyboardMarkup:
    from bot.config import settings

    presets = [7, 14, 30, 60, 90]
    rows = []
    row = []
    for days in presets:
        price = settings.price_for_days(days)
        row.append(
            InlineKeyboardButton(
                text=f"{days} дн. — {price:.0f} ₽",
                callback_data=f"pay_days:{days}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Другое количество", callback_data="pay_days:custom")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="pay_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"pay_ok:{payment_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"pay_no:{payment_id}"),
            ]
        ]
    )
