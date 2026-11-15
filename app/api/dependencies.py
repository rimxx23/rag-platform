from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.chunk import ChunkRepository
from app.repositories.collection import CollectionRepository
from app.repositories.document import DocumentRepository


def get_collection_repository(db: AsyncSession = Depends(get_db)) -> CollectionRepository:
    return CollectionRepository(db)


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_chunk_repository(db: AsyncSession = Depends(get_db)) -> ChunkRepository:
    return ChunkRepository(db)


async def valid_collection_id(
    collection_id: str,
    collections: CollectionRepository = Depends(get_collection_repository),
) -> str:
    if await collections.get_by_id(collection_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    return collection_id
