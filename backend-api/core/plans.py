"""Subscriptions: upgrading to Pro, switching back to Free, and Pro months running out.

Rule: every shop always has exactly one current subscription. Each change ends the old one (status
"ended", end_date today) and starts the new one in the same transaction.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import notify, timeutil
from core.errors import RuleError
from core.ids import new_id
from core.limits import plan_of
from core.payments import pay_subscription_test
from models import Payment, Plan, Shop, Subscription, User


def _start(db: Session, shop_id: str, plan_id: str, end=None) -> Subscription:
    sub = Subscription(subscription_id=new_id("sub"), shop_id=shop_id, plan_id=plan_id,
                       start_date=timeutil.today(), end_date=end, status="active")
    db.add(sub)
    db.flush()
    return sub


def _lock_shop(db: Session, shop: Shop) -> None:
    """Plan changes for one shop happen one at a time (two clicks can't create two Pro months)."""
    db.execute(select(Shop.shop_id).where(Shop.shop_id == shop.shop_id).with_for_update())


def ensure_free(db: Session, shop_id: str) -> None:
    """If the shop has no current subscription, start a Free one today."""
    if plan_of(db, shop_id)[0] is None:
        _start(db, shop_id, "free")


def upgrade_to_pro(db: Session, shop: Shop, owner: User) -> Subscription:
    """Test mode: pay one month of Pro (price from the plans table) and switch to it today."""
    _lock_shop(db, shop)
    current, plan = plan_of(db, shop.shop_id)
    if plan.plan_id == "pro":
        raise RuleError("You're already on Pro.", 409)
    pro = db.get(Plan, "pro")
    today = timeutil.today()
    if current is not None:
        current.status, current.end_date = "ended", today
    db.flush()  # so plan_of no longer sees the old subscription
    end = timeutil.add_months(today, 1)
    sub = _start(db, shop.shop_id, "pro", end)
    pay_subscription_test(db, sub.subscription_id, pro.monthly_price)
    notify.on_pro_started(db, owner, end)
    db.commit()
    return sub


def switch_to_free(db: Session, shop: Shop) -> Subscription:
    _lock_shop(db, shop)
    current, plan = plan_of(db, shop.shop_id)
    if plan.plan_id != "pro" or current is None:
        raise RuleError("You're already on the Free plan.", 409)
    current.status, current.end_date = "ended", timeutil.today()
    db.flush()
    sub = _start(db, shop.shop_id, "free")
    db.commit()
    return sub


def plan_payments(db: Session, shop: Shop) -> list[Payment]:
    """The shop's subscription payments, newest first."""
    return db.scalars(select(Payment).join(Subscription, Payment.subscription_id == Subscription.subscription_id)
                      .where(Subscription.shop_id == shop.shop_id).order_by(Payment.paid_at.desc())).all()


def expire_pro_subscriptions(db: Session) -> int:
    """Scheduler job: Pro months that have ended become expired, and the shop moves to Free."""
    today = timeutil.today()
    ended = db.scalars(select(Subscription).where(Subscription.status == "active", Subscription.plan_id == "pro",
                                                  Subscription.end_date < today)).all()
    for sub in ended:
        sub.status = "expired"
        db.flush()  # so ensure_free no longer sees this one as current
        ensure_free(db, sub.shop_id)
    return len(ended)
