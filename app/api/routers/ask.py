from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_chunk_repository, valid_collection_id
from app.repositories.chunk import ChunkRepository
from app.schemas.ask import AnswerSchema, AskSchema
from app.services.ask import answer_question
from app.services.llm import LLMUnavailableError

router = APIRouter(prefix="/collections/{collection_id}/ask", tags=["ask"])


@router.post("")
async def ask(
    payload: AskSchema,
    collection_id: str = Depends(valid_collection_id),
    chunks: ChunkRepository = Depends(get_chunk_repository),
) -> AnswerSchema:
    try:
        return await answer_question(chunks, collection_id, payload.question)
    except LLMUnavailableError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from None
