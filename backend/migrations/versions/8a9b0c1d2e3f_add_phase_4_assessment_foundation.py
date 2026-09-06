"""add phase 4 assessment foundation

Revision ID: 8a9b0c1d2e3f
Revises: 7f8a9b0c1d2e
Create Date: 2026-09-06

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "8a9b0c1d2e3f"
down_revision = "7f8a9b0c1d2e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 1)", name="ck_attempt_score_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessment_attempts_user_id", "assessment_attempts", ["user_id"], unique=False)
    op.create_index("ix_assessment_attempts_competency_id", "assessment_attempts", ["competency_id"], unique=False)

    op.create_table(
        "assessment_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("assessment_item_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("selected_option", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["assessment_attempts.id"]),
        sa.ForeignKeyConstraint(["assessment_item_id"], ["assessment_items.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "assessment_item_id", name="uq_attempt_assessment_item_response"),
    )
    op.create_index("ix_assessment_responses_attempt_id", "assessment_responses", ["attempt_id"], unique=False)
    op.create_index("ix_assessment_responses_assessment_item_id", "assessment_responses", ["assessment_item_id"], unique=False)
    op.create_index("ix_assessment_responses_competency_id", "assessment_responses", ["competency_id"], unique=False)
    op.create_index("ix_assessment_responses_subskill_id", "assessment_responses", ["subskill_id"], unique=False)

    op.create_table(
        "assessment_signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("assessment_response_id", sa.Integer(), nullable=True),
        sa.Column("is_session_aggregate", sa.Boolean(), nullable=False),
        sa.Column("response_time", sa.Float(), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column("hints_requested", sa.Integer(), nullable=True),
        sa.Column("skips", sa.Integer(), nullable=True),
        sa.Column("repeated_errors", sa.Integer(), nullable=True),
        sa.Column("session_duration", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("response_time IS NULL OR response_time >= 0", name="ck_signal_response_time_nonnegative"),
        sa.CheckConstraint("retries IS NULL OR retries >= 0", name="ck_signal_retries_nonnegative"),
        sa.CheckConstraint("hints_requested IS NULL OR hints_requested >= 0", name="ck_signal_hints_nonnegative"),
        sa.CheckConstraint("skips IS NULL OR skips >= 0", name="ck_signal_skips_nonnegative"),
        sa.CheckConstraint("repeated_errors IS NULL OR repeated_errors >= 0", name="ck_signal_errors_nonnegative"),
        sa.CheckConstraint("session_duration IS NULL OR session_duration >= 0", name="ck_signal_duration_nonnegative"),
        sa.ForeignKeyConstraint(["attempt_id"], ["assessment_attempts.id"]),
        sa.ForeignKeyConstraint(["assessment_response_id"], ["assessment_responses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assessment_signals_attempt_id", "assessment_signals", ["attempt_id"], unique=False)
    op.create_index("ix_assessment_signals_assessment_response_id", "assessment_signals", ["assessment_response_id"], unique=False)
    op.create_index("ix_assessment_signals_is_session_aggregate", "assessment_signals", ["is_session_aggregate"], unique=False)

    op.create_table(
        "misconceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("misconception_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("occurrences", sa.Integer(), nullable=False),
        sa.Column("first_observed", sa.DateTime(), nullable=False),
        sa.Column("last_observed", sa.DateTime(), nullable=False),
        sa.Column("intervention_applied", sa.Boolean(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("resolution_evidence_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("occurrences >= 0", name="ck_misconception_occurrences_nonnegative"),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.ForeignKeyConstraint(["resolution_evidence_id"], ["evidence.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_misconceptions_learner_id", "misconceptions", ["learner_id"], unique=False)
    op.create_index("ix_misconceptions_competency_id", "misconceptions", ["competency_id"], unique=False)
    op.create_index("ix_misconceptions_subskill_id", "misconceptions", ["subskill_id"], unique=False)
    op.create_index("ix_misconceptions_misconception_type", "misconceptions", ["misconception_type"], unique=False)
    op.create_index("ix_misconceptions_last_observed", "misconceptions", ["last_observed"], unique=False)
    op.create_index("ix_misconceptions_resolved", "misconceptions", ["resolved"], unique=False)
    op.create_index("ix_misconceptions_resolution_evidence_id", "misconceptions", ["resolution_evidence_id"], unique=False)

    op.create_table(
        "monitoring_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("significance", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=True),
        sa.Column("competency_id", sa.Integer(), nullable=True),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("source_entity_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("source_entity_id", sa.Integer(), nullable=True),
        sa.Column("event_metadata", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_events_event_type", "monitoring_events", ["event_type"], unique=False)
    op.create_index("ix_monitoring_events_significance", "monitoring_events", ["significance"], unique=False)
    op.create_index("ix_monitoring_events_status", "monitoring_events", ["status"], unique=False)
    op.create_index("ix_monitoring_events_learner_id", "monitoring_events", ["learner_id"], unique=False)
    op.create_index("ix_monitoring_events_competency_id", "monitoring_events", ["competency_id"], unique=False)
    op.create_index("ix_monitoring_events_subskill_id", "monitoring_events", ["subskill_id"], unique=False)
    op.create_index("ix_monitoring_events_source_entity_id", "monitoring_events", ["source_entity_id"], unique=False)
    op.create_index("ix_monitoring_events_scheduled_for", "monitoring_events", ["scheduled_for"], unique=False)


def downgrade() -> None:
    for index_name in (
        "ix_monitoring_events_scheduled_for",
        "ix_monitoring_events_source_entity_id",
        "ix_monitoring_events_subskill_id",
        "ix_monitoring_events_competency_id",
        "ix_monitoring_events_learner_id",
        "ix_monitoring_events_status",
        "ix_monitoring_events_significance",
        "ix_monitoring_events_event_type",
    ):
        op.drop_index(index_name, table_name="monitoring_events")
    op.drop_table("monitoring_events")

    for index_name in (
        "ix_misconceptions_resolution_evidence_id",
        "ix_misconceptions_resolved",
        "ix_misconceptions_last_observed",
        "ix_misconceptions_misconception_type",
        "ix_misconceptions_subskill_id",
        "ix_misconceptions_competency_id",
        "ix_misconceptions_learner_id",
    ):
        op.drop_index(index_name, table_name="misconceptions")
    op.drop_table("misconceptions")

    for index_name in (
        "ix_assessment_signals_is_session_aggregate",
        "ix_assessment_signals_assessment_response_id",
        "ix_assessment_signals_attempt_id",
    ):
        op.drop_index(index_name, table_name="assessment_signals")
    op.drop_table("assessment_signals")

    for index_name in (
        "ix_assessment_responses_subskill_id",
        "ix_assessment_responses_competency_id",
        "ix_assessment_responses_assessment_item_id",
        "ix_assessment_responses_attempt_id",
    ):
        op.drop_index(index_name, table_name="assessment_responses")
    op.drop_table("assessment_responses")

    op.drop_index("ix_assessment_attempts_competency_id", table_name="assessment_attempts")
    op.drop_index("ix_assessment_attempts_user_id", table_name="assessment_attempts")
    op.drop_table("assessment_attempts")