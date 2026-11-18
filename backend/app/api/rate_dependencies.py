from fastapi import Depends, HTTPException, Request, status
from redis.exceptions import RedisError

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.models.user import UserORM


async def enforce(request: Request, key: str, limit: int) -> None:
    limiter: RateLimiter = request.app.state.rate_limiter
    try:
        retry_after = await limiter.retry_after(key, limit, get_settings().RATE_LIMIT_WINDOW_SECONDS)
    except RedisError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Rate limiter unavailable"
        ) from None
    if retry_after:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


async def limit_ask(request: Request, user: UserORM = Depends(get_current_user)) -> None:
    await enforce(request, f"ask:{user.id}", get_settings().ASK_RATE_LIMIT)


async def limit_upload(request: Request, user: UserORM = Depends(get_current_user)) -> None:
    await enforce(request, f"upload:{user.id}", get_settings().UPLOAD_RATE_LIMIT)


async def limit_login(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    await enforce(request, f"login:{host}", get_settings().LOGIN_RATE_LIMIT)


async def limit_registration(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    await enforce(request, f"register:{host}", get_settings().REGISTER_RATE_LIMIT)
