from __future__ import annotations

from fastapi import Response
from app.core.config import get_settings

settings = get_settings()

def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    common = dict(
        httponly=True,
        secure=settings.cookie_secure_effective,  # config에 property 있어야 함
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key=settings.COOKIE_ACCESS_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        **common,
    )
    response.set_cookie(
        key=settings.COOKIE_REFRESH_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        **common,
    )

def clear_auth_cookies(response: Response) -> None:
    common = dict(
        httponly=True,
        secure=settings.cookie_secure_effective,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.delete_cookie(settings.COOKIE_ACCESS_NAME, **common)
    response.delete_cookie(settings.COOKIE_REFRESH_NAME, **common)