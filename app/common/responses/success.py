from __future__ import annotations

from typing import Any
from fastapi.responses import JSONResponse


def ok(data: Any = None, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "success": True,
            "data": data,
        },
    )
