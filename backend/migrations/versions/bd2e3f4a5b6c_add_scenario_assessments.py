"""add scenario assessment persistence

Revision ID: bd2e3f4a5b6c
Revises: ac1d2e3f4a5b
Create Date: 2026-09-07

"""

from alembic import op
import sqlalchemy as sa


revision = "bd2e3f4a5b6c"
down_revision = "ac1d2e3f4a5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scenario_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.String(length=255), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("context", sa.String(length=10000), nullable=False),
        sa.Column("context_data", sa.JSON(), nullable=False),
        sa.Column("task_question", sa.String(length=5000), nullable=False),
        sa.Column("response_type", sa.String(length=50), nullable=False),
        sa.Column("instructions", sa.String(length=5000), nullable=False),
        sa.Column("expected_reasoning", sa.JSON(), nullable=False),
        sa.Column("rubric", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("cognitive_level", sa.String(length=20), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("generator_metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_id", name="uq_scenario_item_scenario_id"),
    )
    op.create_index("ix_scenario_items_scenario_id", "scenario_items", ["scenario_id"], unique=False)
    op.create_index("ix_scenario_items_competency_id", "scenario_items", ["competency_id"], unique=False)
    op.create_index("ix_scenario_items_subskill_id", "scenario_items", ["subskill_id"], unique=False)
    op.create_index("ix_scenario_items_status", "scenario_items", ["status"], unique=False)

    op.create_table(
        "scenario_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_item_id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("submitted_response", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('ATTEMPTED', 'SUBMITTED', 'PENDING_EVALUATION', 'EVALUATED', 'PROVIDER_UNAVAILABLE', 'FAILED')",
            name="ck_scenario_attempt_status",
        ),
        sa.ForeignKeyConstraint(["scenario_item_id"], ["scenario_items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenario_attempts_scenario_item_id", "scenario_attempts", ["scenario_item_id"], unique=False)
    op.create_index("ix_scenario_attempts_scenario_id", "scenario_attempts", ["scenario_id"], unique=False)
    op.create_index("ix_scenario_attempts_user_id", "scenario_attempts", ["user_id"], unique=False)
    op.create_index("ix_scenario_attempts_competency_id", "scenario_attempts", ["competency_id"], unique=False)
    op.create_index("ix_scenario_attempts_subskill_id", "scenario_attempts", ["subskill_id"], unique=False)
    op.create_index("ix_scenario_attempts_status", "scenario_attempts", ["status"], unique=False)

    op.create_table(
        "scenario_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_attempt_id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.String(length=255), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("overall_result", sa.String(length=40), nullable=False),
        sa.Column("criterion_results", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.JSON(), nullable=False),
        sa.Column("demonstrated_competency", sa.Boolean(), nullable=False),
        sa.Column("evaluator_confidence", sa.Float(), nullable=False),
        sa.Column("evaluator_metadata", sa.JSON(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scenario_attempt_id"], ["scenario_attempts.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_attempt_id", name="uq_scenario_evaluation_attempt"),
    )
    op.create_index("ix_scenario_evaluations_scenario_attempt_id", "scenario_evaluations", ["scenario_attempt_id"], unique=False)
    op.create_index("ix_scenario_evaluations_scenario_id", "scenario_evaluations", ["scenario_id"], unique=False)
    op.create_index("ix_scenario_evaluations_competency_id", "scenario_evaluations", ["competency_id"], unique=False)
    op.create_index("ix_scenario_evaluations_subskill_id", "scenario_evaluations", ["subskill_id"], unique=False)


def downgrade() -> None:
    for index_name in (
        "ix_scenario_evaluations_subskill_id",
        "ix_scenario_evaluations_competency_id",
        "ix_scenario_evaluations_scenario_id",
        "ix_scenario_evaluations_scenario_attempt_id",
    ):
        op.drop_index(index_name, table_name="scenario_evaluations")
    op.drop_table("scenario_evaluations")

    for index_name in (
        "ix_scenario_attempts_status",
        "ix_scenario_attempts_subskill_id",
        "ix_scenario_attempts_competency_id",
        "ix_scenario_attempts_user_id",
        "ix_scenario_attempts_scenario_id",
        "ix_scenario_attempts_scenario_item_id",
    ):
        op.drop_index(index_name, table_name="scenario_attempts")
    op.drop_table("scenario_attempts")

    for index_name in (
        "ix_scenario_items_status",
        "ix_scenario_items_subskill_id",
        "ix_scenario_items_competency_id",
        "ix_scenario_items_scenario_id",
    ):
        op.drop_index(index_name, table_name="scenario_items")
    op.drop_table("scenario_items")