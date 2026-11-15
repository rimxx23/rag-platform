import asyncio

from app.models.document import DocumentORM, DocumentStatus
from app.repositories.document import DocumentRepository
from app.services.storage import get_extension, get_upload_path
from app.worker.celery_app import celery_app
from app.worker.db import WorkerSessionLocal


async def index_document(document: DocumentORM) -> None:
    path = get_upload_path(document.id, get_extension(document.filename))
    if not path.exists():
        raise FileNotFoundError("Uploaded file not found")


async def process(document_id: str) -> None:
    async with WorkerSessionLocal() as db:
        repository = DocumentRepository(db)
        document = await repository.get_by_id(document_id)
        if document is None:
            return

        try:
            await index_document(document)
            document.status = DocumentStatus.READY
        except Exception as e:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            document.error = str(e)

        await db.commit()


@celery_app.task
def process_document(document_id: str) -> None:
    asyncio.run(process(document_id))
