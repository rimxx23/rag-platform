from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped

from app.models.base import Base


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    username: Mapped[str]
    hashed_password: Mapped[str]
