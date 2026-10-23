"""Numbers for the owner's dashboard (the prototype's vDash and dayCapacity)."""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import timeutil
from core.limits import limit_info, plan_of
from core.shops import active_services
from core.slots import hours_for, to_min
from core.status import occupies
from models import Booking, Notification, Shop, User

DAYS_SHOWN = 7
LATEST_ALERTS = 4


def day_capacity(shop: Shop, day: date) -> Optional[int]:
    """A rough estimate of how many customers the shop can serve that day. None when closed.

    (minutes open / average length of the shop's active services, or 60 if it has none) x max_per_slot.
    """
    h = hours_for(shop, day)
    if h is None:
        return None
    services = active_services(shop)
    avg = sum(s.duration_min for s in services) / len(services) if services else 60
    per_place = max(1, int((to_min(h.close_time) - to_min(h.open_time)) // avg))
    return per_place * max(1, h.max_per_slot)


def week(db: Session, shop: Shop) -> list[dict]:
    """Today and the next 6 days: bookings taking a place, against the day's capacity."""
    now = timeutil.now()
    end = now.date() + timedelta(days=DAYS_SHOWN)
    rows = db.scalars(select(Booking).where(Booking.shop_id == shop.shop_id, Booking.booking_date >= now.date(),
                                            Booking.booking_date < end)).all()
    out = []
    for i in range(DAYS_SHOWN):
        day = now.date() + timedelta(days=i)
        out.append({
            "date": day,
            "count": sum(1 for b in rows if b.booking_date == day and occupies(b, now)),
            "capacity": day_capacity(shop, day),
        })
    return out


def summary(db: Session, shop: Shop, owner: User) -> dict:
    """Plan, this month's usage, the week, the latest alerts and how many reminders are waiting."""
    today = timeutil.today()
    alerts = db.scalars(select(Notification).where(Notification.recipient_id == owner.user_id,
                                                   Notification.status == "sent")
                        .order_by(Notification.sent_at.desc()).limit(LATEST_ALERTS)).all()
    pending = db.scalars(select(Notification.notification_id).join(Booking, Notification.booking_id == Booking.booking_id)
                         .where(Booking.shop_id == shop.shop_id, Notification.status == "pending")).all()
    return {
        "plan": plan_of(db, shop.shop_id)[1],
        "usage": limit_info(db, shop.shop_id, today),
        "days": week(db, shop),
        "alerts": alerts,
        "pending_reminders": len(pending),
    }
