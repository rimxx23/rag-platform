"""Add users and collection ownership.

Revision ID: 5d2b4ef41ac0
Revises: 239d27d0178c
"""

from alembic import op
import sqlalchemy as sa


revision = "5d2b4ef41ac0"
down_revision = "239d27d0178c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.add_column("collections", sa.Column("owner_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_collections_owner_id_users", "collections", "users", ["owner_id"], ["id"]
    )
    op.create_index("ix_collections_owner_id", "collections", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_collections_owner_id", table_name="collections")
    op.drop_constraint("fk_collections_owner_id_users", "collections", type_="foreignkey")
    op.drop_column("collections", "owner_id")
    op.drop_table("users")
