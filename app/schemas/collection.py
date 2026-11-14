from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectionCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CollectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
