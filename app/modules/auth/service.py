from __future__ import annotations

from fastapi import Depends, Response
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.errors.raise_ import raise_app_error
from app.core.security.jwt import create_access_token, create_refresh_token, \
  create_session_id
from app.core.security.jwt import decode_token
from app.core.security.password import verify_password
from app.infra.redis import delete_session
from app.infra.redis import (
  get_refresh_session,
  store_refresh_session,
)
from app.modules.users.errors import UserError
from app.modules.users.models import User
from app.modules.users.repository import get_by_email
from app.modules.users.service import create_user
from .cookies import set_auth_cookies, clear_auth_cookies

settings = get_settings()


class AuthService:
  def __init__(self, db: Session = Depends(get_db)):
    self.db = db

  def signup(self, *, email: str, nickname: str, password: str) -> User:
    if get_by_email(self.db, email) is not None:
      raise_app_error(UserError.EMAIL_ALREADY_EXISTS)

    user = create_user(self.db,
                       email=email,
                       nickname=nickname,
                       password=password)
    self.db.commit()
    self.db.refresh(user)
    return user

  def login_and_set_cookies(self, response: Response, *, email: str,
      password: str):

    user = get_by_email(self.db, email)

    if user is None or not verify_password(password, user.password):
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    sid = create_session_id()

    access = create_access_token(user_id=user.id, session_id=sid)

    refresh, jti = create_refresh_token(
        user_id=user.id,
        session_id=sid,
    )

    # ⭐ Redis에 현재 refresh 저장
    store_refresh_session(
        user_id=user.id,
        sid=sid,
        refresh_jti=jti,
        ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    set_auth_cookies(response, access, refresh)

  def logout(self, request: Request, response: Response):
    refresh_token = request.cookies.get(settings.COOKIE_REFRESH_NAME)

    if not refresh_token:
      clear_auth_cookies(response)
      return

    try:
      payload = decode_token(refresh_token)
    except Exception:
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    user_id = int(payload["sub"])
    sid = payload["sid"]

    delete_session(user_id, sid)

    clear_auth_cookies(response)

  def refresh(self, request: Request, response: Response):

    refresh_token = request.cookies.get(settings.COOKIE_REFRESH_NAME)

    if not refresh_token:
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    try:
      payload = decode_token(refresh_token)

      if payload.get("typ") != "refresh":
        raise_app_error(UserError.LOGIN_UNAUTHORIZED)

      user_id = int(payload["sub"])
      sid = payload["sid"]
      jti = payload["jti"]

    except (KeyError, ValueError, TypeError):
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    current_jti = get_refresh_session(user_id, sid)

    # 세션 없음 (TTL 만료 or logout)
    if current_jti is None:
      clear_auth_cookies(response)
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    # replay / theft detection
    if current_jti != jti:
      delete_session(user_id, sid)
      clear_auth_cookies(response)
      raise_app_error(UserError.LOGIN_UNAUTHORIZED)

    # ROTATION
    new_access = create_access_token(user_id, sid)
    new_refresh, new_jti = create_refresh_token(user_id, sid)

    store_refresh_session(
        user_id,
        sid,
        new_jti,
        settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    set_auth_cookies(response, new_access, new_refresh)
