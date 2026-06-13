from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main import app_download_kb, main_menu
from bot.messages import amnezia_setup_steps
from bot.services.devices import count_devices, days_left_for, user_daily_cost
from bot.services.users import count_referrals, get_user_by_telegram_id, register_user

router = Router()


def parse_referrer(message: Message) -> int | None:
    if not message.text:
        return None
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if payload.startswith("ref_"):
        try:
            return int(payload.replace("ref_", ""))
        except ValueError:
            return None
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    referrer_tid = parse_referrer(message)
    user, is_new = await register_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referrer_telegram_id=referrer_tid,
    )

    cabinet_link = settings.cabinet_url(user.cabinet_token)
    name = message.from_user.first_name or "друг"

    if is_new:
        intro = (
            f"👋 Привет, <b>{name}</b>!\n\n"
            f"🎁 Пробный доступ: <b>{settings.trial_days} дня</b> "
            f"({settings.trial_balance_rub:.0f} ₽ на балансе)\n"
            f"📅 Тариф: <b>{settings.daily_price_rub:.0f} ₽/сутки</b> за каждое устройство\n"
        )
        if referrer_tid and user.referrer_id:
            intro += f"👥 Реферальная ссылка сработала — спасибо!\n"
        intro += (
            f"\n🌐 <b>Личный кабинет</b> (работает без Telegram):\n"
            f"<a href=\"{cabinet_link}\">{cabinet_link}</a>\n\n"
            "Чтобы подключиться — открой «📱 Мои устройства» и добавь устройство."
        )
        await message.answer(intro, reply_markup=main_menu(), parse_mode="HTML")
        await message.answer(
            amnezia_setup_steps(),
            reply_markup=app_download_kb(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        devices = await count_devices(session, user)
        left = await days_left_for(session, user)
        text = (
            f"С возвращением, <b>{name}</b>!\n\n"
            f"💰 Баланс: <b>{user.balance_rub:.0f} ₽</b>\n"
            f"📱 Устройств: <b>{devices}</b> (~{left} дн.)\n\n"
            f"🌐 <a href=\"{cabinet_link}\">Личный кабинет</a>"
        )
        await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@router.message(F.text == "🌐 Личный кабинет")
async def show_cabinet(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return
    link = settings.cabinet_url(user.cabinet_token)
    await message.answer(
        f"🌐 <b>Личный кабинет</b>\n\n"
        f"<a href=\"{link}\">{link}</a>\n\n"
        "Там баланс, оплата и устройства — даже если Telegram заблокирован.",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    devices = await count_devices(session, user)
    cost = await user_daily_cost(session, user)
    left = await days_left_for(session, user)
    await message.answer(
        f"💰 <b>Баланс:</b> {user.balance_rub:.0f} ₽\n"
        f"📅 <b>Тариф:</b> {settings.daily_price_rub:.0f} ₽/сутки за устройство\n"
        f"📱 <b>Устройств:</b> {devices}\n"
        f"💸 <b>Списание:</b> {cost:.0f} ₽/сутки\n"
        f"⏳ <b>Хватит на:</b> ~{left} дн.",
        parse_mode="HTML",
    )


@router.message(F.text == "👥 Рефералы")
async def show_referrals(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}"
    ref_count = await count_referrals(session, user)

    await message.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Твоя ссылка:\n<code>{ref_link}</code>\n\n"
        f"За каждого нового пользователя — <b>+{settings.referral_bonus_rub:.0f} ₽</b> на баланс.\n"
        f"Приглашено: <b>{ref_count}</b> чел.",
        parse_mode="HTML",
    )


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message) -> None:
    await message.answer(
        amnezia_setup_steps() + "\n\n"
        "<b>Устройства и оплата</b>\n"
        "• «📱 Мои устройства» — добавляй/удаляй устройства\n"
        "• Каждое устройство = +тариф за сутки\n"
        "• «💳 Пополнить» — выбери дни, переведи, отправь скрин\n"
        "• «👥 Рефералы» — приглашай друзей, получай бонус",
        reply_markup=app_download_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
