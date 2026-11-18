from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_chunk_repository, get_question_repository, valid_collection_id
from app.api.rate_dependencies import limit_ask
from app.repositories.chunk import ChunkRepository
from app.repositories.question import QuestionRepository
from app.schemas.ask import AnswerSchema, AskSchema, HistoryItemSchema
from app.services.ask import answer_question
from app.services.llm import LLMUnavailableError

router = APIRouter(prefix="/collections/{collection_id}", tags=["ask"])


@router.post("/ask", dependencies=[Depends(limit_ask)])
async def ask(
    payload: AskSchema,
    collection_id: str = Depends(valid_collection_id),
    chunks: ChunkRepository = Depends(get_chunk_repository),
    history: QuestionRepository = Depends(get_question_repository),
) -> AnswerSchema:
    try:
        result = await answer_question(chunks, collection_id, payload.question)
    except LLMUnavailableError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from None
    await history.create(collection_id, payload.question, result)
    await history.db.commit()
    return result


@router.get("/history")
async def list_history(
    collection_id: str = Depends(valid_collection_id),
    history: QuestionRepository = Depends(get_question_repository),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[HistoryItemSchema]:
    items = await history.list_by_collection(collection_id, limit, offset)
    return [HistoryItemSchema.model_validate(item) for item in items]
