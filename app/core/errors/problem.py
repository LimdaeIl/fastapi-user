from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Problem:
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

    # ✅ 권장: 전역 카테고리 + 도메인 상세코드 분리
    code: Optional[str] = None          # 예: "CONFLICT"
    domain_code: Optional[str] = None   # 예: "USER_EMAIL_ALREADY_EXISTS"

    errors: Optional[Any] = None
