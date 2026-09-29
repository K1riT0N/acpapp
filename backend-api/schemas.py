"""Pydantic models: the shape of the JSON that goes in and out of the API.

Request fields that people type are plain strings with defaults, so that an empty form reaches our
own checks in core/ and gets the prototype's friendly message instead of a technical 422 error.
Clock times go out as "HH:MM", like the prototype.
"""
from datetime import time
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
