from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
WorkerSessionLocal = async_sessionmaker(bind=worker_engine, expire_on_commit=False)
