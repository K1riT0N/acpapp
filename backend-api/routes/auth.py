# Temporary demo login from the starter template. Step 3 replaces it with
# register/login/me on the real `users` table (bcrypt + JWT).
import secrets

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import engine, get_db

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    email: str
    token: str


def setup_demo_users():
    demo_password = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS demo_users (
                    email VARCHAR(255) PRIMARY KEY,
                    password TEXT NOT NULL,
                    token TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO demo_users (email, password)
                VALUES (:email, :password)
                ON CONFLICT (email) DO NOTHING
                """
            ),
            {"email": "demo@example.com", "password": demo_password},
        )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.execute(
            text("SELECT email, password FROM demo_users WHERE email = :email"),
            {"email": payload.email},
        )
        .mappings()
        .first()
    )

    if user is None or not bcrypt.checkpw(
        payload.password.encode("utf-8"), user["password"].encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = secrets.token_urlsafe(32)
    db.execute(
        text("UPDATE demo_users SET token = :token WHERE email = :email"),
        {"email": payload.email, "token": token},
    )
    db.commit()

    return LoginResponse(email=payload.email, token=token)
