from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskSchema(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class SourceSchema(BaseModel):
    number: int
    document_id: str
    filename: str
    page: int | None
    content: str


class AnswerSchema(BaseModel):
    answer: str
    sources: list[SourceSchema]


class HistoryItemSchema(AnswerSchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    created_at: datetime
