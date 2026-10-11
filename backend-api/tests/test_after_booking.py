"""Tests for what happens after the deposit: messages, cancel, complete, no-show, and plans."""
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select

from core import bookings, notify, payments, plans, timeutil
from core.bookings import create_booking
from core.errors import RuleError
from core.limits import plan_of
from models import Notification, Payment, Subscription

FRIDAY = date(2026, 9, 25)  # two days after the frozen "now" (Wed 23 Sep, 09:00)


def confirmed(w, customer, day=FRIDAY, at=time(11)):
    b = create_booking(w.db, customer, "shop_t", w.cut.service_id, day, at)
    payments.pay_deposit_test(w.db, b, policy_accepted=True)
    return b


def messages(w, b):
    return w.db.scalars(select(Notification).where(Notification.booking_id == b.booking_id)
                        .order_by(Notification.scheduled_at, Notification.title)).all()


# ---------- messages ----------

def test_deposit_creates_the_five_messages(world):
    b = confirmed(world, world.ploy)
    got = {(n.recipient_id == world.owner.user_id, n.type, n.status, n.title, n.body) for n in messages(world, b)}
    w = "Fri 25 Sep at 11:00"
    assert got == {
        (True, "new_booking", "sent", "New booking: Haircut",
         f"Ploy Srisuk booked Haircut on {w}. Deposit ฿135 received."),
        (False, "booking_confirmed", "sent", "Booking confirmed at Test Salon",
         f"Haircut on {w}. Ref {b.ref}. Pay ฿315 at the shop."),
        (False, "reminder", "pending", "Reminder: your appointment at Test Salon", f"Haircut on {w}. Ref {b.ref}."),
        (True, "reminder", "pending", "Upcoming: Ploy Srisuk at 11:00", f"Haircut on {w}."),
        (False, "reminder", "pending", "Starting in 2 hours at Test Salon", f"Haircut on {w}. Ref {b.ref}."),
    }
    when = {n.title: n.scheduled_at for n in messages(world, b)}
    start = datetime(2026, 9, 25, 11, tzinfo=timeutil.BANGKOK)
    assert when["Reminder: your appointment at Test Salon"] == start - timedelta(hours=24)
    assert when["Starting in 2 hours at Test Salon"] == start - timedelta(hours=2)


def test_reminders_in_the_past_are_skipped(world):
    b = confirmed(world, world.ploy, day=date(2026, 9, 23), at=time(12))  # today at 12:00, it's 09:00 now
    titles = {n.title for n in messages(world, b)}
    assert "Starting in 2 hours at Test Salon" in titles  # 10:00 is still ahead
    assert not any(t.startswith("Reminder:") or t.startswith("Upcoming:") for t in titles)


def test_channel_is_line_or_email(world):
    b = confirmed(world, world.ton)  # Ton has no LINE account
    assert {n.channel for n in messages(world, b) if n.recipient_id == world.ton.user_id} == {"email"}
    assert {n.channel for n in messages(world, b) if n.recipient_id == world.owner.user_id} == {"line"}


def test_scheduler_sends_messages_when_due(world, clock):
    b = confirmed(world, world.ploy)
    assert notify.send_due(world.db) == 0
    clock.set(datetime(2026, 9, 24, 11, 0, tzinfo=timeutil.BANGKOK))  # 24 h before
    assert notify.send_due(world.db) == 2
    world.db.commit()
    pending = [n.title for n in messages(world, b) if n.status == "pending"]
    assert pending == ["Starting in 2 hours at Test Salon"]


# ---------- cancel ----------

def test_customer_cancels_a_future_booking(world):
    b = confirmed(world, world.ploy)
    bookings.cancel_by_customer(world.db, b.booking_id)
    assert b.status == "cancelled" and b.cancelled_at is not None
    msgs = messages(world, b)
    assert not [n for n in msgs if n.status == "pending"]  # reminders called off
    assert {n.title for n in msgs if n.type == "cancellation"} == {
        "Cancelled: Ploy Srisuk at 11:00", "Booking cancelled at Test Salon"}
    owner_msg = next(n for n in msgs if n.title.startswith("Cancelled:"))
    assert owner_msg.body == ("Haircut on Fri 25 Sep at 11:00 was cancelled. "
                              "The ฿135 deposit is kept, and the time is free again.")
    # No refund: the only payment is still the deposit
    assert [p.payment_type for p in world.db.scalars(select(Payment))] == ["deposit"]


def test_cannot_cancel_after_the_start_or_twice(world, clock):
    b = confirmed(world, world.ploy)
    clock.set(datetime(2026, 9, 25, 11, 0, tzinfo=timeutil.BANGKOK))
    with pytest.raises(RuleError, match="already started"):
        bookings.cancel_by_customer(world.db, b.booking_id)
    b2 = confirmed(world, world.ton, day=date(2026, 9, 26))
    bookings.cancel_by_customer(world.db, b2.booking_id)
    with pytest.raises(RuleError):
        bookings.cancel_by_customer(world.db, b2.booking_id)


# ---------- complete and no-show ----------

def test_complete_only_on_the_day_and_records_the_rest(world, clock):
    b = confirmed(world, world.ploy)
    with pytest.raises(RuleError, match="on the day"):
        bookings.complete(world.db, b.booking_id, "cash")
    clock.set(datetime(2026, 9, 25, 11, 50, tzinfo=timeutil.BANGKOK))
    with pytest.raises(RuleError, match="cash, PromptPay or card"):
        bookings.complete(world.db, b.booking_id, "bitcoin")
    bookings.complete(world.db, b.booking_id, "cash")
    assert b.status == "completed"
    rest = world.db.scalar(select(Payment).where(Payment.payment_type == "remaining"))
    assert (rest.amount, rest.method, rest.gateway_ref) == (315, "cash", None)
    assert not [n for n in messages(world, b) if n.status == "pending"]


def test_card_payment_gets_a_reference(world, clock):
    b = confirmed(world, world.ploy)
    clock.set(datetime(2026, 9, 25, 12, 0, tzinfo=timeutil.BANGKOK))
    bookings.complete(world.db, b.booking_id, "card")
    rest = world.db.scalar(select(Payment).where(Payment.payment_type == "remaining"))
    assert rest.gateway_ref.startswith("TEST-")


def test_no_show_keeps_the_deposit_and_tells_the_customer(world, clock):
    b = confirmed(world, world.ploy)
    clock.set(datetime(2026, 9, 25, 12, 0, tzinfo=timeutil.BANGKOK))
    bookings.mark_no_show(world.db, b.booking_id)
    assert b.status == "no_show"
    msg = next(n for n in messages(world, b) if n.type == "no_show")
    assert msg.title == "Missed appointment at Test Salon"
    assert msg.body == ("Haircut on Fri 25 Sep at 11:00 was marked as a no-show. "
                        "The ฿135 deposit is kept by the shop.")
    with pytest.raises(RuleError):  # already handled
        bookings.complete(world.db, b.booking_id, "cash")


# ---------- plans ----------

def test_upgrade_to_pro_and_back_to_free(world, clock):
    assert plan_of(world.db, "shop_t")[1].plan_id == "free"
    pro = plans.upgrade_to_pro(world.db, world.shop, world.owner)
    assert (pro.start_date, pro.end_date) == (date(2026, 9, 23), date(2026, 10, 23))
    assert plan_of(world.db, "shop_t")[1].plan_id == "pro"
    assert world.db.get(Subscription, "sub_t_free").status == "ended"
    (paid,) = plans.plan_payments(world.db, world.shop)
    assert (paid.amount, paid.payment_type, paid.booking_id) == (299, "subscription", None)
    msg = world.db.scalar(select(Notification).where(Notification.type == "plan"))
    assert (msg.title, msg.body, msg.status) == ("Pro plan is active", "Bookings are unlimited until Fri 23 Oct.", "sent")
    with pytest.raises(RuleError, match="already on Pro"):
        plans.upgrade_to_pro(world.db, world.shop, world.owner)

    plans.switch_to_free(world.db, world.shop)
    assert plan_of(world.db, "shop_t")[1].plan_id == "free"
    actives = world.db.scalars(select(Subscription).where(Subscription.status == "active")).all()
    assert len(actives) == 1  # always exactly one current subscription


def test_finished_pro_month_expires_to_free(world, clock):
    plans.upgrade_to_pro(world.db, world.shop, world.owner)
    clock.set(datetime(2026, 10, 23, 23, 0, tzinfo=timeutil.BANGKOK))  # last day of Pro: still Pro
    assert plans.expire_pro_subscriptions(world.db) == 0
    assert plan_of(world.db, "shop_t")[1].plan_id == "pro"
    clock.set(datetime(2026, 10, 24, 0, 1, tzinfo=timeutil.BANGKOK))
    assert plans.expire_pro_subscriptions(world.db) == 1
    world.db.commit()
    assert plan_of(world.db, "shop_t")[1].plan_id == "free"
    statuses = sorted(s.status for s in world.db.scalars(select(Subscription)))
    assert statuses == ["active", "ended", "expired"]


@pytest.mark.parametrize("start, months, end", [
    (date(2026, 9, 23), 1, date(2026, 10, 23)),
    (date(2026, 1, 31), 1, date(2026, 2, 28)),
    (date(2028, 1, 31), 1, date(2028, 2, 29)),  # leap year
    (date(2026, 12, 15), 1, date(2027, 1, 15)),
])
def test_add_months(start, months, end):
    assert timeutil.add_months(start, months) == end
