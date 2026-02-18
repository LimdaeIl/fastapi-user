# app/core/errors/defs.py (또는 기존 defs.py)
from __future__ import annotations

from typing import Protocol, runtime_checkable
from app.core.errors.codes import ErrorCode


@runtime_checkable
class DomainErrorDef(Protocol):
    code: ErrorCode
    domain_code: str
    message: str
    type: str
