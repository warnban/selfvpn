from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, User
from bot.keyboards.main import admin_payment_kb, days_selection_kb, menu_for
from bot.services.notify import notify_payment_approved, notify_payment_rejected
from bot.services.users import approve_payment, create_payment_request, get_user_by_telegram_id, reject_payment

router = Router()


class TopUpStates(StatesGroup):
    waiting_custom_days = State()
    waiting_screenshot = State()


def payment_details_text(amount: float, days: int) -> str:
    return (
        f"📦 Вы выбрали: <b>{days} дн.</b>\n"
        f"💰 К оплате: <b>{amount:.0f} ₽</b>\n"
        f"({settings.daily_price_rub:.0f} ₽ × {days} дн.)\n\n"
        f"Реквизиты для перевода:\n"
        f"💳 <code>{settings.payment_card}</code>\n"
        f"🏦 {settings.payment_bank}\n"
        f"👤 {settings.payment_holder}\n\n"
        f"После перевода отправь <b>скриншот чека</b> сюда."
    )


@router.message(F.text == "💳 Пополнить")
async def topup_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Выбери, на сколько дней хочешь пополнить баланс.\n"
        f"Тариф: {settings.daily_price_rub:.0f} ₽/сутки.",
        reply_markup=days_selection_kb(),
    )


@router.callback_query(F.data == "pay_cancel")
async def pay_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Пополнение отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("pay_days:"))
async def pay_select_days(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":")[1]
    if value == "custom":
        await state.set_state(TopUpStates.waiting_custom_days)
        await callback.message.edit_text("Введи количество дней (число), например: 15")
        await callback.answer()
        return

    days = int(value)
    amount = settings.price_for_days(days)
    await state.update_data(days=days, amount=amount)
    await state.set_state(TopUpStates.waiting_screenshot)
    await callback.message.edit_text(payment_details_text(amount, days), parse_mode="HTML")
    await callback.answer()


@router.message(TopUpStates.waiting_custom_days)
async def pay_custom_days(message: Message, state: FSMContext) -> None:
    try:
        days = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Введи целое число дней, например: 15")
        return

    if days < 1:
        await message.answer("Минимум 1 день")
        return
    if days > 365:
        await message.answer("Максимум 365 дней за раз")
        return

    amount = settings.price_for_days(days)
    await state.update_data(days=days, amount=amount)
    await state.set_state(TopUpStates.waiting_screenshot)
    await message.answer(payment_details_text(amount, days), parse_mode="HTML")


@router.message(TopUpStates.waiting_screenshot, F.photo)
async def topup_screenshot(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        await state.clear()
        return

    data = await state.get_data()
    amount = float(data["amount"])
    days = int(data["days"])
    photo = message.photo[-1]

    payment = await create_payment_request(
        session,
        user,
        amount,
        days,
        screenshot_file_id=photo.file_id,
    )
    await state.clear()

    await message.answer(
        "✅ Заявка отправлена администратору.\n"
        "После проверки баланс будет пополнен.",
        reply_markup=menu_for(message.from_user.id),
    )

    admin_text = (
        f"💳 Заявка #{payment.id}\n"
        f"Источник: Telegram\n"
        f"Пользователь: {message.from_user.id} (@{message.from_user.username or '-'})\n"
        f"Пакет: {days} дн.\n"
        f"Сумма: {amount:.0f} ₽"
    )
    for admin_id in settings.admin_id_list:
        try:
            await bot.send_photo(
                admin_id,
                photo.file_id,
                caption=admin_text,
                reply_markup=admin_payment_kb(payment.id),
            )
        except Exception:
            pass


@router.message(TopUpStates.waiting_screenshot)
async def topup_need_photo(message: Message) -> None:
    await message.answer("Отправь скриншот перевода как фото (не файлом).")


@router.callback_query(F.data.startswith("pay_ok:"))
async def admin_approve_payment(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await session.get(Payment, payment_id)
    if not payment or payment.status != PaymentStatus.PENDING.value:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    user = await approve_payment(session, payment)
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ ОДОБРЕНО",
        reply_markup=None,
    )
    await callback.answer("Одобрено")

    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
    )


@router.callback_query(F.data.startswith("pay_no:"))
async def admin_reject_payment(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await session.get(Payment, payment_id)
    if not payment or payment.status != PaymentStatus.PENDING.value:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    await reject_payment(session, payment, "Отклонено администратором")
    user = await session.get(User, payment.user_id)

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ ОТКЛОНЕНО",
        reply_markup=None,
    )
    await callback.answer("Отклонено")

    if user:
        await notify_payment_rejected(user.telegram_id)


@router.message(Command("admin"))
async def admin_stats(message: Message, session: AsyncSession) -> None:
    if message.from_user.id not in settings.admin_id_list:
        return

    users = (await session.execute(select(User))).scalars().all()
    pending = (
        await session.execute(select(Payment).where(Payment.status == PaymentStatus.PENDING.value))
    ).scalars().all()

    await message.answer(
        f"📊 Статистика\n\n"
        f"Пользователей: {len(users)}\n"
        f"Активных VPN: {sum(1 for u in users if u.vpn_active)}\n"
        f"Заявок на оплату: {len(pending)}\n\n"
        f"🌐 Админ-панель:\n{settings.web_base_url.rstrip('/')}/admin\n\n"
        f"Тариф: {settings.daily_price_rub:.0f} ₽/сутки\n"
        f"Пробный период: {settings.trial_days} дня"
    )
