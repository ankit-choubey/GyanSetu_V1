"""add unique competency state constraint

Revision ID: 3c4e7d8a1b2f
Revises: f79ac6f66ac6
Create Date: 2026-09-05

"""

from alembic import op


revision = "3c4e7d8a1b2f"
down_revision = "f79ac6f66ac6"
branch_labels = None
depends_on = None


_CONSTRAINT_NAME = "uq_competency_state_user_competency"
_TABLE_NAME = "competency_states"


def upgrade() -> None:
    with op.batch_alter_table(_TABLE_NAME) as batch_op:
        batch_op.create_unique_constraint(_CONSTRAINT_NAME, ["user_id", "competency_id"])


def downgrade() -> None:
    with op.batch_alter_table(_TABLE_NAME) as batch_op:
        batch_op.drop_constraint(_CONSTRAINT_NAME, type_="unique")
