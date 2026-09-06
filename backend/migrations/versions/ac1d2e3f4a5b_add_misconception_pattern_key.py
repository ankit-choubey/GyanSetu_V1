"""add deterministic misconception pattern key

Revision ID: ac1d2e3f4a5b
Revises: 9b0c1d2e3f4a
Create Date: 2026-09-06

"""

from alembic import op
import sqlalchemy as sa


revision = "ac1d2e3f4a5b"
down_revision = "9b0c1d2e3f4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("misconceptions") as batch_op:
        batch_op.add_column(sa.Column("pattern_key", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_misconception_pattern_scope",
        "misconceptions",
        ["learner_id", "competency_id", "subskill_id", "pattern_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_misconception_pattern_scope", table_name="misconceptions")
    with op.batch_alter_table("misconceptions") as batch_op:
        batch_op.drop_column("pattern_key")