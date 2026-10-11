"""/owner: everything a shop owner manages. Every route here requires the shop_owner role.

The shop is always the logged-in owner's own shop, so an owner can never change someone else's.
"""
from datetime import date as Date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import bookings as booking_rules
from core import dashboard, plans, timeutil
from core import shops as shop_rules
from core.limits import limit_info, plan_of
from database import get_db
from models import Plan, Subscription, User
from routes.bookings import booking_out, detail_out
from routes.shops import shop_out
from schemas import (BookingDetailOut, CompleteIn, DashboardOut, HoursDayIn, HoursOut, OwnerBookingsOut,
                     PlanPageOut, PlanPaymentOut, ServiceIn, ServiceOut, ShopOut, ShopUpdateIn)
from security import require_role

router = APIRouter()
owner_only = require_role("shop_owner")


@router.get("/services", response_model=list[ServiceOut])
def list_services(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """All the shop's services, hidden ones included, A to Z."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return sorted(shop.services, key=lambda s: s.service_name.lower())


@router.post("/services", response_model=ServiceOut, status_code=201)
def add_service(body: ServiceIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.add_service(db, shop, body.service_name, body.price, body.duration_min)


@router.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: str, body: ServiceIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.update_service(db, shop, service_id, body.model_dump(exclude_unset=True))


@router.get("/shop", response_model=ShopOut)
def get_shop(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    return shop_out(db, shop_rules.shop_of_owner(db, user.user_id))


@router.patch("/shop", response_model=ShopOut)
def update_shop(body: ShopUpdateIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    shop_rules.update_shop(db, shop, body.model_dump(exclude_unset=True))
    return shop_out(db, shop)


@router.put("/shop/hours", response_model=list[HoursOut])
def set_hours(body: list[HoursDayIn], user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """Send all 7 days. Closed days (open: false) lose their row."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.set_hours(db, shop, [d.model_dump() for d in body])


# ---------- dashboard and bookings ----------

@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(date: Optional[Date] = None, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """The week at a glance and the queue for `date` (default today; earlier dates show today)."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    today = timeutil.today()
    day = date if date and date >= today else today
    return {
        "shop_id": shop.shop_id,
        "shop_name": shop.shop_name,
        **dashboard.summary(db, shop, user),
        "date": day,
        "queue": [booking_out(b) for b in booking_rules.queue_for_day(db, shop, day)],
    }


@router.get("/bookings", response_model=OwnerBookingsOut)
def list_bookings(filter: str = "upcoming", user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """filter: upcoming | pending | completed | cancelled | no_show | all. Counts are given for every filter."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    rows, counts = booking_rules.for_owner(db, shop, filter)
    return {"shop_name": shop.shop_name, "filter": filter if filter in booking_rules.OWNER_FILTERS else "upcoming",
            "rows": [booking_out(b) for b in rows], "counts": counts}


@router.post("/bookings/{booking_id}/complete", response_model=BookingDetailOut)
def complete(booking_id: str, body: CompleteIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """On the day: the customer came. Records the rest of the price (cash, promptpay or card)."""
    b = booking_rules.get_owners_booking(db, booking_id, user)
    b = booking_rules.complete(db, b.booking_id, body.method)
    return detail_out(db, b, "owner", user)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingDetailOut)
def no_show(booking_id: str, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """On the day: the customer didn't come. The deposit is kept."""
    b = booking_rules.get_owners_booking(db, booking_id, user)
    b = booking_rules.mark_no_show(db, b.booking_id)
    return detail_out(db, b, "owner", user)


# ---------- plan ----------

def plan_page(db: Session, user: User) -> dict:
    shop = shop_rules.shop_of_owner(db, user.user_id)
    sub, plan = plan_of(db, shop.shop_id)
    payments = []
    for p in plans.plan_payments(db, shop):
        out = PlanPaymentOut.model_validate(p)
        out.plan_name = db.get(Plan, db.get(Subscription, p.subscription_id).plan_id).plan_name
        payments.append(out)
    return {
        "plan": plan,
        "subscription": sub,
        "usage": limit_info(db, shop.shop_id, timeutil.today()),
        "plans": db.scalars(select(Plan).order_by(Plan.monthly_price)).all(),
        "payments": payments,
    }


@router.get("/plan", response_model=PlanPageOut)
def get_plan(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    return plan_page(db, user)


@router.post("/plan/upgrade", response_model=PlanPageOut)
def upgrade(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """Test mode: pays one month of Pro and switches to it today."""
    plans.upgrade_to_pro(db, shop_rules.shop_of_owner(db, user.user_id), user)
    return plan_page(db, user)


@router.post("/plan/downgrade", response_model=PlanPageOut)
def downgrade(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """Ends Pro today and starts Free."""
    plans.switch_to_free(db, shop_rules.shop_of_owner(db, user.user_id))
    return plan_page(db, user)
