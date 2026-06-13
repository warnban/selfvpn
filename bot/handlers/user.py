from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main import app_download_kb, menu_for
from bot.messages import amnezia_setup_steps, new_user_welcome
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
        intro = new_user_welcome(
            name,
            settings.brand_name,
            cabinet_link,
            trial_days=settings.trial_days,
            trial_balance=settings.trial_balance_rub,
            daily_price=settings.daily_price_rub,
            referral_ok=bool(referrer_tid and user.referrer_id),
        )
        await message.answer(
            intro,
            reply_markup=menu_for(message.from_user.id),
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
        await message.answer(text, reply_markup=menu_for(message.from_user.id), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обновить клавиатуру (если кнопки устарели)."""
    await message.answer("Меню обновлено 👇", reply_markup=menu_for(message.from_user.id))


@router.message(F.text.in_({"🔐 Подключить VPN", "Подключить VPN"}))
async def legacy_connect_vpn(message: Message, session: AsyncSession) -> None:
    """Старая кнопка — перенаправляем в «Мои устройства»."""
    from bot.handlers.devices import my_devices

    await message.answer(
        "Кнопка «Подключить VPN» устарела.\n"
        "Открываю «📱 Мои устройства»…\n"
        "Нажми /menu если меню не обновилось.",
        reply_markup=menu_for(message.from_user.id),
    )
    await my_devices(message, session)


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
        "• «💳 Пополнить» — ссылка на оплату в личном кабинете\n"
        "• «👥 Рефералы» — приглашай друзей, получай бонус",
        reply_markup=app_download_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
