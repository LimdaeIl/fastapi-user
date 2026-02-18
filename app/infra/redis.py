from __future__ import annotations

import json
from typing import Any

from redis import Redis
from app.core.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


def set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    redis_client.set(key, json.dumps(value), ex=ttl_seconds)


def get_json(key: str) -> dict[str, Any] | None:
    raw = redis_client.get(key)
    return json.loads(raw) if raw else None


def delete(key: str) -> None:
    redis_client.delete(key)


def session_key(user_id: int, sid: str) -> str:
    return f"sess:{user_id}:{sid}"


def store_refresh_session(
    user_id: int,
    sid: str,
    refresh_jti: str,
    ttl_seconds: int,
) -> None:
    redis_client.set(
        session_key(user_id, sid),
        refresh_jti,
        ex=ttl_seconds,
    )


def get_refresh_session(user_id: int, sid: str) -> str | None:
    return redis_client.get(session_key(user_id, sid))


def delete_session(user_id: int, sid: str) -> None:
    redis_client.delete(session_key(user_id, sid))