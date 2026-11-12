"""optional user height and weight for the dashboard BMI

Revision ID: c7a1e2f3b4d5
Revises: b200d48a546c
Create Date: 2026-11-11 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7a1e2f3b4d5"
down_revision: Union[str, None] = "b200d48a546c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("height_cm", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("weight_kg", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("weight_kg")
        batch_op.drop_column("height_cm")
