"""Database connection shared by the whole API.

models.py imports `Base` to define the tables, and routes use `get_db`
to get a session for one request.
"""
import os

from sqlalchemy import create_engine
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
