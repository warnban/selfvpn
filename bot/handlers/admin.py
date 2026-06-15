import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import is_admin, settings
from bot.keyboards.main import (
    BTN_ABOUT,
    BTN_ADMIN,
    BTN_CABINET,
    BTN_INVITE,
    BTN_NEWS,
    BTN_SUPPORT,
    LEGACY_MENU_BUTTONS,
    menu_for,
    news_confirm_kb,
)
from bot.services.users import list_all_users

router = Router()
logger = logging.getLogger(__name__)


class AdminNewsStates(StatesGroup):
    waiting_text = State()


@router.message(F.text.in_({BTN_ADMIN, "ADM PANEL"}))
async def admin_panel_link(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    url = settings.admin_url()
    await message.answer(
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"<a href=\"{url}\">{url}</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text.in_({BTN_NEWS, "Новость"}))
async def admin_news_start(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminNewsStates.waiting_text)
    await message.answer(
        "📢 <b>Рассылка новости</b>\n\n"
        "Напиши текст — его получат все пользователи бота.\n"
        "Поддерживается HTML: <b>жирный</b>, <i>курсив</i>.\n\n"
        "Отмена: /cancel",
        parse_mode="HTML",
    )


@router.message(Command("cancel"), AdminNewsStates.waiting_text)
async def admin_news_cancel_cmd(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer("Рассылка отменена.", reply_markup=menu_for(message.from_user.id))


@router.message(AdminNewsStates.waiting_text, F.text)
async def admin_news_preview(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    menu_buttons = {BTN_ADMIN, "ADM PANEL", BTN_NEWS, "Новость", BTN_CABINET, BTN_INVITE, BTN_ABOUT, BTN_SUPPORT}
    menu_buttons |= LEGACY_MENU_BUTTONS
    if text in menu_buttons:
        await message.answer("Это кнопка меню, а не текст новости. Напиши новость или /cancel")
        return

    if not text:
        await message.answer("Текст пустой. Напиши новость или /cancel")
        return

    await state.update_data(news_text=text)
    users = await list_all_users(session)
    await message.answer(
        f"📢 <b>Предпросмотр</b> (так увидят пользователи):\n\n"
        f"📢 <b>Новость</b>\n\n{text}\n\n"
        f"Получателей: <b>{len(users)}</b>\n"
        "Отправить?",
        reply_markup=news_confirm_kb(),
        parse_mode="HTML",
    )


@router.message(AdminNewsStates.waiting_text)
async def admin_news_need_text(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer("Отправь текст новости или /cancel для отмены.")


@router.callback_query(F.data == "news_cancel")
async def admin_news_cancel_cb(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()
    await callback.message.answer("Меню:", reply_markup=menu_for(callback.from_user.id))


@router.callback_query(F.data == "news_send")
async def admin_news_send(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    text = data.get("news_text")
    if not text:
        await callback.answer("Текст не найден, начни заново", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ Отправляю новость...")
    await callback.answer()

    users = await list_all_users(session)
    body = f"📢 <b>Новость</b>\n\n{text}"
    sent = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(user.telegram_id, body)
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning("Рассылка: не доставлено %s: %s", user.telegram_id, exc)
        await asyncio.sleep(0.05)

    await state.clear()
    await callback.message.answer(
        f"✅ Рассылка завершена.\n"
        f"Доставлено: <b>{sent}</b>\n"
        f"Не доставлено: <b>{failed}</b>",
        reply_markup=menu_for(callback.from_user.id),
        parse_mode="HTML",
    )
