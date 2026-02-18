# app/core/config.py
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "fastapi-user"
    APP_ENV: str = "local"
    DEBUG: bool = True

    CORS_ORIGINS: str = "http://localhost:5173"

    DB_HOST: str = "localhost"
    DB_PORT: int = 3307
    DB_NAME: str = "fastapi_user"
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 15
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 14

    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None
    COOKIE_ACCESS_NAME: str = "access_token"
    COOKIE_REFRESH_NAME: str = "refresh_token"

    SINGLE_DEVICE_ONLY: bool = False

    @property
    def cookie_secure_effective(self) -> bool:
        # local에서는 http라서 secure=False 아니면 쿠키가 저장 안됨
        if self.APP_ENV == "local":
            return False
        return self.COOKIE_SECURE

@lru_cache
def get_settings() -> Settings:
    return Settings()
