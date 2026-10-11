"""Shared set-up for the tests.

The tests never touch the real data: they use a separate database with "_test" added to its name
(for example nadd_test), created automatically on the same PostgreSQL server. Every test starts from
empty tables and a frozen clock, so results don't depend on what day it is.

Run inside Docker:  docker compose exec backend-api python -m pytest
"""
import os
from datetime import datetime, time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# ---- point the app at the test database BEFORE any app module creates its engine ----
_url = make_url(os.getenv("DATABASE_URL", "postgresql+psycopg://nadd:change-me@localhost:5432/nadd"))
TEST_URL = _url.set(database=f"{_url.database}_test")
_admin = create_engine(_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
with _admin.connect() as conn:
    if not conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_URL.database}):
        conn.execute(text(f'CREATE DATABASE "{TEST_URL.database}"'))
_admin.dispose()
os.environ["DATABASE_URL"] = TEST_URL.render_as_string(hide_password=False)

import models  # noqa: E402
from core import timeutil  # noqa: E402
from core.ids import new_id  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from security import hash_password  # noqa: E402

PASSWORD_HASH = hash_password("password1")  # bcrypt is slow on purpose, so hash once for all test users

# A Wednesday morning in Bangkok. Every test starts here unless it moves the clock.
START = datetime(2026, 9, 23, 9, 0, tzinfo=timeutil.BANGKOK)


@pytest.fixture(scope="session", autouse=True)
def tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def empty_tables():
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} CASCADE"))


class Clock:
    """A clock the test controls: clock.now, clock.set(datetime), clock.advance(minutes=16)."""

    def __init__(self, now):
        self.now = now

    def set(self, now):
        self.now = now

    def advance(self, **kwargs):
        from datetime import timedelta
        self.now += timedelta(**kwargs)


@pytest.fixture
def clock(monkeypatch):
    c = Clock(START)
    # Every rule asks core.timeutil.now(), so replacing it freezes time for all of them
    monkeypatch.setattr(timeutil, "now", lambda: c.now)
    return c


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


class World:
    """A small shop to test against: open every day 10:00-19:00, 2 customers at once, 30% deposit."""

    def __init__(self, db):
        self.db = db
        db.add_all([
            models.Plan(plan_id="free", plan_name="Free", monthly_price=0, booking_limit=10),
            models.Plan(plan_id="pro", plan_name="Pro", monthly_price=299, booking_limit=None),
        ])
        self.owner = self.user("Owner One", role="shop_owner")
        self.shop = models.Shop(shop_id="shop_t", owner_id=self.owner.user_id, shop_name="Test Salon",
                                category="Hair salon", address="Bangkok", phone="02 000 0000", deposit_percent=30)
        db.add(self.shop)
        db.flush()
        for dow in range(7):
            db.add(models.BusinessHours(hours_id=f"bh_t_{dow}", shop_id="shop_t", day_of_week=dow,
                                        open_time=time(10), close_time=time(19), max_per_slot=2))
        self.cut = self.service("Haircut", 450, 45)
        self.colour = self.service("Colour", 1800, 120)
        db.add(models.Subscription(subscription_id="sub_t_free", shop_id="shop_t", plan_id="free",
                                   start_date=START.date().replace(day=1), end_date=None, status="active"))
        self.ploy = self.user("Ploy Srisuk", line=True)
        self.ton = self.user("Ton Kittisak", line=False)
        db.commit()

    def user(self, name, role="customer", line=True):
        u = models.User(user_id=new_id("u"), full_name=name, email=f"{new_id('e')}@test.nadd", phone="080",
                        password_hash=PASSWORD_HASH, role=role,
                        line_user_id="U-test" if line else None)
        self.db.add(u)
        self.db.flush()
        return u

    def service(self, name, price, minutes):
        s = models.Service(service_id=new_id("svc"), shop_id="shop_t", service_name=name, price=price,
                           duration_min=minutes, is_active=True)
        self.db.add(s)
        self.db.flush()
        return s


@pytest.fixture
def world(db, clock):
    return World(db)
