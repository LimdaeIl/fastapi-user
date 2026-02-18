from __future__ import annotations

from enum import Enum
from app.core.errors.codes import ErrorCode


class UserError(Enum):
    EMAIL_ALREADY_EXISTS = (ErrorCode.CONFLICT, "회원: 이미 사용 중인 이메일입니다.")
    LOGIN_UNAUTHORIZED = (ErrorCode.UNAUTHORIZED, "회원: 아이디 또는 비밀번호가 틀렸습니다.")

    def __init__(self, code: ErrorCode, message: str) -> None:
        self._code = code
        self._message = message

    @property
    def code(self) -> ErrorCode:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    @property
    def domain_code(self) -> str:
        return f"USER_{self.name}"

    @property
    def type(self) -> str:
        return f"https://errors.your-service.com/users/{self.name.lower()}"
