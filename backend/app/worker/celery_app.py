from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("rag_platform", broker=settings.REDIS_URL, include=["app.worker.tasks"])
