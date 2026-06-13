from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, User
from bot.keyboards.main import admin_payment_kb
from bot.services.notify import notify_payment_approved, notify_payment_rejected
from bot.services.users import approve_payment, get_user_by_telegram_id, reject_payment

router = Router()


@router.message(F.text == "💳 Пополнить")
async def topup_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    pay_link = settings.cabinet_pay_url(user.cabinet_token)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить в кабинете", url=pay_link)],
        ]
    )
    await message.answer(
        "💳 <b>Пополнение баланса</b>\n\n"
        "Пополнить баланс нужно в <b>личном кабинете</b> — там выбираешь срок и оплачиваешь картой.\n\n"
        f"<a href=\"{pay_link}\">{pay_link}</a>",
        reply_markup=kb,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


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
