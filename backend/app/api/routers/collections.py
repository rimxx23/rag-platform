from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_collection_repository, get_current_user
from app.models.user import UserORM
from app.repositories.collection import CollectionRepository
from app.schemas.collection import CollectionCreateSchema, CollectionSchema

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_collection(
    payload: CollectionCreateSchema,
    user: UserORM = Depends(get_current_user),
    repository: CollectionRepository = Depends(get_collection_repository),
) -> CollectionSchema:
    collection = await repository.create(name=payload.name, owner_id=user.id)
    await repository.db.commit()
    return CollectionSchema.model_validate(collection)


@router.get("")
async def list_collections(
    user: UserORM = Depends(get_current_user),
    repository: CollectionRepository = Depends(get_collection_repository),
) -> list[CollectionSchema]:
    collections = await repository.get_all(user.id)
    return [CollectionSchema.model_validate(collection) for collection in collections]
