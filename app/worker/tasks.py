import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import ChunkORM
from app.models.document import DocumentORM, DocumentStatus
from app.repositories.document import DocumentRepository
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.extractor import extract_pages
from app.services.storage import get_extension, get_upload_path
from app.worker.celery_app import celery_app
from app.worker.db import WorkerSessionLocal


async def index_document(db: AsyncSession, document: DocumentORM) -> None:
    path = get_upload_path(document.id, get_extension(document.filename))

    chunks = []
    for page, text in extract_pages(path):
        for content in chunk_text(text.replace("\x00", "")):
            chunks.append((page, content))

    if not chunks:
        raise ValueError("Document has no text")

    embeddings = embed_texts([content for _, content in chunks])

    for index, ((page, content), embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            ChunkORM(
                document_id=document.id,
                content=content,
                embedding=embedding,
                page=page,
                chunk_index=index,
            )
        )


async def process(document_id: str) -> None:
    async with WorkerSessionLocal() as db:
        repository = DocumentRepository(db)
        document = await repository.get_by_id(document_id)
        if document is None:
            return

        try:
            await index_document(db, document)
            document.status = DocumentStatus.READY
        except Exception as e:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            document.error = str(e)

        await db.commit()


@celery_app.task
def process_document(document_id: str) -> None:
    asyncio.run(process(document_id))
