"""The 9 tables of Nadd, written as SQLAlchemy 2.0 classes.

Conventions used in every table:
- Primary keys are short strings (VARCHAR(40)) so the demo IDs from nadd_seed_data.json,
  such as "shop_baansuay", stay the same. New rows get a prefix plus a random part, like "b_x7k2...".
- Money is whole baht (INTEGER). Calendar days are DATE, clock times are TIME,
  and moments in time are TIMESTAMPTZ (timestamp with time zone).
- Columns that only allow a few values (role, status, ...) are plain strings with a CHECK
  constraint listing the allowed values, so the database itself rejects a typo like "confimed".

app.py calls Base.metadata.create_all() at start-up, which creates any table that doesn't exist yet.
"""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

ID_LEN = 40

ROLES = ("customer", "shop_owner")
BOOKING_STATUSES = ("pending_payment", "confirmed", "completed", "cancelled", "no_show", "expired")
PAYMENT_TYPES = ("deposit", "remaining", "subscription")
PAYMENT_METHODS = ("promptpay", "cash", "card")
PAYMENT_STATUSES = ("paid",)
NOTIFICATION_TYPES = ("new_booking", "booking_confirmed", "reminder", "cancellation", "no_show", "plan")
CHANNELS = ("line", "email")
NOTIFICATION_STATUSES = ("pending", "sent", "cancelled")
SUBSCRIPTION_STATUSES = ("active", "ended", "expired")


def one_of(column: str, values: tuple) -> str:
    """SQL for a CHECK constraint, e.g. role IN ('customer', 'shop_owner')."""
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def pk() -> Mapped[str]:
    return mapped_column(String(ID_LEN), primary_key=True)


def fk(target: str, nullable: bool = False) -> Mapped:
    return mapped_column(String(ID_LEN), ForeignKey(target), nullable=nullable, index=True)


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(one_of("role", ROLES), name="ck_users_role"),)

    user_id: Mapped[str] = pk()
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    line_user_id: Mapped[Optional[str]] = mapped_column(String(64))  # NULL = messages go by email
    demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = created_at()

    shop: Mapped[Optional["Shop"]] = relationship(back_populates="owner", uselist=False)


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        CheckConstraint("deposit_percent BETWEEN 0 AND 100", name="ck_shops_deposit_percent"),
    )

    shop_id: Mapped[str] = pk()
    # unique: the app assumes one shop per owner account, as in the prototype
    owner_id: Mapped[str] = mapped_column(String(ID_LEN), ForeignKey("users.user_id"), nullable=False, unique=True)
    shop_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deposit_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = created_at()

    owner: Mapped["User"] = relationship(back_populates="shop")
    services: Mapped[list["Service"]] = relationship(back_populates="shop")
    hours: Mapped[list["BusinessHours"]] = relationship(back_populates="shop")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="shop")


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_services_price"),
        CheckConstraint("duration_min > 0", name="ck_services_duration"),
    )

    service_id: Mapped[str] = pk()
    shop_id: Mapped[str] = fk("shops.shop_id")
    service_name: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    shop: Mapped["Shop"] = relationship(back_populates="services")


class BusinessHours(Base):
    """One row per open day. No row for a day means the shop is closed that day."""

    __tablename__ = "business_hours"
    __table_args__ = (
        UniqueConstraint("shop_id", "day_of_week", name="uq_business_hours_shop_day"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_business_hours_day"),  # 0 = Sunday
        CheckConstraint("close_time > open_time", name="ck_business_hours_times"),
        CheckConstraint("max_per_slot BETWEEN 1 AND 50", name="ck_business_hours_cap"),
    )

    hours_id: Mapped[str] = pk()
    shop_id: Mapped[str] = fk("shops.shop_id")
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    max_per_slot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    shop: Mapped["Shop"] = relationship(back_populates="hours")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(one_of("status", BOOKING_STATUSES), name="ck_bookings_status"),
        CheckConstraint("end_time > start_time", name="ck_bookings_times"),
        CheckConstraint(
            "deposit_amount >= 0 AND remaining_amount >= 0 AND deposit_amount + remaining_amount = total_price",
            name="ck_bookings_money",
        ),
        # The slot and monthly-limit checks look up one shop's bookings on one day or month
        Index("ix_bookings_shop_date", "shop_id", "booking_date"),
    )

    booking_id: Mapped[str] = pk()
    ref: Mapped[str] = mapped_column(String(5), nullable=False, unique=True)  # shown on the ticket, e.g. K7Q2M
    customer_id: Mapped[str] = fk("users.user_id")
    shop_id: Mapped[str] = mapped_column(String(ID_LEN), ForeignKey("shops.shop_id"), nullable=False)
    service_id: Mapped[str] = mapped_column(String(ID_LEN), ForeignKey("services.service_id"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)  # shop-local (Bangkok) day
    start_time: Mapped[time] = mapped_column(Time, nullable=False)  # shop-local clock time
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_payment")
    # Price, deposit and remaining are copied here when the booking is made,
    # so later price changes don't change what this customer agreed to pay.
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    hold_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    policy_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at()
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    customer: Mapped["User"] = relationship()
    shop: Mapped["Shop"] = relationship()
    service: Mapped["Service"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")


class Payment(Base):
    """A payment belongs to either a booking (deposit, remaining) or a subscription, never both."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("(booking_id IS NULL) <> (subscription_id IS NULL)", name="ck_payments_one_owner"),
        CheckConstraint(one_of("payment_type", PAYMENT_TYPES), name="ck_payments_type"),
        CheckConstraint(one_of("method", PAYMENT_METHODS), name="ck_payments_method"),
        CheckConstraint(one_of("status", PAYMENT_STATUSES), name="ck_payments_status"),
        CheckConstraint("amount >= 0", name="ck_payments_amount"),
    )

    payment_id: Mapped[str] = pk()
    booking_id: Mapped[Optional[str]] = fk("bookings.booking_id", nullable=True)
    subscription_id: Mapped[Optional[str]] = fk("subscriptions.subscription_id", nullable=True)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="paid")
    gateway_ref: Mapped[Optional[str]] = mapped_column(String(64))  # NULL for cash
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    booking: Mapped[Optional["Booking"]] = relationship(back_populates="payments")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="payments")


class Notification(Base):
    """A LINE or email message. The app shows it on the Messages page instead of really sending it."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(one_of("type", NOTIFICATION_TYPES), name="ck_notifications_type"),
        CheckConstraint(one_of("channel", CHANNELS), name="ck_notifications_channel"),
        CheckConstraint(one_of("status", NOTIFICATION_STATUSES), name="ck_notifications_status"),
        # The scheduler asks "which pending messages are due?" every 30 seconds
        Index("ix_notifications_status_scheduled", "status", "scheduled_at"),
    )

    notification_id: Mapped[str] = pk()
    booking_id: Mapped[Optional[str]] = fk("bookings.booking_id", nullable=True)  # NULL for plan messages
    recipient_id: Mapped[str] = fk("users.user_id")
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class Plan(Base):
    __tablename__ = "plans"

    plan_id: Mapped[str] = mapped_column(String(20), primary_key=True)  # "free" or "pro"
    plan_name: Mapped[str] = mapped_column(String(40), nullable=False)
    monthly_price: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_limit: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(one_of("status", SUBSCRIPTION_STATUSES), name="ck_subscriptions_status"),
    )

    subscription_id: Mapped[str] = pk()
    shop_id: Mapped[str] = fk("shops.shop_id")
    plan_id: Mapped[str] = mapped_column(String(20), ForeignKey("plans.plan_id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)  # NULL = no end (Free)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    shop: Mapped["Shop"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")
