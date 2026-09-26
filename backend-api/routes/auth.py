from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database import Business, User, UserRole, get_db
from deps import COOKIE_NAME, get_current_user
from schemas import LoginRequest, RegisterRequest, UserOut
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24


def _set_auth_cookie(response: Response, user: User) -> None:
    token = create_access_token(str(user.id), user.role.value)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE_SECONDS,
    )


def _to_user_out(user: User) -> UserOut:
    tier = user.business.subscription_tier if user.role == UserRole.business and user.business else None
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        subscription_tier=tier,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.business:
        db.add(Business(user_id=user.id, business_name=payload.business_name))

    db.commit()
    db.refresh(user)
    _set_auth_cookie(response, user)
    return _to_user_out(user)


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _set_auth_cookie(response, user)
    return _to_user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _to_user_out(user)
