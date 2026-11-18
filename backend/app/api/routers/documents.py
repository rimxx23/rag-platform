from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_document_repository, valid_collection_id
from app.api.rate_dependencies import limit_upload
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentSchema
from app.services.exceptions import FileTooLargeError, InvalidFileError
from app.services.storage import save_upload
from app.worker.tasks import process_document

router = APIRouter(prefix="/collections/{collection_id}/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(limit_upload)])
async def upload_document(
    file: UploadFile,
    collection_id: str = Depends(valid_collection_id),
    documents: DocumentRepository = Depends(get_document_repository),
) -> DocumentSchema:
    document = await documents.create(collection_id=collection_id, filename=file.filename or "")
    await documents.db.flush()

    try:
        await save_upload(file, document.id)
    except InvalidFileError as e:
        await documents.db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from None
    except FileTooLargeError as e:
        await documents.db.rollback()
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(e)) from None

    await documents.db.commit()
    process_document.delay(document.id)
    return DocumentSchema.model_validate(document)


@router.get("")
async def list_documents(
    collection_id: str = Depends(valid_collection_id),
    documents: DocumentRepository = Depends(get_document_repository),
) -> list[DocumentSchema]:
    items = await documents.get_by_collection(collection_id)
    return [DocumentSchema.model_validate(document) for document in items]
