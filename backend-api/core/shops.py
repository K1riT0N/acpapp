"""Shops, services and opening hours: searching, and the owner's changes. Wording follows the prototype."""
from datetime import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import NotFound, RuleError
from core.ids import new_id
from core.timeutil import DAY_NAMES
from models import BusinessHours, Service, Shop

CATEGORIES = ["Hair salon", "Beauty and nails", "Massage and spa", "Car care", "Clinic", "Pet grooming", "Other"]
DURATIONS = [15, 30, 45, 60, 75, 90, 120, 150, 180, 240]


# ---------- reading ----------

def active_services(shop: Shop) -> list[Service]:
    """Services customers can book, cheapest first (the prototype's servicesOf(shop, true))."""
    return sorted((s for s in shop.services if s.is_active), key=lambda s: s.price)


def search_shops(db: Session, q: str = "", category: str = "") -> list[Shop]:
    """All shops, A to Z, filtered by category and by words in the name, category, address or service names."""
    q = q.strip().lower()
    result = []
    for shop in db.scalars(select(Shop).order_by(Shop.shop_name)):
        if category and shop.category != category:
            continue
        haystack = " ".join([shop.shop_name, shop.category, shop.address] +
                            [s.service_name for s in active_services(shop)]).lower()
        if q and q not in haystack:
            continue
        result.append(shop)
    return result


def get_shop(db: Session, shop_id: str) -> Shop:
    shop = db.get(Shop, shop_id)
    if shop is None:
        raise NotFound("That shop isn't listed.")
    return shop


def shop_of_owner(db: Session, owner_id: str) -> Shop:
    shop = db.scalar(select(Shop).where(Shop.owner_id == owner_id))
    if shop is None:
        raise NotFound("This account doesn't have a shop yet.")
    return shop


# ---------- services ----------

def _service_errors(name: Optional[str], price: Optional[float], duration: Optional[int]) -> list[str]:
    errors = []
    if not (name or "").strip():
        errors.append("Enter a service name.")
    if price is None or price < 0 or price != int(price):
        errors.append("Enter a price of 0 baht or more.")
    if duration not in DURATIONS:
        errors.append("Pick a duration.")
    return errors


def add_service(db: Session, shop: Shop, name: Optional[str], price: Optional[float], duration: Optional[int]) -> Service:
    errors = _service_errors(name, price, duration)
    if errors:
        raise RuleError(" ".join(errors))
    service = Service(service_id=new_id("svc"), shop_id=shop.shop_id, service_name=name.strip(),
                      price=int(price), duration_min=duration, is_active=True)
    db.add(service)
    db.commit()
    return service


def update_service(db: Session, shop: Shop, service_id: str, changes: dict) -> Service:
    """Change any of service_name, price, duration_min, is_active. Only the fields that were sent change."""
    service = db.get(Service, service_id)
    if service is None or service.shop_id != shop.shop_id:
        raise NotFound("We couldn't find that service.")
    name = changes.get("service_name", service.service_name)
    price = changes.get("price", service.price)
    duration = changes.get("duration_min", service.duration_min)
    errors = _service_errors(name, price, duration)
    if errors:
        raise RuleError(" ".join(errors))
    service.service_name, service.price, service.duration_min = name.strip(), int(price), duration
    if changes.get("is_active") is not None:
        service.is_active = changes["is_active"]
    db.commit()
    return service


# ---------- shop details and opening hours ----------

def update_shop(db: Session, shop: Shop, changes: dict) -> Shop:
    errors = []
    if "shop_name" in changes and not (changes["shop_name"] or "").strip():
        errors.append("Enter the shop name.")
    if "deposit_percent" in changes:
        dep = changes["deposit_percent"]
        if dep is None or not 0 <= dep <= 100 or dep != int(dep):
            errors.append("Set the deposit between 0 and 100 percent.")
    if errors:
        raise RuleError(" ".join(errors))

    for field in ("shop_name", "category", "address", "phone", "description"):
        if changes.get(field) is not None:
            setattr(shop, field, changes[field].strip())
    if not shop.category:
        shop.category = CATEGORIES[0]
    if "deposit_percent" in changes:
        shop.deposit_percent = int(changes["deposit_percent"])
    db.commit()
    return shop


def _parse_time(value: Optional[str]) -> Optional[time]:
    try:
        return time.fromisoformat(value) if value else None
    except ValueError:
        return None


def set_hours(db: Session, shop: Shop, days: list[dict]) -> list[BusinessHours]:
    """Replace the week's opening hours. A closed day has no row, so closing a day deletes its row."""
    errors, wanted = [], {}
    for day in sorted(days, key=lambda d: (d["day_of_week"] + 6) % 7):  # check Monday first, like the form
        dow = day["day_of_week"]
        if not 0 <= dow <= 6 or not day.get("open"):
            continue
        opens, closes, cap = _parse_time(day.get("open_time")), _parse_time(day.get("close_time")), day.get("max_per_slot")
        if opens is None or closes is None or opens >= closes:
            errors.append(f"{DAY_NAMES[dow]}: the closing time has to be after the opening time.")
        if cap is None or not 1 <= cap <= 50 or cap != int(cap):
            errors.append(f"{DAY_NAMES[dow]}: customers at once has to be a whole number from 1 to 50.")
        wanted[dow] = (opens, closes, cap)
    if errors:
        raise RuleError(" ".join(errors))

    existing = {h.day_of_week: h for h in shop.hours}
    for dow, row in existing.items():
        if dow not in wanted:
            db.delete(row)
    for dow, (opens, closes, cap) in wanted.items():
        row = existing.get(dow)
        if row is None:
            row = BusinessHours(hours_id=f"bh_{shop.shop_id}_{dow}", shop_id=shop.shop_id, day_of_week=dow)
            db.add(row)
        row.open_time, row.close_time, row.max_per_slot = opens, closes, int(cap)
    db.commit()
    db.expire(shop, ["hours"])  # so shop.hours is read again from the database next time
    return db.scalars(select(BusinessHours).where(BusinessHours.shop_id == shop.shop_id)
                      .order_by(BusinessHours.day_of_week)).all()
