from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.responses.success import ok
from app.core.config import get_settings
from app.core.errors.handlers import register_exception_handlers
from app.core.logging import RequestIdMiddleware, setup_logging
from app.api.router import api_router
from app.core.security.sliding_session import SlidingSessionMiddleware



def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging()
    app = FastAPI(title=settings.APP_NAME, version="0.1.0")

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SlidingSessionMiddleware)

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_exception_handlers(app)

    @app.get("/health")
    async def health():
        return ok({"status": "ok"})

    # ✅ 여기서 버전 prefix를 한 번만
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
