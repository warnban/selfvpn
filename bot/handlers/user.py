from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main import BTN_ABOUT, BTN_CABINET, BTN_INVITE, BTN_SUPPORT, invite_kb, menu_for
from bot.messages import cabinet_intro, new_user_welcome
from bot.services.devices import count_devices, days_left_for
from bot.services.auth import link_telegram_to_user, load_telegram_link_user_id
from bot.services.users import count_referrals, get_user_by_telegram_id, register_user

router = Router()


def parse_start_payload(message: Message) -> tuple[str | None, int | None]:
    """Returns (action, value) where action is 'ref', 'link', or None."""
    if not message.text:
        return None, None
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    payload = parts[1].strip()
    if payload.startswith("ref_"):
        try:
            return "ref", int(payload.replace("ref_", ""))
        except ValueError:
            return None, None
    if payload.startswith("link_"):
        return "link", None
    return None, None


def parse_referrer(message: Message) -> int | None:
    action, value = parse_start_payload(message)
    if action == "ref":
        return value
    return None


def parse_link_token(message: Message) -> str | None:
    if not message.text:
        return None
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if payload.startswith("link_"):
        return payload.replace("link_", "", 1)
    return None


async def _try_channel_bonus(message: Message, session: AsyncSession, user) -> None:
    """После привязки/проверки пробуем выдать бонус за подписку на канал."""
    if not settings.channel_bonus_enabled or user.channel_bonus_paid:
        return
    from bot.services.channel import GRANT_GRANTED, GRANT_NOT_SUBSCRIBED, grant_channel_bonus

    result = await grant_channel_bonus(session, user)
    if result == GRANT_GRANTED:
        await message.answer(
            f"🎁 Бонус за подписку на канал: <b>+{settings.channel_bonus_rub:.0f} ₽</b>\n"
            f"💰 Баланс: <b>{user.balance_rub:.0f} ₽</b>",
            parse_mode="HTML",
        )
    elif result == GRANT_NOT_SUBSCRIBED:
        await message.answer(
            "Чтобы получить бонус, подпишитесь на канал "
            f"{settings.channel_url} и нажмите «Проверить подписку» в личном кабинете.",
            disable_web_page_preview=True,
        )


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    link_token = parse_link_token(message)
    if link_token:
        user_id = load_telegram_link_user_id(link_token)
        if not user_id:
            await message.answer("Ссылка привязки устарела. Запросите новую в личном кабинете.")
            return
        from bot.services.users import get_user_by_id

        user = await get_user_by_id(session, user_id)
        if not user:
            await message.answer("Аккаунт не найден.")
            return
        err = await link_telegram_to_user(
            session,
            user,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        if err:
            await message.answer(f"❌ {err}")
            return
        cabinet_link = settings.cabinet_url(user.cabinet_token)
        await message.answer(
            f"✅ Telegram привязан к аккаунту <b>{user.email}</b>!\n\n"
            f"🌐 <a href=\"{cabinet_link}\">Личный кабинет</a>",
            reply_markup=menu_for(message.from_user.id),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        await _try_channel_bonus(message, session, user)
        return

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
            f"💰 Баланс: <b>{user.balance_rub:.0f} ₽</b> · ~{left} дн.\n"
            f"📱 Устройств: <b>{devices}</b>\n\n"
            f"🌐 <a href=\"{cabinet_link}\">Личный кабинет</a> — ключи и настройка подключения"
        )
        await message.answer(text, reply_markup=menu_for(message.from_user.id), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Обновить клавиатуру (если кнопки устарели)."""
    await message.answer("Меню обновлено 👇", reply_markup=menu_for(message.from_user.id))


@router.message(Command("terms"))
async def cmd_terms(message: Message) -> None:
    await message.answer(
        f"📄 <b>Условия использования {settings.brand_name}</b>\n\n"
        f"• Тариф: {settings.daily_price_rub:.0f} ₽ за устройство в сутки.\n"
        "• Баланс списывается ежедневно; при нулевом балансе доступ приостанавливается.\n"
        "• Оплата Stars и картой пополняет баланс; возврат — через поддержку.\n"
        "• Используя сервис, вы соглашаетесь с этими условиями.\n\n"
        f"Полные условия: {settings.web_base_url.rstrip('/')}/about\n"
        f"Поддержка: /paysupport",
        parse_mode="HTML",
    )


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message) -> None:
    url = settings.support_tg_url()
    handle = settings.support_tg_handle
    if url:
        await message.answer(
            "🧾 <b>Поддержка по оплатам</b>\n\n"
            "Если оплата прошла, но баланс не начислился — напишите в поддержку "
            "с указанием даты, суммы и способа оплаты.\n\n"
            f"📞 <a href=\"tel:89169046701\">+7 (916) 904-67-01</a>\n"
            f'💬 <a href="{url}">Telegram @{handle}</a>\n\n'
            "Telegram не помогает с покупками в ботах — только мы.",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        await message.answer(
            "🧾 <b>Поддержка по оплатам</b>\n\n"
            "Напишите администратору с указанием даты, суммы и способа оплаты.",
            parse_mode="HTML",
        )


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await show_about(message)


@router.message(F.text == BTN_ABOUT)
async def show_about(message: Message) -> None:
    url = settings.about_url()
    await message.answer(
        f"ℹ️ <b>О сервисе</b>\n\n"
        f"Условия, политика конфиденциальности и контакты поддержки:\n"
        f'<a href="{url}">{url}</a>',
        parse_mode="HTML",
        disable_web_page_preview=False,
    )


@router.message(F.text.in_({"🔐 Подключить", "Подключить", "🔐 Подключить VPN", "Подключить VPN", "📱 Мои устройства", "💰 Баланс", "ℹ️ Помощь"}))
async def legacy_menu_buttons(message: Message, session: AsyncSession) -> None:
    """Старые кнопки меню — перенаправляем в личный кабинет."""
    from bot.messages import amnezia_setup_steps

    extra = ""
    if message.text in {"ℹ️ Помощь", "🔐 Подключить", "Подключить", "🔐 Подключить VPN", "Подключить VPN"}:
        extra = f"\n\n{amnezia_setup_steps()}"

    await message.answer(
        "Эта кнопка больше не в меню — всё в <b>личном кабинете</b>."
        f"{extra}\n\n"
        "Нажми /menu чтобы обновить клавиатуру.",
        reply_markup=menu_for(message.from_user.id),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await show_cabinet(message, session)


@router.message(F.text == BTN_CABINET)
async def show_cabinet(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return
    link = settings.cabinet_url(user.cabinet_token)
    devices = await count_devices(session, user)
    left = await days_left_for(session, user)
    await message.answer(
        cabinet_intro(link, device_count=devices, days_left=left),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text.in_({BTN_INVITE, "👥 Рефералы"}))
async def show_invite(message: Message, session: AsyncSession) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}"
    ref_count = await count_referrals(session, user)

    await message.answer(
        f"👥 <b>Пригласить друга</b>\n\n"
        "Нажми <b>«Скопировать ссылку»</b> — она попадёт в буфер обмена.\n"
        "Или <b>«Поделиться»</b>, чтобы отправить другу в Telegram.\n\n"
        f"За каждого нового пользователя — <b>+{settings.referral_bonus_rub:.0f} ₽</b> на баланс.\n"
        f"Приглашено: <b>{ref_count}</b> чел.",
        reply_markup=invite_kb(ref_link),
        parse_mode="HTML",
    )


@router.message(F.text == BTN_SUPPORT)
async def show_support(message: Message) -> None:
    url = settings.support_tg_url()
    handle = settings.support_tg_handle
    if url:
        await message.answer(
            f"🆘 <b>Поддержка</b>\n\n"
            f"📞 <a href=\"tel:89169046701\">+7 (916) 904-67-01</a>\n"
            f'💬 <a href="{url}">Telegram @{handle}</a>',
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
