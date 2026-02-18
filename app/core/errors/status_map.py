# app/core/errors/status_map.py
from __future__ import annotations

from http import HTTPStatus
from app.core.errors.codes import ErrorCode

ERROR_CODE_HTTP_STATUS: dict[ErrorCode, HTTPStatus] = {
    ErrorCode.VALIDATION_ERROR: HTTPStatus.UNPROCESSABLE_ENTITY,  # 422
    ErrorCode.BAD_REQUEST: HTTPStatus.BAD_REQUEST,                # 400
    ErrorCode.UNAUTHORIZED: HTTPStatus.UNAUTHORIZED,              # 401
    ErrorCode.FORBIDDEN: HTTPStatus.FORBIDDEN,                    # 403
    ErrorCode.NOT_FOUND: HTTPStatus.NOT_FOUND,                    # 404
    ErrorCode.CONFLICT: HTTPStatus.CONFLICT,                      # 409
    ErrorCode.INTERNAL_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,   # 500
}
