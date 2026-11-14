from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChunkORM(Base):
    __tablename__ = "chunks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    page: Mapped[int | None]
    chunk_index: Mapped[int]
