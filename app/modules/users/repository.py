from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.users.models import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def save(db: Session, user: User) -> User:
    db.add(user)
    db.flush()  # id 채우기
    return user
