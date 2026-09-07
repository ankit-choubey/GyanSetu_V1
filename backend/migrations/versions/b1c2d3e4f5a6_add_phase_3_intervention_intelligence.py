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

    op.create_table(
        "intervention_outcomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("intervention_id", sa.Integer(), nullable=False),
        sa.Column("recommendation_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="COMPLETED", nullable=False),
        sa.Column("completion_score", sa.Float(), nullable=True),
        sa.Column("has_post_assessment_evidence", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=True),
        sa.Column("pre_competency_mastery", sa.Float(), nullable=True),
        sa.Column("post_competency_mastery", sa.Float(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"]),
        sa.ForeignKeyConstraint(["intervention_id"], ["interventions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intervention_outcomes_evidence_id", "intervention_outcomes", ["evidence_id"], unique=False)
    op.create_index("ix_intervention_outcomes_idempotency_key", "intervention_outcomes", ["idempotency_key"], unique=True)
    op.create_index("ix_intervention_outcomes_intervention_id", "intervention_outcomes", ["intervention_id"], unique=False)
    op.create_index("ix_intervention_outcomes_recommendation_id", "intervention_outcomes", ["recommendation_id"], unique=False)
    op.create_index("ix_intervention_outcomes_status", "intervention_outcomes", ["status"], unique=False)
    op.create_index("ix_intervention_outcomes_user_id", "intervention_outcomes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_intervention_outcomes_user_id", table_name="intervention_outcomes")
    op.drop_index("ix_intervention_outcomes_status", table_name="intervention_outcomes")
    op.drop_index("ix_intervention_outcomes_recommendation_id", table_name="intervention_outcomes")
    op.drop_index("ix_intervention_outcomes_intervention_id", table_name="intervention_outcomes")
    op.drop_index("ix_intervention_outcomes_idempotency_key", table_name="intervention_outcomes")
    op.drop_index("ix_intervention_outcomes_evidence_id", table_name="intervention_outcomes")
    op.drop_table("intervention_outcomes")

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

