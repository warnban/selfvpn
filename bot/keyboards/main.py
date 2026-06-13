from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.config import settings
from bot.messages import AMNEZIAWG_ANDROID, AMNEZIAWG_APPLE, AMNEZIAWG_WINDOWS


def main_menu(*, is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="📱 Мои устройства"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="💳 Пополнить"), KeyboardButton(text="🌐 Личный кабинет")],
        [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="ℹ️ Помощь")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="⚙️ ADM PANEL"), KeyboardButton(text="📢 Новость")])
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


def _app_download_rows() -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(text="📱 Android", url=AMNEZIAWG_ANDROID),
            InlineKeyboardButton(text="🍎 iPhone/iPad", url=AMNEZIAWG_APPLE),
        ],
        [
            InlineKeyboardButton(text="🖥 Windows", url=AMNEZIAWG_WINDOWS),
            InlineKeyboardButton(text="💻 macOS", url=AMNEZIAWG_APPLE),
        ],
    ]


def app_download_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_app_download_rows())


def device_conf_kb(cabinet_token: str, device_id: int) -> InlineKeyboardMarkup:
    """Кнопки после выдачи .conf: браузер + скачать AmneziaWG."""
    conf_url = settings.conf_download_url(cabinet_token, device_id)
    rows = [[InlineKeyboardButton(text="🌐 Скачать через браузер", url=conf_url)]]
    rows.extend(_app_download_rows())
    rows.append([InlineKeyboardButton(text="➕ Добавить ещё", callback_data="dev_add")])
    rows.append([InlineKeyboardButton(text="📱 К моим устройствам", callback_data="dev_list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def device_conf_resend_kb(cabinet_token: str, device_id: int) -> InlineKeyboardMarkup:
    conf_url = settings.conf_download_url(cabinet_token, device_id)
    rows = [[InlineKeyboardButton(text="🌐 Скачать через браузер", url=conf_url)]]
    rows.extend(_app_download_rows())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def device_created_kb(cabinet_token: str, device_id: int) -> InlineKeyboardMarkup:
    return device_conf_kb(cabinet_token, device_id)


def devices_kb(devices: list) -> InlineKeyboardMarkup:
    """Список устройств: кнопка показа ключа + удаление."""
    rows = []
    for d in devices:
        rows.append([InlineKeyboardButton(text=f"🔑 {d.name}", callback_data=f"dev_key:{d.id}")])
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
