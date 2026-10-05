"""/bookings: making a booking, paying the deposit (test mode) and viewing a booking.

(Step 9 adds /bookings/me and cancelling.)
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import bookings as booking_rules
from core import timeutil
from core.payments import pay_deposit_test
from core.status import hold_active
from database import get_db
from models import Booking, Notification, Payment, User
from schemas import BookingDetailOut, BookingIn, BookingOut, BookingShopOut, PayDepositIn
from security import get_current_user, require_role

router = APIRouter()
customer_only = require_role("customer")


def booking_out(b: Booking) -> BookingOut:
    out = BookingOut.model_validate(b)
    out.hold_active = hold_active(b, timeutil.now())
    out.shop_name, out.service_name = b.shop.shop_name, b.service.service_name
    out.customer_name, out.customer_phone = b.customer.full_name, b.customer.phone
    return out


def detail_out(db: Session, b: Booking, viewer: str, user: User) -> BookingDetailOut:
    payments = db.scalars(select(Payment).where(Payment.booking_id == b.booking_id).order_by(Payment.paid_at)).all()
    messages = db.scalars(select(Notification).where(Notification.booking_id == b.booking_id,
                                                     Notification.recipient_id == user.user_id)
                          .order_by(Notification.scheduled_at)).all()
    shop = b.shop
    return BookingDetailOut(
        booking=booking_out(b),
        shop=BookingShopOut(shop_id=shop.shop_id, shop_name=shop.shop_name, owner_id=shop.owner_id,
                            phone=shop.phone, deposit_percent=shop.deposit_percent),
        viewer=viewer,
        payments=payments,
        notifications=messages,
    )


@router.post("", response_model=BookingOut, status_code=201)
def create(body: BookingIn, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Hold the time for 15 minutes. 409 if the time was just taken or the shop's monthly limit is reached."""
    b = booking_rules.create_booking(db, user, body.shop_id, body.service_id, body.booking_date, body.start_time)
    return booking_out(b)


@router.get("/{booking_id}", response_model=BookingDetailOut)
def get(booking_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """For the booking's customer or the shop's owner only."""
    b, viewer = booking_rules.get_for_viewer(db, booking_id, user)
    return detail_out(db, b, viewer, user)


@router.post("/{booking_id}/pay-deposit", response_model=BookingDetailOut)
def pay_deposit(booking_id: str, body: PayDepositIn, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """Test mode: acts as if PromptPay reported a successful payment. Needs policy_accepted: true."""
    b = booking_rules.get_customers_booking(db, booking_id, user)
    b = pay_deposit_test(db, b, body.policy_accepted)
    return detail_out(db, b, "customer", user)


@router.post("/{booking_id}/release", response_model=BookingOut)
def release(booking_id: str, user: User = Depends(customer_only), db: Session = Depends(get_db)):
    """The customer gives the held time back before paying."""
    b = booking_rules.get_customers_booking(db, booking_id, user)
    return booking_out(booking_rules.release_hold(db, b))
