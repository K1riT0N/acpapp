"""Time slots a customer can book (the prototype's slotsFor) and the 14-day calendar."""
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import timeutil
from core.status import occupies
from models import Booking, BusinessHours, Shop

SLOT_STEP = 30  # a slot starts every 30 minutes


def to_min(t: time) -> int:
    return t.hour * 60 + t.minute


def from_min(m: int) -> time:
    return time(m // 60, m % 60)


def hours_for(shop: Shop, day: date) -> Optional[BusinessHours]:
    """The opening hours for that day, or None when the shop is closed."""
    dow = timeutil.day_of_week(day)
    return next((h for h in shop.hours if h.day_of_week == dow), None)


def slots_for(db: Session, shop: Shop, day: date, duration: int, now: Optional[datetime] = None) -> Optional[list[dict]]:
    """Every start time on `day` for a service of `duration` minutes. None if the shop is closed.

    A slot runs from `t` to `t + duration`. It is full when the bookings overlapping that period
    reach max_per_slot. On today's date, start times at or before the current time are "past".
    """
    now = now or timeutil.now()
    h = hours_for(shop, day)
    if h is None:
        return None
    opens, closes, cap = to_min(h.open_time), to_min(h.close_time), max(1, h.max_per_slot)
    taken = [
        b for b in db.scalars(select(Booking).where(Booking.shop_id == shop.shop_id, Booking.booking_date == day))
        if occupies(b, now)
    ]
    is_today = day == now.date()
    now_min = now.hour * 60 + now.minute

    out = []
    t = opens
    while t + duration <= closes:
        used = sum(1 for b in taken if to_min(b.start_time) < t + duration and t < to_min(b.end_time))
        out.append({
            "time": from_min(t),
            "used": used,
            "cap": cap,
            "full": used >= cap,
            "past": is_today and t <= now_min,
        })
        t += SLOT_STEP
    return out


def calendar(db: Session, shop: Shop, duration: int, days: int = 14) -> list[dict]:
    """For each day from today: is the shop open, and is any time still free?"""
    now = timeutil.now()
    out = []
    for i in range(days):
        day = now.date() + timedelta(days=i)
        slots = slots_for(db, shop, day, duration, now)
        out.append({
            "date": day,
            "open": slots is not None,
            "has_free_slot": bool(slots) and any(not s["full"] and not s["past"] for s in slots),
        })
    return out
