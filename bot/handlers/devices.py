from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main import (
    app_download_kb,
    device_created_kb,
    device_del_confirm_kb,
    devices_kb,
    platform_choice_kb,
)
from bot.messages import device_connect_choice, devices_empty_hint, vpn_conf_instructions, vpn_key_instructions
from bot.services.devices import (
    add_device,
    days_left_for,
    get_device,
    get_device_config,
    list_devices,
    platform_label,
    public_vpn_link_for_device,
    remove_device,
    user_daily_cost,
)
from bot.services.vpn_config import safe_conf_filename
from bot.services.users import get_user_by_telegram_id

router = Router()


async def _safe_edit(message, text: str, reply_markup=None) -> None:
    """Редактирует сообщение, не падая на 'message is not modified' и старых сообщениях."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        try:
            await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            pass


async def _devices_overview(session: AsyncSession, user) -> str:
    devices = await list_devices(session, user)
    cost = await user_daily_cost(session, user)
    left = await days_left_for(session, user)

    text = (
        "📱 <b>Мои устройства</b>\n\n"
        f"💰 Баланс: <b>{user.balance_rub:.0f} ₽</b>\n"
        f"📅 Тариф: <b>{settings.daily_price_rub:.0f} ₽/сутки</b> "
        f"(до {settings.max_devices} устройств)\n"
        f"🔢 Устройств: <b>{len(devices)}</b> из {settings.max_devices}\n"
        f"💸 Списание: <b>{cost:.0f} ₽/сутки</b>\n"
        f"⏳ Хватит на: <b>~{left} дн.</b>\n\n"
    )
    if devices:
        text += "Список:\n"
        for d in devices:
            text += f"• {platform_label(d.platform)} — {d.name}\n"
    else:
        text += devices_empty_hint()
    return text


async def _show_devices(message_or_cb, session: AsyncSession, user, edit: bool = False) -> None:
    text = await _devices_overview(session, user)
    devices = await list_devices(session, user)
    kb = devices_kb(devices)
    if edit and isinstance(message_or_cb, CallbackQuery):
        await _safe_edit(message_or_cb.message, text, kb)
    else:
        target = message_or_cb.message if isinstance(message_or_cb, CallbackQuery) else message_or_cb
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "📱 Мои устройства")
async def my_devices(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return
    await _show_devices(message, session, user)


@router.callback_query(F.data == "dev_list")
async def cb_device_list(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return
    await _show_devices(callback, session, user, edit=True)
    await callback.answer()


@router.callback_query(F.data == "dev_add")
async def cb_device_add(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    devices = await list_devices(session, user)
    if len(devices) >= settings.max_devices:
        await callback.answer(f"Лимит {settings.max_devices} устройств", show_alert=True)
        return

    await _safe_edit(
        callback.message,
        "Выбери платформу нового устройства.\n\n"
        f"Тариф остаётся <b>{settings.daily_price_rub:.0f} ₽/сутки</b> "
        f"— до {settings.max_devices} устройств в одном аккаунте.",
        platform_choice_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dev_new:"))
async def cb_device_create(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    platform = callback.data.split(":")[1]
    await callback.answer()
    await _safe_edit(callback.message, "⏳ Создаю устройство на сервере...")

    try:
        device = await add_device(session, user, platform)
    except Exception as exc:
        err = str(exc).strip() or type(exc).__name__
        await _safe_edit(
            callback.message,
            f"❌ Не удалось добавить устройство:\n<code>{err}</code>",
            platform_choice_kb(),
        )
        return

    await _safe_edit(
        callback.message,
        device_connect_choice(device.name, device.platform),
        device_created_kb(device.id),
    )


@router.callback_query(F.data.startswith("dev_key:"))
async def cb_device_key(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    device_id = int(callback.data.split(":")[1])
    device = await get_device(session, user, device_id)
    if not device:
        await callback.answer("Устройство не найдено", show_alert=True)
        return

    await callback.message.answer(
        vpn_key_instructions(public_vpn_link_for_device(device), device.name, device.platform),
        reply_markup=app_download_kb(device.platform),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dev_conf:"))
async def cb_device_conf(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    device_id = int(callback.data.split(":")[1])
    device = await get_device(session, user, device_id)
    if not device:
        await callback.answer("Устройство не найдено", show_alert=True)
        return

    config = get_device_config(device)
    if not config:
        await callback.answer("Conf-файл недоступен для этого устройства", show_alert=True)
        return

    filename = safe_conf_filename(device.name, device.id)
    await callback.message.answer_document(
        BufferedInputFile(config.encode("utf-8"), filename=filename),
        caption=vpn_conf_instructions(device.name),
        reply_markup=app_download_kb(device.platform),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dev_del:"))
async def cb_device_del(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    device_id = int(callback.data.split(":")[1])
    device = await get_device(session, user, device_id)
    if not device:
        await callback.answer("Устройство не найдено", show_alert=True)
        return

    devices = await list_devices(session, user)
    del_hint = (
        f"После удаления последнего устройства списание прекратится "
        f"({settings.daily_price_rub:.0f} ₽/сутки)."
        if len(devices) == 1
        else f"Тариф не изменится — до {settings.max_devices} устройств по одной цене."
    )

    await _safe_edit(
        callback.message,
        f"Удалить устройство «{device.name}»?\n\n"
        f"Ключ перестанет работать. {del_hint}",
        device_del_confirm_kb(device_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dev_delok:"))
async def cb_device_del_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    device_id = int(callback.data.split(":")[1])
    ok = await remove_device(session, user, device_id)
    await callback.answer("Удалено" if ok else "Не найдено")
    await _show_devices(callback, session, user, edit=True)
