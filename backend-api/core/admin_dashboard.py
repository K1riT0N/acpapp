"""Platform-wide operational metrics for the Admin dashboard."""
from datetime import date, datetime, time

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from core import timeutil
from models import Booking, Payment, Plan, Shop, Subscription, User

MONTHS_SHOWN = 6


def _month_start(day: date, offset: int = 0) -> date:
    month_index = day.year * 12 + day.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _monthly_counts(db: Session, column, start: datetime, end: datetime) -> dict[tuple[int, int], int]:
    local_time = func.timezone(timeutil.BANGKOK.key, column)
    year = extract("year", local_time)
    month = extract("month", local_time)
    rows = db.execute(
        select(year, month, func.count()).where(column >= start, column < end).group_by(year, month)
    ).all()
    return {(int(y), int(m)): int(count) for y, m, count in rows}


def summary(db: Session, today: date) -> dict:
    """Return user/shop totals, paid transaction totals and six months of chart data."""
    current_month = _month_start(today)
    first_month = _month_start(today, -(MONTHS_SHOWN - 1))
    next_month = _month_start(today, 1)
    start = datetime.combine(first_month, time.min, tzinfo=timeutil.BANGKOK)
    end = datetime.combine(next_month, time.min, tzinfo=timeutil.BANGKOK)

    user_counts = _monthly_counts(db, User.created_at, start, end)
    booking_counts = _monthly_counts(db, Booking.created_at, start, end)

    payment_local_time = func.timezone(timeutil.BANGKOK.key, Payment.paid_at)
    payment_year = extract("year", payment_local_time)
    payment_month = extract("month", payment_local_time)
    payment_rows = db.execute(
        select(payment_year, payment_month, func.count(), func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.paid_at >= start, Payment.paid_at < end, Payment.status == "paid")
        .group_by(payment_year, payment_month)
    ).all()
    payment_totals = {
        (int(year), int(month)): (int(count), int(amount))
        for year, month, count, amount in payment_rows
    }

    months = []
    for offset in range(MONTHS_SHOWN):
        month_start = _month_start(first_month, offset)
        key = (month_start.year, month_start.month)
        transactions, volume = payment_totals.get(key, (0, 0))
        months.append({
            "month": month_start.strftime("%b %Y"),
            "users": user_counts.get(key, 0),
            "bookings": booking_counts.get(key, 0),
            "transactions": transactions,
            "transaction_volume": volume,
        })

    active_subscriptions = db.execute(
        select(func.coalesce(func.sum(Plan.monthly_price), 0))
        .join(Subscription, Subscription.plan_id == Plan.plan_id)
        .where(
            Subscription.status == "active",
            Subscription.start_date <= today,
            (Subscription.end_date.is_(None)) | (Subscription.end_date >= today),
        )
    ).scalar_one()
    current_key = (current_month.year, current_month.month)
    current_transactions, current_volume = payment_totals.get(current_key, (0, 0))

    return {
        # Accounts have no suspension/deactivation field, so every registered account is active.
        "active_users": db.scalar(select(func.count(User.user_id))) or 0,
        "total_shops": db.scalar(select(func.count(Shop.shop_id))) or 0,
        "transactions_this_month": current_transactions,
        "transaction_volume_this_month": current_volume,
        "projected_mrr": int(active_subscriptions),
        "projected_arr": int(active_subscriptions) * 12,
        "months": months,
    }
