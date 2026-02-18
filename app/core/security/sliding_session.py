from __future__ import annotations

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.security.jwt import decode_token
from app.infra.redis import get_refresh_session, store_refresh_session, delete_session
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.modules.auth.cookies import set_auth_cookies

settings = get_settings()

# access 만료 몇 초 전에 refresh 할지
SLIDING_WINDOW_SECONDS = 60 * 3  # 3분


class SlidingSessionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        access_token = request.cookies.get(settings.COOKIE_ACCESS_NAME)
        refresh_token = request.cookies.get(settings.COOKIE_REFRESH_NAME)

        # 토큰 없으면 그냥 통과
        if not access_token or not refresh_token:
            return await call_next(request)

        try:
            payload = decode_token(access_token)
        except Exception:
            return await call_next(request)

        if payload.get("typ") != "access":
            return await call_next(request)

        exp = payload["exp"]
        now = int(time.time())

        # 아직 충분히 남았으면 아무것도 안함
        if exp - now > SLIDING_WINDOW_SECONDS:
            return await call_next(request)

        # ===== refresh 자동 수행 =====
        try:
            refresh_payload = decode_token(refresh_token)

            if refresh_payload.get("typ") != "refresh":
                return await call_next(request)

            user_id = int(refresh_payload["sub"])
            sid = refresh_payload["sid"]
            jti = refresh_payload["jti"]

            current_jti = get_refresh_session(user_id, sid)

            # replay 공격 감지
            if current_jti != jti:
                delete_session(user_id, sid)
                return await call_next(request)

            # rotation
            new_access = create_access_token(user_id, sid)
            new_refresh, new_jti = create_refresh_token(user_id, sid)

            store_refresh_session(
                user_id,
                sid,
                new_jti,
                settings.REFRESH_TOKEN_EXPIRE_SECONDS,
            )

            response: Response = await call_next(request)

            # 여기서 쿠키 재발급
            set_auth_cookies(response, new_access, new_refresh)

            return response

        except Exception:
            return await call_next(request)
