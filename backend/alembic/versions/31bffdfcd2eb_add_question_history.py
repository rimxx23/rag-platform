"""Add collection question history.

Revision ID: 31bffdfcd2eb
Revises: 5d2b4ef41ac0
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "31bffdfcd2eb"
down_revision = "5d2b4ef41ac0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "collection_id",
            sa.String(),
            sa.ForeignKey("collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_questions_collection_created_id", "questions", ["collection_id", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_table("questions")
