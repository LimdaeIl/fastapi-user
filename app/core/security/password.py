from __future__ import annotations

from passlib.context import CryptContext

# bcrypt 해시 컨텍스트
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    평문 비밀번호 -> bcrypt 해시
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시가 일치하는지 검증
    """
    return _pwd_context.verify(plain_password, hashed_password)
