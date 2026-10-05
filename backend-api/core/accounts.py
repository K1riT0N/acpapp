"""Creating accounts and checking passwords. Error messages use the prototype's wording."""
import re
import string
from datetime import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core import timeutil
from core.errors import RuleError
from core.ids import new_id, random_code
from core.shops import CATEGORIES
from models import BusinessHours, Shop, Subscription, User
from security import hash_password, verify_password

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MIN_PASSWORD = 8

# What a brand-new shop starts with (the owner can change it all in Shop settings)
NEW_SHOP_DEPOSIT_PERCENT = 30
NEW_SHOP_DAYS = [1, 2, 3, 4, 5, 6]  # Monday to Saturday
NEW_SHOP_OPEN, NEW_SHOP_CLOSE, NEW_SHOP_PER_SLOT = time(10, 0), time(19, 0), 2


def find_by_email(db: Session, email: str):
    return db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))


def register(db: Session, *, full_name: str, email: str, phone: str, password: str, role: str, line: bool,
             shop_name: str = "", category: str = "", address: str = "") -> User:
    """Create a customer, or a shop owner together with their shop, opening hours and Free plan."""
    full_name, email, phone = full_name.strip(), email.strip().lower(), phone.strip()
    shop_name, address = shop_name.strip(), address.strip()
    if role not in ("customer", "shop_owner"):
        raise RuleError("Choose whether you're booking or running a shop.")

    # Collect every problem, so the person can fix the whole form at once
    errors = []
    if not full_name:
        errors.append("Enter your name.")
    if not EMAIL_RE.match(email):
        errors.append("Enter an email like name@example.com.")
    elif find_by_email(db, email):
        errors.append("That email already has an account. Log in instead.")
    if not phone:
        errors.append("Enter a phone number so shops can reach you.")
    if len(password) < MIN_PASSWORD:
        errors.append(f"Choose a password with at least {MIN_PASSWORD} characters.")
    if role == "shop_owner":
        if not shop_name:
            errors.append("Enter your shop's name.")
        if not address:
            errors.append("Enter your shop's area or address.")
    if errors:
        raise RuleError(" ".join(errors))

    user = User(
        user_id=new_id("u"),
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        # Simulated LINE account. The real LINE Messaging API gives a user ID when the person adds the shop's LINE account.
        line_user_id=f"U-sim-{random_code(5, string.ascii_lowercase)}" if line else None,
        demo=False,
    )
    db.add(user)
    db.flush()  # the shop below points at this user, so the row must exist first

    if role == "shop_owner":
        shop = Shop(
            shop_id=new_id("shop"),
            owner_id=user.user_id,
            shop_name=shop_name,
            category=category if category in CATEGORIES else CATEGORIES[0],
            address=address,
            phone=phone,
            description="",
            deposit_percent=NEW_SHOP_DEPOSIT_PERCENT,
        )
        db.add(shop)
        db.flush()
        for dow in NEW_SHOP_DAYS:
            db.add(BusinessHours(hours_id=f"bh_{shop.shop_id}_{dow}", shop_id=shop.shop_id, day_of_week=dow,
                                 open_time=NEW_SHOP_OPEN, close_time=NEW_SHOP_CLOSE, max_per_slot=NEW_SHOP_PER_SLOT))
        db.add(Subscription(subscription_id=f"sub_{shop.shop_id}_free", shop_id=shop.shop_id, plan_id="free",
                            start_date=timeutil.today(), end_date=None, status="active"))

    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Return the user if the email and password match. Wrong email and wrong password get different messages."""
    email = email.strip().lower()
    if not email or not password:
        raise RuleError("Enter your email and password.")
    user = find_by_email(db, email)
    if user is None:
        raise RuleError("No account uses that email. Check the spelling, or create an account.", 401)
    if not verify_password(password, user.password_hash):
        hint = " Demo accounts use demo1234." if user.demo else ""
        raise RuleError("That password is wrong." + hint, 401)
    return user
