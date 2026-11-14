from datetime import datetime
import enum

from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocumentStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class DocumentORM(Base):
    __tablename__ = "documents"

    collection_id: Mapped[str] = mapped_column(ForeignKey("collections.id"))
    filename: Mapped[str]
    status: Mapped[DocumentStatus] = mapped_column(default=DocumentStatus.PROCESSING)
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
