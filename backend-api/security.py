"""Passwords, login tokens and "who is calling this route?".

- Passwords are stored as bcrypt hashes. bcrypt adds a random salt and is deliberately slow,
  so a stolen database doesn't reveal the passwords.
- After logging in, the browser gets a JWT (JSON Web Token). It holds the user's id and role and is
  signed with JWT_SECRET, so the server can check it wasn't changed. The browser sends it back on
  every request in the header `Authorization: Bearer <token>`.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User

JWT_SECRET = os.getenv("JWT_SECRET") or "dev-only-secret-change-me"
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(days=7)

# auto_error=False: we write our own message when the header is missing
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # not a valid bcrypt hash
        return False


def create_token(user: User) -> str:
    payload = {"sub": user.user_id, "role": user.role, "exp": datetime.now(timezone.utc) + TOKEN_LIFETIME}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_from_token(creds: Optional[HTTPAuthorizationCredentials], db: Session) -> Optional[User]:
    if creds is None:
        return None
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:  # bad signature, expired, or not a token at all
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has ended. Log in again.")
    user = db.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has ended. Log in again.")
    return user


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    """Route dependency: the logged-in user, or 401 if there is no valid token."""
    user = _user_from_token(creds, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Log in to continue.")
    return user


def get_optional_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
                      db: Session = Depends(get_db)) -> Optional[User]:
    """Route dependency for public pages that show a little more to logged-in users."""
    return _user_from_token(creds, db)


def require_role(role: str):
    """Route dependency factory: require_role("shop_owner") lets only shop owners through."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            who = "customers" if role == "customer" else "shop owners"
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"This page is for {who}.")
        return user
    return checker
