from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional, Protocol, TypeVar

from app.core.errors.codes import ErrorCode
from app.core.errors.exception import AppException
from app.core.errors.status_map import ERROR_CODE_HTTP_STATUS


class SupportsDomainError(Protocol):
    code: ErrorCode
    domain_code: str
    message: str
    type: str


E = TypeVar("E", bound=SupportsDomainError)


def raise_app_error(
    err: E,
    *,
    detail: Optional[str] = None,
    instance: Optional[str] = None,
    errors: Any = None,
) -> None:
    http_status: HTTPStatus = ERROR_CODE_HTTP_STATUS.get(err.code, HTTPStatus.INTERNAL_SERVER_ERROR)

    raise AppException(
        status=int(http_status),
        title=http_status.phrase,
        detail=detail or err.message,
        code=err.code,
        domain_code=err.domain_code,
        type_=err.type,
        instance=instance,
        errors=errors,
    )
