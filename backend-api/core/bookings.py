"""Everything that happens to a booking: create, view, release, cancel, complete, no-show, and the lists."""
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import notify, timeutil
from core.errors import NotFound, RuleError
from core.ids import new_id, random_code
from core.limits import limit_info
from core.shops import active_services
from core.slots import from_min, slots_for, to_min
from core.payments import record_remaining
from core.status import HOLD_MINUTES, counts_toward_limit, hold_active
from models import Booking, Service, Shop, User

BOOKING_WINDOW_DAYS = 14  # customers can book today and the next 13 days


def deposit_of(price: int, percent: int) -> int:
    """Deposit = price x percent / 100, rounded to whole baht, halves up (the prototype's Math.round).

    Python's round() rounds halves to the even number (round(112.5) == 112), so we use whole-number
    maths instead: adding 50 before dividing by 100 rounds .5 up. 450 x 25% = 112.5 -> 113.
    """
    return (price * percent + 50) // 100


def limit_message(shop: Shop, day: date) -> str:
    return (f"{shop.shop_name} has reached its booking limit for {timeutil.month_name(day)}. "
            f"Try a date next month, or call the shop on {shop.phone}.")


def _new_ref(db: Session) -> str:
    while True:  # 32^5 = 33 million codes, so a clash is rare, but check anyway
        ref = random_code(5)
        if db.scalar(select(Booking.booking_id).where(Booking.ref == ref)) is None:
            return ref


def create_booking(db: Session, customer: User, shop_id: str, service_id: str, day: date, start: time) -> Booking:
    """Hold a time for 15 minutes while the customer pays the deposit.

    Everything happens in ONE transaction that starts by locking the shop's row (SELECT ... FOR UPDATE).
    A second customer booking the same shop at the same moment waits at that line until we commit, and
    then sees our booking when it counts the slot. That's what prevents double booking.
    """
    shop = db.scalar(select(Shop).where(Shop.shop_id == shop_id)
                     .with_for_update().execution_options(populate_existing=True))
    if shop is None:
        raise NotFound("That shop isn't listed.")
    service = db.get(Service, service_id)
    if service is None or service.shop_id != shop.shop_id or not service.is_active:
        raise RuleError("That service isn't available any more. Pick another one.")

    now = timeutil.now()
    if not now.date() <= day < now.date() + timedelta(days=BOOKING_WINDOW_DAYS):
        raise RuleError(f"Pick a day in the next {BOOKING_WINDOW_DAYS} days.")
    slots = slots_for(db, shop, day, service.duration_min, now)
    if slots is None:
        raise RuleError(f"{shop.shop_name} is closed on {timeutil.DAY_NAMES[timeutil.day_of_week(day)]}s. Pick another day.")
    slot = next((s for s in slots if s["time"] == start), None)
    if slot is None:
        raise RuleError("Pick one of the times shown.")
    if slot["full"] or slot["past"]:
        raise RuleError("That time was just taken. Pick another time.", 409)
    if limit_info(db, shop.shop_id, day, now)["reached"]:
        raise RuleError(limit_message(shop, day), 409)

    deposit = deposit_of(service.price, shop.deposit_percent)
    b = Booking(
        booking_id=new_id("b"),
        ref=_new_ref(db),
        customer_id=customer.user_id,
        shop_id=shop.shop_id,
        service_id=service.service_id,
        booking_date=day,
        start_time=start,
        end_time=from_min(to_min(start) + service.duration_min),
        status="pending_payment",
        # Copied now, so later changes to the price or deposit rate don't change this booking
        total_price=service.price,
        deposit_amount=deposit,
        remaining_amount=service.price - deposit,
        hold_expires_at=now + timedelta(minutes=HOLD_MINUTES),
        created_at=now,
    )
    db.add(b)
    db.commit()  # also releases the shop lock
    return b


def get_for_viewer(db: Session, booking_id: str, user: User) -> tuple[Booking, str]:
    """The booking, if `user` is its customer or the shop's owner. Returns (booking, "customer" | "owner")."""
    b = db.get(Booking, booking_id)
    if b is None:
        raise NotFound("We couldn't find that booking.")
    if b.customer_id == user.user_id:
        return b, "customer"
    if b.shop.owner_id == user.user_id:
        return b, "owner"
    raise NotFound("This booking belongs to another account.")


def get_customers_booking(db: Session, booking_id: str, user: User) -> Booking:
    b = db.get(Booking, booking_id)
    if b is None or b.customer_id != user.user_id:
        raise NotFound("We couldn't find that booking.")
    return b


def release_hold(db: Session, b: Booking) -> Booking:
    """The customer pressed "Cancel and release this time" before paying."""
    if b.status != "pending_payment":
        raise RuleError("This booking isn't waiting for a deposit.", 409)
    b.status = "expired"
    db.commit()
    return b


def expire_holds(db: Session) -> int:
    """Scheduler job: unpaid holds whose 15 minutes are over become expired."""
    now = timeutil.now()
    stale = db.scalars(select(Booking).where(Booking.status == "pending_payment", Booking.hold_expires_at <= now)).all()
    for b in stale:
        b.status = "expired"
    return len(stale)


def sample_slot(db: Session) -> Optional[dict]:
    """For the home page's example ticket: the first free afternoon time in the next 7 days.

    Same choice as the prototype's heroTicket: shops A to Z, each shop's second-cheapest service,
    a time from 13:00 onwards.
    """
    now = timeutil.now()
    for shop in db.scalars(select(Shop).order_by(Shop.shop_name)):
        svcs = active_services(shop)
        if not svcs:
            continue
        v = svcs[min(1, len(svcs) - 1)]
        for i in range(1, 8):
            day = now.date() + timedelta(days=i)
            for s in slots_for(db, shop, day, v.duration_min, now) or []:
                if not s["full"] and not s["past"] and s["time"] >= time(13, 0):
                    return {"shop_id": shop.shop_id, "shop_name": shop.shop_name, "service_id": v.service_id,
                            "service_name": v.service_name, "date": day, "time": s["time"],
                            "deposit": deposit_of(v.price, shop.deposit_percent)}
    return None


# ---------- after the deposit ----------

PAY_METHODS = ("cash", "promptpay", "card")


def _lock(db: Session, booking_id: str) -> Booking:
    """Re-read the booking with a row lock, so two clicks at once can't both change it."""
    return db.scalar(select(Booking).where(Booking.booking_id == booking_id)
                     .with_for_update().execution_options(populate_existing=True))


def get_owners_booking(db: Session, booking_id: str, owner: User) -> Booking:
    b = db.get(Booking, booking_id)
    if b is None or b.shop.owner_id != owner.user_id:
        raise NotFound("We couldn't find that booking.")
    return b


def cancel_by_customer(db: Session, booking_id: str) -> Booking:
    """Only a confirmed booking that hasn't started yet. The deposit is kept (no refund row)."""
    b = _lock(db, booking_id)
    now = timeutil.now()
    if b.status != "confirmed":
        raise RuleError("Only a confirmed booking can be cancelled.", 409)
    if notify.booking_start(b) <= now:
        raise RuleError("This appointment has already started, so it can't be cancelled.", 409)
    b.status = "cancelled"
    b.cancelled_at = now
    notify.cancel_pending(db, b.booking_id)
    notify.on_cancelled(db, b)
    db.commit()
    return b


def _check_on_the_day(b: Booking) -> None:
    if b.status != "confirmed":
        raise RuleError("This booking isn't waiting to be served.", 409)
    if b.booking_date > timeutil.today():
        raise RuleError("You can mark this completed or a no-show on the day.", 409)


def complete(db: Session, booking_id: str, method: str) -> Booking:
    """The customer came and paid the rest at the shop."""
    if method not in PAY_METHODS:
        raise RuleError("Choose how the customer paid: cash, PromptPay or card.")
    b = _lock(db, booking_id)
    _check_on_the_day(b)
    record_remaining(db, b, method)
    b.status = "completed"
    notify.cancel_pending(db, b.booking_id)
    db.commit()
    return b


def mark_no_show(db: Session, booking_id: str) -> Booking:
    """The customer didn't come. The shop keeps the deposit."""
    b = _lock(db, booking_id)
    _check_on_the_day(b)
    b.status = "no_show"
    notify.cancel_pending(db, b.booking_id)
    notify.on_no_show(db, b)
    db.commit()
    return b


# ---------- lists ----------

def _start_key(b: Booking):
    return (b.booking_date, b.start_time)


def for_customer(db: Session, user: User) -> list[Booking]:
    """The customer's bookings, without expired holds (they never became bookings)."""
    return db.scalars(select(Booking).where(Booking.customer_id == user.user_id, Booking.status != "expired")
                      .order_by(Booking.booking_date, Booking.start_time)).all()


OWNER_FILTERS = ["upcoming", "pending", "completed", "cancelled", "no_show", "all"]


def _owner_filter(name: str, b: Booking, now) -> bool:
    if name == "upcoming":
        return b.booking_date >= now.date() and (b.status == "confirmed" or hold_active(b, now))
    if name == "pending":
        return hold_active(b, now)
    if name == "all":
        return b.status != "expired"
    return b.status == name


def for_owner(db: Session, shop: Shop, filter_name: str) -> tuple[list[Booking], dict]:
    """One filter's rows (upcoming and pending soonest first, the rest newest first) and every filter's count."""
    if filter_name not in OWNER_FILTERS:
        filter_name = "upcoming"
    now = timeutil.now()
    every = db.scalars(select(Booking).where(Booking.shop_id == shop.shop_id)).all()
    counts = {f: sum(1 for b in every if _owner_filter(f, b, now)) for f in OWNER_FILTERS}
    rows = sorted((b for b in every if _owner_filter(filter_name, b, now)), key=_start_key,
                  reverse=filter_name not in ("upcoming", "pending"))
    return rows, counts


def queue_for_day(db: Session, shop: Shop, day: date) -> list[Booking]:
    """The owner's queue for one day: everything except expired holds, by start time."""
    now = timeutil.now()
    rows = db.scalars(select(Booking).where(Booking.shop_id == shop.shop_id, Booking.booking_date == day)).all()
    return sorted((b for b in rows if counts_toward_limit(b, now)), key=_start_key)
