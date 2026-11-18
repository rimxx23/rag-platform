from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import CollectionORM


class CollectionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, name: str, owner_id: str) -> CollectionORM:
        collection = CollectionORM(name=name, owner_id=owner_id)
        self.db.add(collection)
        return collection

    async def get_all(self, owner_id: str) -> list[CollectionORM]:
        query = (
            select(CollectionORM)
            .where(CollectionORM.owner_id == owner_id)
            .order_by(CollectionORM.created_at)
        )
        return (await self.db.scalars(query)).all()

    async def get_by_id(self, collection_id: str, owner_id: str) -> CollectionORM | None:
        query = select(CollectionORM).where(
            CollectionORM.id == collection_id, CollectionORM.owner_id == owner_id
        )
        return await self.db.scalar(query)
