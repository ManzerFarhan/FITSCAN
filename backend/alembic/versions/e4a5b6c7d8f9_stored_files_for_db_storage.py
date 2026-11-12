"""stored_files table: uploaded files kept in the database (STORAGE_BACKEND=db)

Revision ID: e4a5b6c7d8f9
Revises: d3f4a5b6c7e8
Create Date: 2026-11-12 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e4a5b6c7d8f9"
down_revision: Union[str, None] = "d3f4a5b6c7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stored_files",
        sa.Column("key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("stored_files")
