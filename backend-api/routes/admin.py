"""Admin-only, read-only platform analytics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core import admin_dashboard
from core import timeutil
from database import get_db
from models import User
from schemas import AdminDashboardOut
from security import require_role

router = APIRouter()
admin_only = require_role("admin")


@router.get("/dashboard", response_model=AdminDashboardOut)
def get_dashboard(user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return admin_dashboard.summary(db, timeutil.today())
