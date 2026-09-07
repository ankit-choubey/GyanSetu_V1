"""create scenario assessment tables

Revision ID: b1c2d3e4f5a6
Revises: ac1d2e3f4a5b
Create Date: 2026-09-07

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "b1c2d3e4f5a6"
down_revision = "ac1d2e3f4a5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scenario_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("scenario_text", sqlmodel.sql.sqltypes.AutoString(length=6000), nullable=False),
        sa.Column("context_data", sqlmodel.sql.sqltypes.AutoString(length=6000), nullable=True),
        sa.Column("question", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("response_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("instructions", sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
        sa.Column("expected_reasoning", sqlmodel.sql.sqltypes.AutoString(length=6000), nullable=False),
        sa.Column("rubric", sqlmodel.sql.sqltypes.AutoString(length=6000), nullable=False),
        sa.Column("difficulty", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("cognitive_level", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("source_reference", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scenario_items_competency_id",
        "scenario_items",
        ["competency_id"],
        unique=False,
    )
    op.create_index(
        "ix_scenario_items_subskill_id",
        "scenario_items",
        ["subskill_id"],
        unique=False,
    )

    op.create_table(
        "scenario_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("response_text", sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.Column("overall_result", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("evaluation_feedback", sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=True),
        sa.Column("evaluation_criterion_results", sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("demonstrated_competency", sa.Boolean(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 10)",
            name="ck_scenario_attempt_score_range",
        ),
        sa.CheckConstraint(
            "percentage IS NULL OR (percentage >= 0 AND percentage <= 100)",
            name="ck_scenario_attempt_percentage_range",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scenario_attempt_confidence_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenario_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scenario_attempts_user_id",
        "scenario_attempts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_scenario_attempts_scenario_id",
        "scenario_attempts",
        ["scenario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scenario_attempts_scenario_id", table_name="scenario_attempts")
    op.drop_index("ix_scenario_attempts_user_id", table_name="scenario_attempts")
    op.drop_table("scenario_attempts")
    op.drop_index("ix_scenario_items_subskill_id", table_name="scenario_items")
    op.drop_index("ix_scenario_items_competency_id", table_name="scenario_items")
    op.drop_table("scenario_items")