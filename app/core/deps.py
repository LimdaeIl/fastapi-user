# app/core/deps.py
from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        # ✅ 커밋은 서비스에서 명시적으로 할 예정이면 여기서 commit 하지 않습니다.
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
