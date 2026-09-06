"""add learner self confidence to assessment attempts

Revision ID: 9b0c1d2e3f4a
Revises: 8a9b0c1d2e3f
Create Date: 2026-09-06

"""

from alembic import op
import sqlalchemy as sa


revision = "9b0c1d2e3f4a"
down_revision = "8a9b0c1d2e3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assessment_attempts") as batch_op:
        batch_op.add_column(sa.Column("self_confidence", sa.Float(), nullable=True))
        batch_op.create_check_constraint(
            "ck_attempt_self_confidence_range",
            "self_confidence IS NULL OR (self_confidence >= 0 AND self_confidence <= 1)",
        )


def downgrade() -> None:
    with op.batch_alter_table("assessment_attempts") as batch_op:
        batch_op.drop_constraint("ck_attempt_self_confidence_range", type_="check")
        batch_op.drop_column("self_confidence")