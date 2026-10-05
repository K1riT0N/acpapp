"""/owner: everything a shop owner manages. Every route here requires the shop_owner role.

The shop is always the logged-in owner's own shop, so an owner can never change someone else's.
(Steps 9 and 10 add the dashboard, bookings and plan routes here.)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core import shops as shop_rules
from database import get_db
from models import User
from routes.shops import shop_out
from schemas import HoursDayIn, HoursOut, ServiceIn, ServiceOut, ShopOut, ShopUpdateIn
from security import require_role

router = APIRouter()
owner_only = require_role("shop_owner")


@router.get("/services", response_model=list[ServiceOut])
def list_services(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """All the shop's services, hidden ones included, A to Z."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return sorted(shop.services, key=lambda s: s.service_name.lower())


@router.post("/services", response_model=ServiceOut, status_code=201)
def add_service(body: ServiceIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.add_service(db, shop, body.service_name, body.price, body.duration_min)


@router.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: str, body: ServiceIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.update_service(db, shop, service_id, body.model_dump(exclude_unset=True))


@router.get("/shop", response_model=ShopOut)
def get_shop(user: User = Depends(owner_only), db: Session = Depends(get_db)):
    return shop_out(db, shop_rules.shop_of_owner(db, user.user_id))


@router.patch("/shop", response_model=ShopOut)
def update_shop(body: ShopUpdateIn, user: User = Depends(owner_only), db: Session = Depends(get_db)):
    shop = shop_rules.shop_of_owner(db, user.user_id)
    shop_rules.update_shop(db, shop, body.model_dump(exclude_unset=True))
    return shop_out(db, shop)


@router.put("/shop/hours", response_model=list[HoursOut])
def set_hours(body: list[HoursDayIn], user: User = Depends(owner_only), db: Session = Depends(get_db)):
    """Send all 7 days. Closed days (open: false) lose their row."""
    shop = shop_rules.shop_of_owner(db, user.user_id)
    return shop_rules.set_hours(db, shop, [d.model_dump() for d in body])
