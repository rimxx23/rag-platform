from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserORM


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, username: str, hashed_password: str) -> UserORM | None:
        query = (
            insert(UserORM)
            .values(username=username, hashed_password=hashed_password)
            .on_conflict_do_nothing(constraint="uq_users_username")
            .returning(UserORM)
        )
        return await self.db.scalar(query)

    async def get_by_username(self, username: str) -> UserORM | None:
        return await self.db.scalar(select(UserORM).where(UserORM.username == username))

    async def get_by_id(self, user_id: str) -> UserORM | None:
        return await self.db.get(UserORM, user_id)
