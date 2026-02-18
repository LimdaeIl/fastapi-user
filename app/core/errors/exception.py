from __future__ import annotations

from typing import Any, Optional

from app.core.errors.codes import ErrorCode
from app.core.errors.problem import Problem


class AppException(Exception):
    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        code: ErrorCode,
        domain_code: str,
        type_: str = "about:blank",
        instance: Optional[str] = None,
        errors: Any = None,
    ) -> None:
        self.problem = Problem(
            type=type_,
            title=title,
            status=status,
            detail=detail,
            instance=instance,
            code=str(code),
            domain_code=domain_code,
            errors=errors,
        )
        super().__init__(detail)
