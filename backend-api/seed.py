"""Load the demo data from nadd_seed_data.json into the database.

Run it inside Docker:
    docker compose exec backend-api python seed.py           add the demo rows that are missing
    docker compose exec backend-api python seed.py --reset   wipe the whole database first, then seed

The JSON is written as if today were 2026-09-23 (its "anchor_date"). Every date and timestamp is
moved forward by (today in Bangkok - anchor date) days, so the demo always has bookings today and
reminders that are still to come. Running it twice is safe: rows whose ID already exists are skipped.
"""
import argparse
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import bcrypt
from sqlalchemy import Date, DateTime, Time, select, text
from sqlalchemy.exc import ProgrammingError

from database import Base, SessionLocal, engine, migrate_user_roles
from models import Booking, BusinessHours, Notification, Payment, Plan, Service, Shop, Subscription, User

BANGKOK = ZoneInfo("Asia/Bangkok")
DATA_FILE = Path(__file__).with_name("nadd_seed_data.json")
DEMO_PASSWORD = "demo1234"

# Parents before children: a row can only point at rows that are already in the database.
TABLES = [
    ("plans", Plan),
    ("users", User),
    ("shops", Shop),
    ("services", Service),
    ("business_hours", BusinessHours),
    ("subscriptions", Subscription),
    ("bookings", Booking),
    ("payments", Payment),
    ("notifications", Notification),
]

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # date.weekday(): Monday = 0
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(d: date) -> str:
    """Same output as the prototype's fmtDate, e.g. 'Wed 23 Sep'."""
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def convert_row(model, raw: dict, shift: timedelta) -> dict:
    """Turn one JSON object into column values, parsing and shifting dates by the column's type."""
    columns = model.__table__.columns
    row = {}
    for key, value in raw.items():
        if key not in columns:  # e.g. a JSON field the table doesn't have
            continue
        col_type = columns[key].type
        if value is not None and isinstance(col_type, DateTime):
            value = datetime.fromisoformat(value) + shift
        elif value is not None and isinstance(col_type, Date):
            value = date.fromisoformat(value) + shift
        elif value is not None and isinstance(col_type, Time):
            value = time.fromisoformat(value)
        row[key] = value
    return row


def fix_message_dates(raw: dict, bookings: dict, shift: timedelta) -> dict:
    """Message texts contain the booking day, e.g. 'on Wed 23 Sep at 16:00'. Rewrite it to the shifted day."""
    booking = bookings.get(raw.get("booking_id"))
    if not booking or not shift:
        return raw
    old_day = date.fromisoformat(booking["booking_date"])
    old, new = fmt_date(old_day), fmt_date(old_day + shift)
    return {**raw, "title": raw["title"].replace(old, new), "body": raw["body"].replace(old, new)}


def reset_database() -> None:
    """Drop every table (including ones from older versions of the app) and create the 9 tables again."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    anchor = date.fromisoformat(data["anchor_date"])
    today = datetime.now(BANGKOK).date()
    shift = today - anchor
    print(f"Anchor date {anchor}, today in Bangkok {today}: moving every date by {shift.days} days.")

    bookings_by_id = {b["booking_id"]: b for b in data["bookings"]}

    with SessionLocal() as db:
        for key, model in TABLES:
            pk_col = model.__table__.primary_key.columns[0]
            rows = data.get(key, [])
            wanted = [r[pk_col.name] for r in rows]
            existing = set(db.scalars(select(pk_col).where(pk_col.in_(wanted))))

            added = 0
            for raw in rows:
                if raw[pk_col.name] in existing:
                    continue
                if model is Notification:
                    raw = fix_message_dates(raw, bookings_by_id, shift)
                row = convert_row(model, raw, shift)
                if model is User:
                    # bcrypt adds a random salt, so each user gets a different hash of the same password
                    row["password_hash"] = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
                db.add(model(**row))
                added += 1
            db.flush()  # send this table's rows now so the next table's foreign keys find them
            print(f"  {key:<15} {added:>3} added, {len(existing):>3} already there")

        db.commit()

        print(f"\nBookings per shop in {today:%B %Y} (not counting expired ones):")
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        for shop in db.scalars(select(Shop).order_by(Shop.shop_name)):
            count = len(db.scalars(
                select(Booking.booking_id).where(
                    Booking.shop_id == shop.shop_id,
                    Booking.booking_date >= month_start,
                    Booking.booking_date < next_month,
                    Booking.status != "expired",
                )
            ).all())
            print(f"  {shop.shop_name:<24} {count}")

    print(f"\nDone. Demo accounts use the password {DEMO_PASSWORD}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load the Nadd demo data.")
    parser.add_argument("--reset", action="store_true", help="delete ALL data and tables first")
    args = parser.parse_args()

    if args.reset:
        print("Resetting the database: dropping every table...")
        reset_database()
    else:
        try:
            Base.metadata.create_all(bind=engine)  # in case the API hasn't started yet
            migrate_user_roles()
        except ProgrammingError:
            raise SystemExit(
                "The database still has tables from an older version of the app.\n"
                "Run `python seed.py --reset` to delete them and start fresh."
            )
    seed()
