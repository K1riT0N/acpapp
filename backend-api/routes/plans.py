"""/plans: Free and Pro, with their price and monthly booking limit."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Plan
from schemas import PlanOut

router = APIRouter()


@router.get("", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.scalars(select(Plan).order_by(Plan.monthly_price)).all()
