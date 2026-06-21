import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import PartnerCommission, PartnerPayout, Payment, PaymentStatus, Referral, User

logger = logging.getLogger(__name__)


async def accrue_partner_commission(
    session: AsyncSession,
    payment: Payment,
    payer: User,
) -> PartnerCommission | None:
    """Начисляет партнёру % с фактической суммы пополнения реферала."""
    if not payer.referrer_id:
        return None

    partner = await session.get(User, payer.referrer_id)
    if not partner or not partner.partner_enabled or partner.partner_commission_pct <= 0:
        return None

    existing = await session.execute(
        select(PartnerCommission).where(PartnerCommission.payment_id == payment.id)
    )
    if existing.scalar_one_or_none():
        return None

    commission = round(payment.amount_rub * partner.partner_commission_pct / 100, 2)
    if commission <= 0:
        return None

    row = PartnerCommission(
        partner_id=partner.id,
        referred_user_id=payer.id,
        payment_id=payment.id,
        payment_amount_rub=payment.amount_rub,
        commission_pct=partner.partner_commission_pct,
        commission_rub=commission,
    )
    session.add(row)
    partner.partner_balance_rub = round(partner.partner_balance_rub + commission, 2)
    logger.info(
        "Partner commission: partner=%s payment=%s amount=%.2f pct=%.1f commission=%.2f",
        partner.id,
        payment.id,
        payment.amount_rub,
        partner.partner_commission_pct,
        commission,
    )
    return row


async def set_partner_config(
    session: AsyncSession,
    user: User,
    *,
    enabled: bool,
    commission_pct: float,
) -> User:
    user.partner_enabled = enabled
    user.partner_commission_pct = max(0.0, min(100.0, round(commission_pct, 2)))
    await session.commit()
    await session.refresh(user)
    return user


async def record_partner_payout(
    session: AsyncSession,
    partner: User,
    amount: float,
    comment: str | None = None,
) -> PartnerPayout:
    amount = round(amount, 2)
    if amount <= 0:
        raise ValueError("Сумма выплаты должна быть больше 0")
    if amount > partner.partner_balance_rub + 0.01:
        raise ValueError(
            f"Нельзя выплатить {amount:.0f} ₽ — на балансе партнёра {partner.partner_balance_rub:.0f} ₽"
        )

    partner.partner_balance_rub = round(partner.partner_balance_rub - amount, 2)
    partner.partner_paid_out_total_rub = round(partner.partner_paid_out_total_rub + amount, 2)
    payout = PartnerPayout(
        partner_id=partner.id,
        amount_rub=amount,
        comment=comment or None,
    )
    session.add(payout)
    await session.commit()
    await session.refresh(partner)
    return payout


async def count_referred_with_topups(session: AsyncSession, partner_id: int) -> int:
    result = await session.execute(
        select(func.count(func.distinct(Payment.user_id)))
        .select_from(Payment)
        .join(Referral, Referral.referred_id == Payment.user_id)
        .where(
            Referral.referrer_id == partner_id,
            Payment.status == PaymentStatus.APPROVED.value,
        )
    )
    return int(result.scalar_one() or 0)


async def count_partner_topups(session: AsyncSession, partner_id: int) -> int:
    result = await session.execute(
        select(func.count(PartnerCommission.id)).where(PartnerCommission.partner_id == partner_id)
    )
    return int(result.scalar_one() or 0)


async def total_partner_earned(session: AsyncSession, partner: User) -> float:
    return round(partner.partner_balance_rub + partner.partner_paid_out_total_rub, 2)


async def get_partner_stats(session: AsyncSession, partner: User) -> dict:
    from bot.services.users import count_referrals

    return {
        "enabled": partner.partner_enabled,
        "commission_pct": partner.partner_commission_pct,
        "balance_rub": partner.partner_balance_rub,
        "paid_out_total_rub": partner.partner_paid_out_total_rub,
        "earned_total_rub": await total_partner_earned(session, partner),
        "referrals_count": await count_referrals(session, partner),
        "referrals_paid_count": await count_referred_with_topups(session, partner.id),
        "topups_count": await count_partner_topups(session, partner.id),
    }


async def build_admin_partner_stats(session: AsyncSession, users: list[User]) -> dict[int, dict]:
    stats: dict[int, dict] = {}
    for user in users:
        if user.partner_enabled or user.partner_balance_rub > 0 or user.partner_paid_out_total_rub > 0:
            stats[user.id] = await get_partner_stats(session, user)
    return stats


async def list_partner_commissions(
    session: AsyncSession,
    partner_id: int,
    *,
    limit: int = 20,
) -> list[PartnerCommission]:
    result = await session.execute(
        select(PartnerCommission)
        .where(PartnerCommission.partner_id == partner_id)
        .order_by(PartnerCommission.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
