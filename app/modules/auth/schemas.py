from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignUpRequest(BaseModel):
  email: EmailStr
  nickname: str = Field(min_length=2, max_length=50)
  password: str = Field(min_length=8, max_length=512)  # 문자 길이는 넉넉히

  @field_validator("password")
  @classmethod
  def validate_password_bcrypt_limit(cls, v: str) -> str:
    # bcrypt는 입력이 72 bytes 초과면 문제 발생
    if len(v.encode("utf-8")) > 72:
      raise ValueError("password must be at most 72 bytes for bcrypt")
    return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
  ok: bool = True