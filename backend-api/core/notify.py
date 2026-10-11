"""LINE and email messages: creating them with the right wording, and "sending" them.

Nothing leaves the server yet. send_line() and send_email() only write a log line; the app shows the
messages on the Messages page. To go live, replace their bodies with a call to the LINE Messaging API
(push message to user.line_user_id) and to an email service. Nothing else has to change.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import timeutil
from core.ids import new_id
from models import Booking, Notification, User

log = logging.getLogger("nadd.notify")


# ---------- the channels ----------

def send_line(user: User, n: Notification) -> None:
    """Later: POST https://api.line.me/v2/bot/message/push with the channel access token."""
    log.info("LINE to %s (%s): %s | %s", user.full_name, user.line_user_id, n.title, n.body)


def send_email(user: User, n: Notification) -> None:
    """Later: send through an email service such as SMTP or SendGrid."""
    log.info("Email to %s <%s>: %s | %s", user.full_name, user.email, n.title, n.body)


def deliver(db: Session, n: Notification, now: Optional[datetime] = None) -> None:
    """Send one message on its channel and mark it sent."""
    user = db.get(User, n.recipient_id)
    (send_line if n.channel == "line" else send_email)(user, n)
    n.status = "sent"
    n.sent_at = now or timeutil.now()


# ---------- creating messages ----------

def create(db: Session, recipient: User, booking_id: Optional[str], type_: str, title: str, body: str,
           scheduled_at: Optional[datetime] = None) -> Notification:
    """Add a message. With no scheduled_at it is sent right away; otherwise the scheduler sends it later."""
    now = timeutil.now()
    n = Notification(
        notification_id=new_id("n"),
        booking_id=booking_id,
        recipient_id=recipient.user_id,
        type=type_,
        channel="line" if recipient.line_user_id else "email",
        title=title,
        body=body,
        scheduled_at=scheduled_at or now,
        sent_at=None,
        status="pending",
        read=False,
    )
    db.add(n)
    if scheduled_at is None:
        deliver(db, n, now)
    return n


def when(b: Booking) -> str:
    """'Thu 24 Sep at 11:00'"""
    return f"{timeutil.fmt_date(b.booking_date)} at {b.start_time:%H:%M}"


def booking_start(b: Booking) -> datetime:
    return datetime.combine(b.booking_date, b.start_time, tzinfo=timeutil.BANGKOK)


def on_deposit_paid(db: Session, b: Booking) -> None:
    """The five messages from section 5: two now, and reminders 24 h and 2 h before (if still ahead)."""
    owner, customer = b.shop.owner, b.customer
    svc, shop = b.service.service_name, b.shop.shop_name
    w = when(b)
    create(db, owner, b.booking_id, "new_booking", f"New booking: {svc}",
           f"{customer.full_name} booked {svc} on {w}. Deposit {timeutil.baht(b.deposit_amount)} received.")
    create(db, customer, b.booking_id, "booking_confirmed", f"Booking confirmed at {shop}",
           f"{svc} on {w}. Ref {b.ref}. Pay {timeutil.baht(b.remaining_amount)} at the shop.")

    now, start = timeutil.now(), booking_start(b)
    r24, r2 = start - timedelta(hours=24), start - timedelta(hours=2)
    if r24 > now:
        create(db, customer, b.booking_id, "reminder", f"Reminder: your appointment at {shop}",
               f"{svc} on {w}. Ref {b.ref}.", r24)
        create(db, owner, b.booking_id, "reminder", f"Upcoming: {customer.full_name} at {b.start_time:%H:%M}",
               f"{svc} on {w}.", r24)
    if r2 > now:
        create(db, customer, b.booking_id, "reminder", f"Starting in 2 hours at {shop}",
               f"{svc} on {w}. Ref {b.ref}.", r2)


def cancel_pending(db: Session, booking_id: str) -> None:
    """A booking changed (cancelled, completed, no-show): its reminders shouldn't go out any more."""
    for n in db.scalars(select(Notification).where(Notification.booking_id == booking_id,
                                                   Notification.status == "pending")):
        n.status = "cancelled"


# ---------- sending what's due ----------

def send_due(db: Session) -> int:
    """Send every pending message whose time has come. Used by the scheduler every 30 seconds."""
    now = timeutil.now()
    due = db.scalars(select(Notification).where(Notification.status == "pending",
                                                Notification.scheduled_at <= now)).all()
    for n in due:
        deliver(db, n, now)
    return len(due)


def send_now_for(db: Session, user: User) -> int:
    """Demo shortcut: send all of this user's pending messages immediately."""
    now = timeutil.now()
    pending = db.scalars(select(Notification).where(Notification.recipient_id == user.user_id,
                                                    Notification.status == "pending")).all()
    for n in pending:
        deliver(db, n, now)
    db.commit()
    return len(pending)


def mark_all_read(db: Session, user: User) -> int:
    unread = db.scalars(select(Notification).where(Notification.recipient_id == user.user_id,
                                                   Notification.status == "sent",
                                                   Notification.read.is_(False))).all()
    for n in unread:
        n.read = True
    db.commit()
    return len(unread)


def on_cancelled(db: Session, b: Booking) -> None:
    """The customer cancelled: tell the shop the time is free again, and confirm to the customer."""
    owner, customer = b.shop.owner, b.customer
    svc, deposit = b.service.service_name, timeutil.baht(b.deposit_amount)
    create(db, owner, b.booking_id, "cancellation", f"Cancelled: {customer.full_name} at {b.start_time:%H:%M}",
           f"{svc} on {when(b)} was cancelled. The {deposit} deposit is kept, and the time is free again.")
    create(db, customer, b.booking_id, "cancellation", f"Booking cancelled at {b.shop.shop_name}",
           f"{svc} on {when(b)}. The {deposit} deposit is not refunded.")


def on_no_show(db: Session, b: Booking) -> None:
    create(db, b.customer, b.booking_id, "no_show", f"Missed appointment at {b.shop.shop_name}",
           f"{b.service.service_name} on {when(b)} was marked as a no-show. "
           f"The {timeutil.baht(b.deposit_amount)} deposit is kept by the shop.")


def on_pro_started(db: Session, owner: User, end) -> None:
    create(db, owner, None, "plan", "Pro plan is active", f"Bookings are unlimited until {timeutil.fmt_date(end)}.")
