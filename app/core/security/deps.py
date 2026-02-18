from __future__ import annotations

from fastapi import Request, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.errors.raise_ import raise_app_error
from app.core.security.jwt import decode_token
from app.infra.redis import get_refresh_session
from app.modules.users.errors import UserError
from app.modules.users.models import User

settings = get_settings()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
  access_token = request.cookies.get(settings.COOKIE_ACCESS_NAME)
  if not access_token:
    raise_app_error(UserError.LOGIN_UNAUTHORIZED)

  try:
    payload = decode_token(access_token)

    if payload.get("typ") != "access":
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    user_id = int(payload["sub"])
    sid = payload["sid"]

  except (ValueError, KeyError, TypeError):
    raise_app_error(UserError.LOGIN_UNAUTHORIZED)

  # session binding (access 즉시 revoke 가능)
  try:
    if get_refresh_session(user_id, sid) is None:
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)
  except Exception:
    raise_app_error(UserError.LOGIN_UNAUTHORIZED)

  user = db.get(User, user_id)
  if user is None:
    raise_app_error(UserError.LOGIN_UNAUTHORIZED)

  return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
  access_token = request.cookies.get(settings.COOKIE_ACCESS_NAME)
  if not access_token:
    return None

  try:
    payload = decode_token(access_token)
  except ValueError:
    return None

  if payload.get("typ") != "access":
    return None

  try:
    user_id = int(payload["sub"])
    sid = payload["sid"]
  except (KeyError, ValueError):
    return None

  if get_refresh_session(user_id, sid) is None:
    return None

  return db.get(User, user_id)
