"""Pydantic models: the shape of the JSON that goes in and out of the API.

Request fields that people type are plain strings with defaults, so that an empty form reaches our
own checks in core/ and gets the prototype's friendly message instead of a technical 422 error.
Clock times go out as "HH:MM", like the prototype.
"""
from datetime import date, datetime, time
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, PlainSerializer

HHMM = Annotated[time, PlainSerializer(lambda t: t.strftime("%H:%M"), return_type=str)]


class ORMModel(BaseModel):
    """Lets a response model be built straight from a SQLAlchemy object."""
    model_config = ConfigDict(from_attributes=True)


# ---------- auth ----------

class RegisterIn(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    password: str = ""
    role: str = "customer"
    line: bool = True
    shop_name: str = ""
    category: str = ""
    address: str = ""


class LoginIn(BaseModel):
    email: str = ""
    password: str = ""


class UserOut(ORMModel):
    user_id: str
    full_name: str
    email: str
    phone: str
    role: str
    line_user_id: Optional[str]
    shop_id: Optional[str] = None


class AuthOut(BaseModel):
    token: str
    user: UserOut


class DemoAccountOut(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: str
    shop_name: Optional[str] = None
    plan_name: Optional[str] = None


# ---------- plans, shops, services, hours ----------

class PlanOut(ORMModel):
    plan_id: str
    plan_name: str
    monthly_price: int
    booking_limit: Optional[int]


class ServiceOut(ORMModel):
    service_id: str
    shop_id: str
    service_name: str
    price: int
    duration_min: int
    is_active: bool


class HoursOut(ORMModel):
    day_of_week: int
    open_time: HHMM
    close_time: HHMM
    max_per_slot: int


class ShopOut(ORMModel):
    shop_id: str
    owner_id: str
    shop_name: str
    category: str
    address: str
    phone: str
    description: str
    deposit_percent: int
    plan_name: str
    services: list[ServiceOut]
    hours: list[HoursOut]


class ServiceIn(BaseModel):
    service_name: Optional[str] = None
    price: Optional[float] = None
    duration_min: Optional[int] = None
    is_active: Optional[bool] = None


class ShopUpdateIn(BaseModel):
    shop_name: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    deposit_percent: Optional[float] = None


class HoursDayIn(BaseModel):
    day_of_week: int
    open: bool
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    max_per_slot: Optional[float] = None


# ---------- calendar and slots ----------

class CalendarDayOut(BaseModel):
    date: date
    open: bool
    has_free_slot: bool


class SlotOut(BaseModel):
    time: HHMM
    used: int
    cap: int
    full: bool
    past: bool


class LimitOut(BaseModel):
    plan: str
    used: int
    limit: Optional[int]
    reached: bool


class SlotsOut(BaseModel):
    closed: bool
    slots: list[SlotOut]
    limit: LimitOut


class SampleSlotOut(BaseModel):
    shop_id: str
    shop_name: str
    service_id: str
    service_name: str
    date: date
    time: HHMM
    deposit: int


# ---------- bookings, payments, messages ----------

class BookingIn(BaseModel):
    shop_id: str
    service_id: str
    booking_date: date
    start_time: time


class PayDepositIn(BaseModel):
    policy_accepted: bool = False


class BookingOut(ORMModel):
    booking_id: str
    ref: str
    customer_id: str
    shop_id: str
    service_id: str
    booking_date: date
    start_time: HHMM
    end_time: HHMM
    status: str
    hold_active: bool = False  # worked out from hold_expires_at, so it's right even before the job runs
    total_price: int
    deposit_amount: int
    remaining_amount: int
    hold_expires_at: datetime
    policy_accepted_at: Optional[datetime]
    created_at: datetime
    cancelled_at: Optional[datetime]
    # names for the ticket, so the page doesn't need extra requests
    shop_name: str = ""
    service_name: str = ""
    customer_name: str = ""
    customer_phone: str = ""


class PaymentOut(ORMModel):
    payment_id: str
    payment_type: str
    amount: int
    method: str
    status: str
    gateway_ref: Optional[str]
    paid_at: datetime


class NotificationOut(ORMModel):
    notification_id: str
    booking_id: Optional[str]
    type: str
    channel: str
    title: str
    body: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    status: str
    read: bool


class BookingShopOut(BaseModel):
    shop_id: str
    shop_name: str
    owner_id: str
    phone: str
    deposit_percent: int


class BookingDetailOut(BaseModel):
    booking: BookingOut
    shop: BookingShopOut
    viewer: str  # "customer" or "owner"
    payments: list[PaymentOut]
    notifications: list[NotificationOut]  # only the viewer's own messages about this booking


class InboxOut(BaseModel):
    sent: list[NotificationOut]
    scheduled: list[NotificationOut]
    unread_count: int


class CountOut(BaseModel):
    count: int


# ---------- owner: dashboard, bookings, plan ----------

class DayLoadOut(BaseModel):
    date: date
    count: int
    capacity: Optional[int]  # None = closed


class DashboardOut(BaseModel):
    shop_id: str
    shop_name: str
    plan: PlanOut
    usage: LimitOut
    days: list[DayLoadOut]
    date: date
    queue: list[BookingOut]
    alerts: list[NotificationOut]
    pending_reminders: int


class AdminMonthOut(BaseModel):
    month: str
    users: int
    bookings: int
    transactions: int
    transaction_volume: int


class AdminDashboardOut(BaseModel):
    active_users: int
    total_shops: int
    transactions_this_month: int
    transaction_volume_this_month: int
    projected_mrr: int
    projected_arr: int
    months: list[AdminMonthOut]


class OwnerBookingsOut(BaseModel):
    shop_name: str
    filter: str
    rows: list[BookingOut]
    counts: dict[str, int]


class CompleteIn(BaseModel):
    method: str = ""


class SubscriptionOut(ORMModel):
    subscription_id: str
    plan_id: str
    start_date: date
    end_date: Optional[date]
    status: str


class PlanPaymentOut(PaymentOut):
    plan_name: str = ""


class PlanPageOut(BaseModel):
    plan: PlanOut
    subscription: Optional[SubscriptionOut]
    usage: LimitOut
    plans: list[PlanOut]
    payments: list[PlanPaymentOut]
