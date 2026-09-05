"""constrain evidence type taxonomy

Revision ID: 5d6e8f9a2b3c
Revises: 3c4e7d8a1b2f
Create Date: 2026-09-05

"""

from alembic import op
import sqlalchemy as sa


revision = "5d6e8f9a2b3c"
down_revision = "3c4e7d8a1b2f"
branch_labels = None
depends_on = None

_EVIDENCE_TYPES = (
    "KNOWLEDGE_ASSESSMENT",
    "APPLICATION_SCENARIO",
    "PRACTICAL_TASK",
    "TRAINING_HISTORY",
    "SELF_REPORT",
    "WORKPLACE_SIGNAL",
)


def upgrade() -> None:
    op.execute("UPDATE evidence SET evidence_type = 'TRAINING_HISTORY' WHERE evidence_type = 'PROFILE'")
    evidence_type = sa.Enum(*_EVIDENCE_TYPES, name="evidencetype", native_enum=False, create_constraint=True)
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.alter_column(
            "evidence_type",
            existing_type=sa.String(length=50),
            type_=evidence_type,
            existing_nullable=False,
        )


def downgrade() -> None:
    evidence_type = sa.Enum(*_EVIDENCE_TYPES, name="evidencetype", native_enum=False, create_constraint=True)
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.alter_column(
            "evidence_type",
            existing_type=evidence_type,
            type_=sa.String(length=50),
            existing_nullable=False,
        )
