"""Tests for the booking rules in core/: slots, full slots, the monthly limit, holds, double booking and deposits.

The clock is frozen at Wednesday 23 Sep 2026, 09:00 Bangkok time (see conftest.py).
"""
import threading
from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from core import bookings, payments
from core.bookings import create_booking, deposit_of, expire_holds
from core.errors import RuleError
from core.limits import limit_info
from core.slots import slots_for
from database import SessionLocal
from models import Booking, Plan, Subscription

TOMORROW = date(2026, 9, 24)


def book(w, customer, day=TOMORROW, at=time(10), service=None):
    return create_booking(w.db, customer, "shop_t", (service or w.cut).service_id, day, at)


# ---------- slots ----------

def test_slots_start_every_30_minutes_and_must_end_by_closing(world):
    slots = slots_for(world.db, world.shop, TOMORROW, 45)
    times = [s["time"] for s in slots]
    assert times[0] == time(10, 0) and times[1] == time(10, 30)
    assert times[-1] == time(18, 0)  # 18:00 + 45 min = 18:45 <= 19:00, but 18:30 would end at 19:15
    assert all(s["cap"] == 2 and s["used"] == 0 and not s["full"] for s in slots)


def test_closed_day_has_no_slots(world):
    world.db.delete(world.db.get(type(world.shop.hours[0]), "bh_t_4"))  # close Thursdays
    world.db.commit()
    world.db.expire(world.shop, ["hours"])
    assert slots_for(world.db, world.shop, TOMORROW, 45) is None  # 24 Sep 2026 is a Thursday


def test_times_at_or_before_now_are_past_today(world, clock):
    clock.set(clock.now.replace(hour=11, minute=0))
    slots = {s["time"]: s for s in slots_for(world.db, world.shop, clock.now.date(), 45)}
    assert slots[time(10, 30)]["past"] and slots[time(11, 0)]["past"]
    assert not slots[time(11, 30)]["past"]
    with pytest.raises(RuleError) as err:
        book(world, world.ploy, day=clock.now.date(), at=time(11, 0))
    assert err.value.status_code == 409


# ---------- full slot ----------

def test_slot_is_full_at_max_per_slot(world):
    book(world, world.ploy, at=time(10))
    book(world, world.ton, at=time(10))
    slot = next(s for s in slots_for(world.db, world.shop, TOMORROW, 45) if s["time"] == time(10))
    assert slot["used"] == 2 and slot["full"]
    third = world.user("Third Customer")
    with pytest.raises(RuleError) as err:
        book(world, third, at=time(10))
    assert err.value.status_code == 409
    assert err.value.message == "That time was just taken. Pick another time."


def test_overlapping_longer_booking_takes_a_place(world):
    book(world, world.ploy, at=time(10), service=world.colour)  # 10:00-12:00
    slots = {s["time"]: s for s in slots_for(world.db, world.shop, TOMORROW, 45)}
    assert slots[time(11, 30)]["used"] == 1  # 11:30-12:15 overlaps 10:00-12:00
    assert slots[time(12, 0)]["used"] == 0  # starts exactly when the colour ends


# ---------- monthly limit ----------

def test_monthly_limit_comes_from_the_plans_table(world):
    world.db.get(Plan, "free").booking_limit = 3
    world.db.commit()
    for i, who in enumerate([world.ploy, world.ton, world.ploy]):
        book(world, who, at=time(10 + i))
    info = limit_info(world.db, "shop_t", TOMORROW)
    assert info == {"plan": "Free", "used": 3, "limit": 3, "reached": True}
    with pytest.raises(RuleError) as err:
        book(world, world.ton, at=time(15))
    assert err.value.status_code == 409
    assert err.value.message == ("Test Salon has reached its booking limit for September. "
                                 "Try a date next month, or call the shop on 02 000 0000.")
    # A booking in the next month is fine: the limit is per month
    book(world, world.ton, day=date(2026, 10, 1), at=time(10))


def test_pro_has_no_limit(world):
    world.db.get(Plan, "free").booking_limit = 1
    world.db.get(Subscription, "sub_t_free").status = "ended"
    world.db.add(Subscription(subscription_id="sub_t_pro", shop_id="shop_t", plan_id="pro",
                              start_date=date(2026, 9, 1), end_date=date(2026, 10, 1), status="active"))
    world.db.commit()
    for h in range(10, 14):
        book(world, world.ploy, at=time(h))
    assert limit_info(world.db, "shop_t", TOMORROW)["limit"] is None


# ---------- holds ----------

def test_new_booking_is_held_for_15_minutes(world, clock):
    b = book(world, world.ploy)
    assert b.status == "pending_payment"
    assert b.hold_expires_at == clock.now + timedelta(minutes=15)


def test_expired_hold_frees_slot_and_limit_before_the_job_runs(world, clock):
    world.db.get(Plan, "free").booking_limit = 2
    world.db.commit()
    book(world, world.ploy, at=time(10))
    book(world, world.ton, at=time(10))
    assert limit_info(world.db, "shop_t", TOMORROW)["reached"]

    clock.advance(minutes=16)  # nobody paid
    assert limit_info(world.db, "shop_t", TOMORROW)["used"] == 0
    slot = next(s for s in slots_for(world.db, world.shop, TOMORROW, 45) if s["time"] == time(10))
    assert slot["used"] == 0
    book(world, world.user("Late Customer"), at=time(10))  # allowed straight away

    # The background job then tidies up the status
    assert expire_holds(world.db) == 2
    world.db.commit()
    statuses = sorted(world.db.scalars(select(Booking.status)))
    assert statuses == ["expired", "expired", "pending_payment"]


def test_released_hold_frees_the_slot(world):
    b = book(world, world.ploy)
    bookings.release_hold(world.db, b)
    assert b.status == "expired"
    assert slots_for(world.db, world.shop, TOMORROW, 45)[0]["used"] == 0


# ---------- double booking ----------

def test_simultaneous_bookings_cannot_overfill_a_slot(world):
    """8 customers press "Continue to deposit" at the same moment for a slot with room for 2."""
    customers = [world.user(f"Racer {i}") for i in range(8)]
    world.db.commit()
    start = threading.Barrier(len(customers))
    results = []

    def attempt(customer_id):
        with SessionLocal() as s:  # each request has its own database session, like the real API
            customer = s.get(type(world.ploy), customer_id)
            start.wait()
            try:
                create_booking(s, customer, "shop_t", world.cut.service_id, TOMORROW, time(14))
                results.append("ok")
            except RuleError:
                results.append("taken")

    threads = [threading.Thread(target=attempt, args=(c.user_id,)) for c in customers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok", "ok"] + ["taken"] * 6
    assert len(world.db.scalars(select(Booking).where(Booking.start_time == time(14))).all()) == 2


# ---------- deposit maths ----------

@pytest.mark.parametrize("price, percent, deposit", [
    (450, 30, 135),
    (6500, 20, 1300),
    (900, 25, 225),
    (450, 25, 113),  # 112.5 rounds UP, like the prototype's Math.round (Python's round() would give 112)
    (300, 0, 0),
    (300, 100, 300),
])
def test_deposit_rounding(price, percent, deposit):
    assert deposit_of(price, percent) == deposit


def test_booking_copies_price_deposit_and_remaining(world):
    b = book(world, world.ploy)
    assert (b.total_price, b.deposit_amount, b.remaining_amount) == (450, 135, 315)
    assert b.end_time == time(10, 45)
    # Changing the price later doesn't change an existing booking
    world.cut.price = 999
    world.db.commit()
    world.db.refresh(b)
    assert b.total_price == 450


def test_paying_needs_the_policy_and_an_active_hold(world, clock):
    b = book(world, world.ploy)
    with pytest.raises(RuleError, match="Tick the deposit policy first."):
        payments.pay_deposit_test(world.db, b, policy_accepted=False)
    clock.advance(minutes=16)
    with pytest.raises(RuleError, match="Your hold on this time ran out"):
        payments.pay_deposit_test(world.db, b, policy_accepted=True)


def test_paying_confirms_and_records_a_test_payment(world):
    b = book(world, world.ploy)
    payments.pay_deposit_test(world.db, b, policy_accepted=True)
    assert b.status == "confirmed" and b.policy_accepted_at is not None
    (p,) = b.payments
    assert (p.payment_type, p.amount, p.method) == ("deposit", 135, "promptpay")
    assert p.gateway_ref.startswith("TEST-") and len(p.gateway_ref) == 15
    with pytest.raises(RuleError):  # paying twice
        payments.pay_deposit_test(world.db, b, policy_accepted=True)
