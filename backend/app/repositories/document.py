from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentORM


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, collection_id: str, filename: str) -> DocumentORM:
        document = DocumentORM(collection_id=collection_id, filename=filename)
        self.db.add(document)
        return document

    async def get_by_id(self, document_id: str) -> DocumentORM | None:
        return await self.db.get(DocumentORM, document_id)

    async def get_by_collection(self, collection_id: str) -> list[DocumentORM]:
        query = select(DocumentORM).where(DocumentORM.collection_id == collection_id).order_by(DocumentORM.created_at)
        return (await self.db.scalars(query)).all()