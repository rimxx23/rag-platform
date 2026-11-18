from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CollectionORM(Base):
    __tablename__ = "collections"

    name: Mapped[str]
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", name="fk_collections_owner_id_users"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())