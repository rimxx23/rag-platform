from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chunk import ChunkORM
from app.models.document import DocumentORM


class ChunkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(self, collection_id: str, embedding: list[float], limit: int = 5) -> list[ChunkORM]:
        query = (
            select(ChunkORM)
            .join(DocumentORM, ChunkORM.document_id == DocumentORM.id)
            .where(DocumentORM.collection_id == collection_id)
            .order_by(ChunkORM.embedding.l2_distance(embedding))
            .limit(limit)
            .options(selectinload(ChunkORM.document))
        )
        return (await self.db.scalars(query)).all()
