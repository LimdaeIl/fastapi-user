# app/modules/users/models.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER)

    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
