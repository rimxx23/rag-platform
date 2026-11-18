from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.routers.ask import router as ask_router
from app.api.routers.auth import router as auth_router
from app.api.routers.collections import router as collections_router
from app.api.routers.documents import router as documents_router

from app.core.config import get_settings
from app.core.rate_limit import RateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Redis.from_url(get_settings().REDIS_URL, socket_timeout=2, socket_connect_timeout=2) as redis:
        app.state.rate_limiter = RateLimiter(redis)
        yield


app = FastAPI(title="RAG Platform", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(collections_router)
app.include_router(documents_router)
app.include_router(ask_router)
