import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import UserORM
from app.repositories.chunk import ChunkRepository
from app.repositories.collection import CollectionRepository
from app.repositories.document import DocumentRepository
from app.repositories.question import QuestionRepository
from app.repositories.user import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repository),
) -> UserORM:
    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise invalid_credentials() from None
    user = await users.get_by_id(user_id)
    if user is None:
        raise invalid_credentials()
    return user


def get_collection_repository(db: AsyncSession = Depends(get_db)) -> CollectionRepository:
    return CollectionRepository(db)


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_chunk_repository(db: AsyncSession = Depends(get_db)) -> ChunkRepository:
    return ChunkRepository(db)


def get_question_repository(db: AsyncSession = Depends(get_db)) -> QuestionRepository:
    return QuestionRepository(db)


async def valid_collection_id(
    collection_id: str,
    user: UserORM = Depends(get_current_user),
    collections: CollectionRepository = Depends(get_collection_repository),
) -> str:
    if await collections.get_by_id(collection_id, user.id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    return collection_id
