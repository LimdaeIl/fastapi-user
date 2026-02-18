from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors.codes import ErrorCode
from app.core.errors.exception import AppException
from app.core.errors.problem import Problem

logger = logging.getLogger(__name__)


def _to_json(problem: Problem) -> dict:
    body = {
        "type": problem.type,
        "title": problem.title,
        "status": problem.status,
        "detail": problem.detail,
        "instance": problem.instance,
        "code": problem.code,
        "domain_code": problem.domain_code,
        "errors": problem.errors,
    }
    return {k: v for k, v in body.items() if v is not None}


def _loc_to_field_path(loc: Tuple[Any, ...]) -> str:
    if not loc:
        return "_global"

    parts: List[str] = []
    for i, p in enumerate(loc):
        if i == 0:
            parts.append(str(p))
        elif isinstance(p, int):
            parts[-1] = f"{parts[-1]}[{p}]"
        else:
            parts.append(str(p))

    return ".".join(parts)


def _group_validation_errors(exc: RequestValidationError) -> Dict[str, List[str]]:
    field_errors: Dict[str, List[str]] = {}
    for e in exc.errors():
        field = _loc_to_field_path(tuple(e.get("loc", ())))
        msg = e.get("msg", "Invalid value")
        field_errors.setdefault(field, []).append(msg)
    return field_errors


def _json(problem: Problem) -> JSONResponse:
    """Problem -> JSONResponse"""
    return JSONResponse(status_code=problem.status, content=_to_json(problem))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_error_handler(request: Request,
        exc: AppException) -> JSONResponse:
        p = replace(exc.problem, instance=str(request.url.path))
        return JSONResponse(status_code=p.status, content=_to_json(p))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        p = Problem(
            type="https://errors.your-service.com/problems/validation-error",
            title="Validation Error",
            status=422,
            detail="Request validation failed",
            instance=str(request.url.path),
            code=str(ErrorCode.VALIDATION_ERROR),
            errors=_group_validation_errors(exc),
        )
        return _json(p)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        p = Problem(
            type="about:blank",
            title="Internal Server Error",
            status=500,
            detail="Unexpected server error",
            instance=str(request.url.path),
            code=str(ErrorCode.INTERNAL_ERROR),
        )
        return _json(p)
