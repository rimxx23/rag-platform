from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import QuestionORM
from app.schemas.ask import AnswerSchema


class QuestionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, collection_id: str, question: str, result: AnswerSchema) -> None:
        self.db.add(
            QuestionORM(
                collection_id=collection_id,
                question=question,
                answer=result.answer,
                sources=[source.model_dump(mode="json") for source in result.sources],
            )
        )

    async def list_by_collection(
        self, collection_id: str, limit: int, offset: int
    ) -> Sequence[QuestionORM]:
        query = (
            select(QuestionORM)
            .where(QuestionORM.collection_id == collection_id)
            .order_by(QuestionORM.created_at.desc(), QuestionORM.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self.db.scalars(query)).all()
