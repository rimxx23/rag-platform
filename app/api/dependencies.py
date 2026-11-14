from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.collection import CollectionRepository


def get_collection_repository(db: AsyncSession = Depends(get_db)) -> CollectionRepository:
    return CollectionRepository(db)
