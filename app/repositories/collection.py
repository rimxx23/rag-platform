from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import CollectionORM


class CollectionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, name: str) -> CollectionORM:
        collection = CollectionORM(name=name)
        self.db.add(collection)
        return collection

    async def get_all(self) -> list[CollectionORM]:
        query = select(CollectionORM).order_by(CollectionORM.created_at)
        return (await self.db.scalars(query)).all()

    async def get_by_id(self, collection_id: str) -> CollectionORM | None:
        return await self.db.get(CollectionORM, collection_id)
