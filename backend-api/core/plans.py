"""Subscriptions. (Step 10 adds upgrading to Pro and switching back to Free here.)"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import timeutil
from core.limits import plan_of
from models import Subscription


def ensure_free(db: Session, shop_id: str) -> None:
    """Every shop always has an active subscription: if none is current, start a Free one today."""
    today = timeutil.today()
    if plan_of(db, shop_id, today)[0] is not None:
        return
    sub_id = f"sub_free_{shop_id}_{today:%Y%m%d}"
    if db.get(Subscription, sub_id) is None:
        db.add(Subscription(subscription_id=sub_id, shop_id=shop_id, plan_id="free",
                            start_date=today, end_date=None, status="active"))
        db.flush()


def expire_pro_subscriptions(db: Session) -> int:
    """Scheduler job: Pro months that have ended become expired, and the shop moves to Free."""
    today = timeutil.today()
    ended = db.scalars(select(Subscription).where(Subscription.status == "active", Subscription.plan_id == "pro",
                                                  Subscription.end_date < today)).all()
    for sub in ended:
        sub.status = "expired"
        db.flush()  # so ensure_free no longer sees this one as active
        ensure_free(db, sub.shop_id)
    return len(ended)
