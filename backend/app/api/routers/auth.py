from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_current_user, get_user_repository, invalid_credentials
from app.api.rate_dependencies import limit_login, limit_registration
from app.core.security import create_access_token, dummy_hash, password_hash
from app.models.user import UserORM
from app.repositories.user import UserRepository
from app.schemas.user import TokenSchema, UserCreateSchema, UserSchema


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(limit_registration)])
async def register(
    payload: UserCreateSchema,
    users: UserRepository = Depends(get_user_repository),
) -> UserSchema:
    hashed_password = await run_in_threadpool(password_hash.hash, payload.password)
    user = await users.create(payload.username, hashed_password)
    if user is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    await users.db.commit()
    return UserSchema.model_validate(user)


@router.post("/login", dependencies=[Depends(limit_login)])
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    users: UserRepository = Depends(get_user_repository),
) -> TokenSchema:
    if not 3 <= len(form.username) <= 64 or not 8 <= len(form.password) <= 128:
        raise invalid_credentials()
    user = await users.get_by_username(form.username)
    hashed_password = user.hashed_password if user else dummy_hash
    valid = await run_in_threadpool(password_hash.verify, form.password, hashed_password)
    if user is None or not valid:
        raise invalid_credentials()
    return TokenSchema(access_token=create_access_token(user.id))


@router.get("/me")
async def me(user: UserORM = Depends(get_current_user)) -> UserSchema:
    return UserSchema.model_validate(user)
