"""Add a hash for detecting duplicate CSV imports.

Revision ID: 20260902_03
Revises: 20260902_02
Create Date: 2026-09-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260902_03"
down_revision: str | None = "20260902_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.add_column(sa.Column("import_hash", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_expense_user_import_hash", ["user_id", "import_hash"]
        )


def downgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_constraint("uq_expense_user_import_hash", type_="unique")
        batch_op.drop_column("import_hash")
