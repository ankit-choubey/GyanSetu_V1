"""add Phase 3 intervention and recommendation intelligence

Revision ID: b1c2d3e4f5a6
Revises: ac1d2e3f4a5b
Create Date: 2026-09-07

"""

from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "ac1d2e3f4a5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("interventions") as batch_op:
        batch_op.add_column(sa.Column("provider", sa.String(length=100), server_default="INTERNAL", nullable=False))
        batch_op.add_column(sa.Column("modality", sa.String(length=50), server_default="ONLINE_SELF_PACED", nullable=False))
        batch_op.add_column(sa.Column("duration_minutes", sa.Integer(), server_default="60", nullable=True))
        batch_op.add_column(sa.Column("difficulty", sa.String(length=20), server_default="intermediate", nullable=False))
        batch_op.add_column(sa.Column("prerequisites_json", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("availability", sa.String(length=50), server_default="ALWAYS_AVAILABLE", nullable=False))
        batch_op.add_column(sa.Column("status", sa.String(length=50), server_default="ACTIVE", nullable=False))
        batch_op.add_column(sa.Column("source", sa.String(length=100), server_default="SYSTEM", nullable=False))
        batch_op.add_column(sa.Column("source_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("source_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("provenance", sa.String(length=100), server_default="[CURATED]", nullable=False))
        batch_op.add_column(sa.Column("version", sa.String(length=20), server_default="v1.0", nullable=False))
        batch_op.add_column(sa.Column("last_verified_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("target_misconception_pattern", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_interventions_provider", ["provider"], unique=False)
        batch_op.create_index("ix_interventions_status", ["status"], unique=False)
        batch_op.create_index("ix_interventions_source_id", ["source_id"], unique=False)
        batch_op.create_index("ix_interventions_target_misconception_pattern", ["target_misconception_pattern"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("interventions") as batch_op:
        batch_op.drop_index("ix_interventions_target_misconception_pattern")
        batch_op.drop_index("ix_interventions_source_id")
        batch_op.drop_index("ix_interventions_status")
        batch_op.drop_index("ix_interventions_provider")
        batch_op.drop_column("target_misconception_pattern")
        batch_op.drop_column("last_verified_at")
        batch_op.drop_column("version")
        batch_op.drop_column("provenance")
        batch_op.drop_column("source_url")
        batch_op.drop_column("source_id")
        batch_op.drop_column("source")
        batch_op.drop_column("status")
        batch_op.drop_column("availability")
        batch_op.drop_column("prerequisites_json")
        batch_op.drop_column("difficulty")
        batch_op.drop_column("duration_minutes")
        batch_op.drop_column("modality")
        batch_op.drop_column("provider")
