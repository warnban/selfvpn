import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Payment, PaymentStatus, User
from bot.keyboards.main import stars_days_selection_kb
from bot.services.app_settings import (
    get_deposit_multiplier,
    get_min_topup,
    get_stars_per_day,
    stars_for_days,
)
from bot.services.notify import notify_payment_approved, notify_payment_rejected
from bot.services.users import (
    approve_payment,
    cancel_pending_stars_for_user,
    create_payment_request,
    finalize_stars_payment,
    get_user_by_telegram_id,
    reject_payment,
)

logger = logging.getLogger(__name__)
router = Router()

STARS_PAYLOAD_PREFIX = "stars:"


def _parse_stars_payload(payload: str) -> int | None:
    if not payload.startswith(STARS_PAYLOAD_PREFIX):
        return None
    try:
        return int(payload.removeprefix(STARS_PAYLOAD_PREFIX))
    except ValueError:
        return None


async def _send_stars_invoice(message: Message, session: AsyncSession, user: User, days: int) -> None:
    if days < 1 or days > 365:
        await message.answer("Выбери срок от 1 до 365 дней.")
        return

    stars = await stars_for_days(session, days)
    amount_rub = settings.price_for_days(days)

    min_topup = await get_min_topup(session)
    if amount_rub < min_topup:
        min_days = max(1, -(-int(min_topup) // int(settings.daily_price_rub))) if settings.daily_price_rub else 1
        await message.answer(
            f"Минимальная сумма пополнения — <b>{min_topup:.0f} ₽</b>.\n"
            f"Выбери срок от <b>{min_days} дн.</b> и больше.",
            parse_mode="HTML",
        )
        return
    await cancel_pending_stars_for_user(session, user)
    payment = await create_payment_request(
        session,
        user,
        amount_rub,
        days,
        source="stars",
        stars_amount=stars,
    )

    await message.answer_invoice(
        title=f"{settings.brand_name} — {days} дн.",
        description=(
            f"Пополнение баланса на {amount_rub:.0f} ₽ "
            f"({settings.daily_price_rub:.0f} ₽/сутки × {days} дн.)"
        ),
        payload=f"{STARS_PAYLOAD_PREFIX}{payment.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{days} дн. сервиса", amount=stars)],
    )


@router.message(F.text == "⭐ Пополнить")
async def stars_topup_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not settings.stars_enabled:
        await message.answer("Оплата Stars временно недоступна.")
        return

    await state.clear()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    stars_day = await get_stars_per_day(session)
    multiplier = await get_deposit_multiplier(session)
    pay_link = settings.cabinet_pay_url(user.cabinet_token)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить картой в кабинете", url=pay_link)],
        ]
    )
    promo_line = ""
    if multiplier > 1:
        promo_line = (
            f"🎉 <b>Акция ×{multiplier:g}!</b> Баланс пополнится в {multiplier:g} раза больше "
            "оплаченной суммы.\n\n"
        )
    await message.answer(
        "⭐ <b>Пополнение через Telegram Stars</b>\n\n"
        f"{promo_line}"
        f"Тариф: <b>{settings.daily_price_rub:.0f} ₽/сутки</b> "
        f"(до {settings.max_devices} устр., ≈ <b>{stars_day} ⭐/сутки</b>)\n\n"
        "Выбери срок — придёт счёт на оплату Stars прямо в Telegram.",
        reply_markup=stars_days_selection_kb(stars_day),
        parse_mode="HTML",
    )
    await message.answer(
        "Или оплати картой в личном кабинете:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("stars_days:"))
async def stars_days_chosen(callback: CallbackQuery, session: AsyncSession) -> None:
    if not settings.stars_enabled:
        await callback.answer("Stars недоступны", show_alert=True)
        return

    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return

    raw = callback.data.split(":", 1)[1]
    if raw == "cancel":
        await callback.message.delete()
        await callback.answer()
        return

    try:
        days = int(raw)
    except ValueError:
        await callback.answer("Некорректный срок", show_alert=True)
        return

    await callback.answer()
    await _send_stars_invoice(callback.message, session, user, days)


@router.pre_checkout_query()
async def stars_pre_checkout(query: PreCheckoutQuery, session: AsyncSession) -> None:
    if query.currency != "XTR":
        await query.answer(ok=False, error_message="Поддерживается только оплата Stars (XTR).")
        return

    payment_id = _parse_stars_payload(query.invoice_payload)
    if not payment_id:
        await query.answer(ok=False, error_message="Некорректный счёт.")
        return

    payment = await session.get(Payment, payment_id)
    if not payment or payment.source != "stars" or payment.status != PaymentStatus.PENDING.value:
        await query.answer(ok=False, error_message="Счёт не найден или уже обработан.")
        return

    user = await session.get(User, payment.user_id)
    if not user or user.telegram_id != query.from_user.id:
        await query.answer(ok=False, error_message="Этот счёт выставлен другому пользователю.")
        return

    expected_stars = await stars_for_days(session, payment.days_purchased or 0)
    if query.total_amount != expected_stars:
        await query.answer(ok=False, error_message="Сумма счёта устарела. Запроси новый.")
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def stars_successful_payment(message: Message, session: AsyncSession) -> None:
    sp = message.successful_payment
    if sp.currency != "XTR":
        return

    payment_id = _parse_stars_payload(sp.invoice_payload)
    if not payment_id:
        logger.warning("Stars payment with unknown payload: %s", sp.invoice_payload)
        return

    payment = await session.get(Payment, payment_id)
    if not payment or payment.source != "stars":
        logger.warning("Stars payment #%s not found", payment_id)
        return

    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user or user.id != payment.user_id:
        logger.warning("Stars payment user mismatch for payment #%s", payment_id)
        return

    expected_stars = await stars_for_days(session, payment.days_purchased or 0)
    if sp.total_amount != expected_stars:
        logger.warning(
            "Stars amount mismatch for payment #%s: paid=%s expected=%s",
            payment_id,
            sp.total_amount,
            expected_stars,
        )
        return

    already_done = payment.status == PaymentStatus.APPROVED.value
    user, credited = await finalize_stars_payment(
        session,
        payment,
        charge_id=sp.telegram_payment_charge_id,
        stars_paid=sp.total_amount,
    )
    if already_done:
        await message.answer("✅ Эта оплата уже была обработана ранее.")
        return

    await notify_payment_approved(
        user.telegram_id,
        payment.amount_rub,
        payment.days_purchased or 0,
        user.balance_rub,
        credited=credited,
    )
    lines = ["✅ Оплата прошла!", ""]
    if credited > payment.amount_rub + 0.01:
        bonus = credited - payment.amount_rub
        lines.append(f"Оплачено: <b>{payment.amount_rub:.0f} ₽</b> ({payment.days_purchased} дн.)")
        lines.append(f"🎁 Бонус акции: <b>+{bonus:.0f} ₽</b>")
        lines.append(f"Зачислено: <b>{credited:.0f} ₽</b>")
    else:
        lines.append(
            f"Начислено: <b>{credited:.0f} ₽</b> ({payment.days_purchased} дн.)"
        )
    lines.append(f"Баланс: <b>{user.balance_rub:.0f} ₽</b>")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "💳 Пополнить")
async def topup_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await stars_topup_start(message, state, session)


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

    user, credited = await approve_payment(session, payment)
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
        credited=credited,
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
    stars_day = await get_stars_per_day(session)

    await message.answer(
        f"📊 Статистика\n\n"
        f"Пользователей: {len(users)}\n"
        f"Активных подключений: {sum(1 for u in users if u.vpn_active)}\n"
        f"Заявок на оплату: {len(pending)}\n\n"
        f"🌐 Админ-панель:\n{settings.web_base_url.rstrip('/')}/admin\n\n"
        f"Тариф: {settings.daily_price_rub:.0f} ₽/сутки\n"
        f"Stars: {stars_day} ⭐/сутки\n"
        f"Пробный период: {settings.trial_days} дня"
    )
