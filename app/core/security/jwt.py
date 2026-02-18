# app/core/security/jwt.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt, JWTError

from app.core.config import get_settings

settings = get_settings()


def _now() -> datetime:
  return datetime.now(timezone.utc)


def create_session_id() -> str:
  return uuid4().hex


def create_access_token(user_id: int, session_id: str) -> str:
  now = _now()
  payload = {
    "sub": str(user_id),
    "sid": session_id,
    "typ": "access",
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(
      seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)).timestamp()),
  }
  return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_refresh_token(user_id: int, session_id: str) -> tuple[str, str]:
  now = _now()
  jti = uuid4().hex

  payload = {
    "sub": str(user_id),
    "sid": session_id,
    "jti": jti,
    "typ": "refresh",
    "iat": int(now.timestamp()),
    "exp": int(
        (now + timedelta(
          seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)).timestamp()
    ),
  }

  token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
  return token, jti


def decode_token(token: str) -> dict:
  try:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
  except JWTError as e:
    raise ValueError("Invalid token") from e
