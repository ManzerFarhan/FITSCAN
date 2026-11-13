"""admin panel: user role, suspension and last login (FR-ADM-7..9)

Revision ID: f6b7c8d9e0a1
Revises: e4a5b6c7d8f9
Create Date: 2026-11-13 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6b7c8d9e0a1"
down_revision: Union[str, None] = "e4a5b6c7d8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(16), nullable=False, server_default="USER"))
        batch_op.add_column(sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("disabled_at")
        batch_op.drop_column("role")
