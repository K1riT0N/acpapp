"""Which plan a shop is on. (Step 6 adds the monthly booking limit here.)"""
from datetime import date
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core import timeutil
from models import Plan, Subscription


def plan_of(db: Session, shop_id: str, on: Optional[date] = None) -> tuple[Optional[Subscription], Plan]:
    """The shop's current subscription and plan, like the prototype's planOf().

    A subscription counts when it is active and `on` (default today) lies between its start and end.
    If two match, Pro wins. If none match, the shop is treated as Free.
    """
    on = on or timeutil.today()
    subs = db.scalars(
        select(Subscription).where(
            Subscription.shop_id == shop_id,
            Subscription.status == "active",
            Subscription.start_date <= on,
            or_(Subscription.end_date.is_(None), Subscription.end_date >= on),
        )
    ).all()
    sub = next((s for s in subs if s.plan_id == "pro"), subs[0] if subs else None)
    plan = db.get(Plan, sub.plan_id if sub else "free")
    return sub, plan


def ensure_plans(db: Session) -> None:
    """Create the Free and Pro plans if the database has none yet (for example before seed.py has run).

    These are only starting values. Every rule reads the limit and price from the plans table.
    """
    if db.scalar(select(Plan.plan_id).limit(1)) is None:
        db.add_all([
            Plan(plan_id="free", plan_name="Free", monthly_price=0, booking_limit=10),
            Plan(plan_id="pro", plan_name="Pro", monthly_price=299, booking_limit=None),
        ])
        db.commit()
