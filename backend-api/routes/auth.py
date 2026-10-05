"""/auth: sign up, log in, who am I, and the demo accounts for the login page."""
from fastapi import APIRouter, Depends
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from core import accounts
from core.limits import plan_of
from database import get_db
from models import User
from schemas import AuthOut, DemoAccountOut, LoginIn, RegisterIn, UserOut
from security import create_token, get_current_user

router = APIRouter()


def user_out(user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.shop_id = user.shop.shop_id if user.shop else None
    return out


def auth_out(user: User) -> AuthOut:
    return AuthOut(token=create_token(user), user=user_out(user))


@router.post("/register", response_model=AuthOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    """Create an account. Shop owners also get a shop (30% deposit, open Mon–Sat 10:00–19:00, Free plan)."""
    user = accounts.register(db, **body.model_dump())
    return auth_out(user)


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = accounts.authenticate(db, body.email, body.password)
    return auth_out(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.get("/demo-accounts", response_model=list[DemoAccountOut])
def demo_accounts(db: Session = Depends(get_db)):
    """Customers first, then shop owners, each A to Z."""
    users = db.scalars(
        select(User).where(User.demo.is_(True))
        .order_by(case((User.role == "customer", 0), else_=1), User.full_name)
    ).all()
    result = []
    for u in users:
        item = DemoAccountOut(user_id=u.user_id, full_name=u.full_name, email=u.email, role=u.role)
        if u.shop:
            item.shop_name = u.shop.shop_name
            item.plan_name = plan_of(db, u.shop.shop_id)[1].plan_name
        result.append(item)
    return result
