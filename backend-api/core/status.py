"""What a booking's status means for slots and limits (the prototype's holdActive, occupies, counts).

A pending_payment booking whose hold has run out is treated as gone *straight away*, by comparing
hold_expires_at with the clock. So the rules stay correct even if the background job that sets
status = "expired" hasn't run yet.
"""
from datetime import datetime

from models import Booking

HOLD_MINUTES = 15


def hold_active(b: Booking, now: datetime) -> bool:
    """Waiting for the deposit, and the 15 minutes aren't over yet."""
    return b.status == "pending_payment" and b.hold_expires_at > now


def occupies(b: Booking, now: datetime) -> bool:
    """Takes up a place in its time slot."""
    return b.status in ("confirmed", "completed", "no_show") or hold_active(b, now)


def counts_toward_limit(b: Booking, now: datetime) -> bool:
    """Counts toward the shop's monthly booking limit: everything except expired holds."""
    if b.status == "expired":
        return False
    return not (b.status == "pending_payment" and not hold_active(b, now))
