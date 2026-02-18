from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
  id: int
  email: EmailStr
  nickname: str
  role: str
  profile_image: str | None = None

  @classmethod
  def from_model(cls, user) -> "UserResponse":
    return cls(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        role=user.role,
        profile_image=getattr(user, "profile_image", None),
    )
