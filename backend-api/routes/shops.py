"""/shops: the public shop directory and shop pages. No login needed."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core import shops as shop_rules
from core.bookings import sample_slot
from core.errors import RuleError
from core.limits import limit_info, plan_of
from core.slots import calendar, slots_for
from database import get_db
from models import Service, Shop
from schemas import CalendarDayOut, HoursOut, SampleSlotOut, ServiceOut, ShopOut, SlotsOut

router = APIRouter()


def shop_out(db: Session, shop: Shop) -> ShopOut:
    """A shop with its bookable services (cheapest first), opening hours and current plan name."""
    return ShopOut(
        shop_id=shop.shop_id,
        owner_id=shop.owner_id,
        shop_name=shop.shop_name,
        category=shop.category,
        address=shop.address,
        phone=shop.phone,
        description=shop.description,
        deposit_percent=shop.deposit_percent,
        plan_name=plan_of(db, shop.shop_id)[1].plan_name,
        services=[ServiceOut.model_validate(s) for s in shop_rules.active_services(shop)],
        hours=[HoursOut.model_validate(h) for h in sorted(shop.hours, key=lambda h: h.day_of_week)],
    )


@router.get("", response_model=list[ShopOut])
def list_shops(q: str = "", category: str = "", db: Session = Depends(get_db)):
    """Search matches the shop name, category, address and service names."""
    return [shop_out(db, s) for s in shop_rules.search_shops(db, q, category)]


@router.get("/sample-slot", response_model=Optional[SampleSlotOut])
def get_sample_slot(db: Session = Depends(get_db)):
    """A free afternoon time in the coming week, for the example ticket on the home page (null if none)."""
    return sample_slot(db)


def _bookable_service(db: Session, shop: Shop, service_id: str) -> Service:
    service = db.get(Service, service_id)
    if service is None or service.shop_id != shop.shop_id or not service.is_active:
        raise RuleError("That service isn't available any more. Pick another one.", 404)
    return service


@router.get("/{shop_id}/calendar", response_model=list[CalendarDayOut])
def get_calendar(shop_id: str, service_id: str, days: int = Query(14, ge=1, le=31), db: Session = Depends(get_db)):
    """For each day from today: open or closed, and whether a time is still free for this service."""
    shop = shop_rules.get_shop(db, shop_id)
    return calendar(db, shop, _bookable_service(db, shop, service_id).duration_min, days)


@router.get("/{shop_id}/slots", response_model=SlotsOut)
def get_slots(shop_id: str, service_id: str, date: date, db: Session = Depends(get_db)):
    """Every start time on that day, how full it is, and the shop's monthly limit for that month."""
    shop = shop_rules.get_shop(db, shop_id)
    slots = slots_for(db, shop, date, _bookable_service(db, shop, service_id).duration_min)
    return {"closed": slots is None, "slots": slots or [], "limit": limit_info(db, shop.shop_id, date)}


@router.get("/{shop_id}", response_model=ShopOut)
def get_shop(shop_id: str, db: Session = Depends(get_db)):
    return shop_out(db, shop_rules.get_shop(db, shop_id))
