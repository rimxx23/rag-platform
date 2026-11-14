from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: str
    filename: str
    status: DocumentStatus
    error: str | None
    created_at: datetime
