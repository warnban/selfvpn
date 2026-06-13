from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.messages import AMNEZIA_ANDROID, AMNEZIA_IOS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Мои устройства"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="💳 Пополнить"), KeyboardButton(text="🌐 Личный кабинет")],
            [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )


def app_download_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Android", url=AMNEZIA_ANDROID),
                InlineKeyboardButton(text="🍎 iPhone", url=AMNEZIA_IOS),
            ],
        ]
    )


def device_created_kb() -> InlineKeyboardMarkup:
    """Показывается после создания ключа: скачать приложение + продолжить."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Android", url=AMNEZIA_ANDROID),
                InlineKeyboardButton(text="🍎 iPhone", url=AMNEZIA_IOS),
            ],
            [InlineKeyboardButton(text="➕ Добавить ещё", callback_data="dev_add")],
            [InlineKeyboardButton(text="📱 К моим устройствам", callback_data="dev_list")],
        ]
    )


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
