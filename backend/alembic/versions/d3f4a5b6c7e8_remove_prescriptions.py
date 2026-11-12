"""remove the doctor's-prescription feature (printed lab reports only)

Drops prescription_items and test_recommendations, the centre_searches -> recommendation link, and any
uploaded prescription documents (their stored files are left for the retention job / manual cleanup).

Revision ID: d3f4a5b6c7e8
Revises: c7a1e2f3b4d5
Create Date: 2026-11-11 23:00:00
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d3f4a5b6c7e8"
down_revision: str | None = "c7a1e2f3b4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "centre_searches" in tables:
        cols = {c["name"] for c in sa.inspect(bind).get_columns("centre_searches")}
        if "recommendation_id" in cols:
            with op.batch_alter_table("centre_searches", schema=None) as batch_op:
                for ix in sa.inspect(bind).get_indexes("centre_searches"):
                    if ix["column_names"] == ["recommendation_id"]:
                        batch_op.drop_index(ix["name"])
                batch_op.drop_column("recommendation_id")
    for name in ("test_recommendations", "prescription_items"):
        if name in tables:
            op.drop_table(name)
    op.execute("DELETE FROM documents WHERE doc_type = 'PRESCRIPTION'")


def downgrade() -> None:
    raise NotImplementedError("The prescription feature was removed; restore from a backup if needed.")
