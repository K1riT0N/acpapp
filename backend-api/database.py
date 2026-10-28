"""Database connection shared by the whole API.

models.py imports `Base` to define the tables, and routes use `get_db`
to get a session for one request.
"""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://nadd:change-me@localhost:5432/nadd",  # used only when running outside Docker
)

# pool_pre_ping checks a connection is still alive before using it
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for every table in models.py."""


def get_db():
    """FastAPI dependency: opens a session for one request, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_user_roles() -> None:
    """Allow the Admin role in databases created before it was added."""
    if engine.dialect.name != "postgresql":
        return

    from models import ROLES, one_of

    with engine.begin() as conn:
        definition = conn.scalar(text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid = 'users'::regclass AND conname = 'ck_users_role'"
        ))
        if definition and "'admin'" in definition:
            return
        if definition:
            conn.execute(text("ALTER TABLE users DROP CONSTRAINT ck_users_role"))
        conn.execute(text(
            f"ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK ({one_of('role', ROLES)})"
        ))
