"""/shops: the public shop directory and shop pages. No login needed."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core import shops as shop_rules
from core.limits import plan_of
from database import get_db
from models import Shop
from schemas import HoursOut, ServiceOut, ShopOut

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


@router.get("/{shop_id}", response_model=ShopOut)
def get_shop(shop_id: str, db: Session = Depends(get_db)):
    return shop_out(db, shop_rules.get_shop(db, shop_id))
