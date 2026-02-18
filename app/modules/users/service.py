# app/modules/users/service.py
from sqlalchemy.orm import Session
from app.core.security.password import hash_password
from app.modules.users.models import User, UserRole
from app.modules.users.repository import save

def create_user(db: Session, *, email: str, nickname: str, password: str) -> User:
    user = User(
        email=email,
        nickname=nickname,
        password=hash_password(password),
        role=str(UserRole.USER),
    )
    save(db, user)     # add + flush
    return user