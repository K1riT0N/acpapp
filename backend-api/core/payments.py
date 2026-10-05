"""All payment code lives here, so the test-mode version can be swapped for a real gateway later.

Today: the "Simulate successful payment" button calls pay_deposit_test(), which pretends PromptPay
reported a successful payment. Later: the gateway (for example Omise or Stripe) calls our webhook
route after a real payment, and that route calls confirm_deposit() with the gateway's reference.
The browser is never trusted to say "I paid".
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import notify, timeutil
from core.errors import RuleError
from core.ids import new_id, random_code
from core.status import hold_active
from models import Booking, Payment


def test_gateway_ref() -> str:
    """Looks like a gateway reference: TEST- plus 10 characters."""
    return "TEST-" + random_code(10)


def confirm_deposit(db: Session, booking_id: str, gateway_ref: str, method: str = "promptpay",
                    policy_accepted_at=None) -> Booking:
    """Record the deposit, confirm the booking and create its messages, all in one transaction."""
    # Lock the booking row so two payment calls at the same moment can't both confirm it.
    # populate_existing re-reads the row after the lock, instead of reusing an older copy from this session.
    b = db.scalar(select(Booking).where(Booking.booking_id == booking_id)
                  .with_for_update().execution_options(populate_existing=True))
    now = timeutil.now()
    if b.status != "pending_payment":
        raise RuleError("This booking doesn't need a deposit any more.", 409)
    if not hold_active(b, now):
        raise RuleError("Your hold on this time ran out. Pick a time again.", 409)

    db.add(Payment(payment_id=new_id("pay"), booking_id=b.booking_id, subscription_id=None, payment_type="deposit",
                   amount=b.deposit_amount, method=method, status="paid", gateway_ref=gateway_ref, paid_at=now))
    b.status = "confirmed"
    if policy_accepted_at is not None:
        b.policy_accepted_at = policy_accepted_at
    notify.on_deposit_paid(db, b)
    db.commit()
    return b


def pay_deposit_test(db: Session, b: Booking, policy_accepted: bool) -> Booking:
    """Test mode: the customer pressed "Simulate successful payment"."""
    if not policy_accepted:
        raise RuleError("Tick the deposit policy first.")
    # The customer agreed to the no-refund policy just now; keep that moment as proof
    return confirm_deposit(db, b.booking_id, test_gateway_ref(), policy_accepted_at=timeutil.now())
