"""add phase 5 practical tasks and practical attempts

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-09-07 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'practical_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('subskill_id', sa.Integer(), nullable=True),
        sa.Column('scenario_type', sa.String(length=50), server_default='STATISTICAL_PROCEDURE', nullable=False),
        sa.Column('difficulty', sa.String(length=20), server_default='medium', nullable=False),
        sa.Column('scenario_context', sa.Text(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('input_artifacts_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('expected_output_type', sa.String(length=50), server_default='NUMERICAL_JSON', nullable=False),
        sa.Column('rubric_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('rubric_version', sa.String(length=50), server_default='v1.0-rubric', nullable=False),
        sa.Column('prerequisites_json', sa.Text(), nullable=True),
        sa.Column('provenance', sa.String(length=100), server_default='[CURATED:SIMULATION]', nullable=False),
        sa.Column('source', sa.String(length=100), server_default='MOSPI_SIMULATION', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ),
        sa.ForeignKeyConstraint(['subskill_id'], ['subskills.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_practical_tasks_task_id', 'practical_tasks', ['task_id'], unique=True)
    op.create_index('ix_practical_tasks_competency_id', 'practical_tasks', ['competency_id'], unique=False)
    op.create_index('ix_practical_tasks_subskill_id', 'practical_tasks', ['subskill_id'], unique=False)

    op.create_table(
        'practical_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.String(length=128), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='CREATED', nullable=False),
        sa.Column('task_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('rubric_version', sa.String(length=50), server_default='v1.0-rubric', nullable=False),
        sa.Column('submission_payload_json', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('evaluator_type', sa.String(length=50), nullable=True),
        sa.Column('evaluator_version', sa.String(length=50), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('evaluation_result_json', sa.Text(), nullable=True),
        sa.Column('evidence_id', sa.Integer(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['practical_tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_practical_attempts_attempt_id', 'practical_attempts', ['attempt_id'], unique=True)
    op.create_index('ix_practical_attempts_task_id', 'practical_attempts', ['task_id'], unique=False)
    op.create_index('ix_practical_attempts_user_id', 'practical_attempts', ['user_id'], unique=False)
    op.create_index('ix_practical_attempts_evidence_id', 'practical_attempts', ['evidence_id'], unique=False)
    op.create_index('ix_practical_attempts_idempotency_key', 'practical_attempts', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_practical_attempts_idempotency_key', table_name='practical_attempts')
    op.drop_index('ix_practical_attempts_evidence_id', table_name='practical_attempts')
    op.drop_index('ix_practical_attempts_user_id', table_name='practical_attempts')
    op.drop_index('ix_practical_attempts_task_id', table_name='practical_attempts')
    op.drop_index('ix_practical_attempts_attempt_id', table_name='practical_attempts')
    op.drop_table('practical_attempts')

    op.drop_index('ix_practical_tasks_subskill_id', table_name='practical_tasks')
    op.drop_index('ix_practical_tasks_competency_id', table_name='practical_tasks')
    op.drop_index('ix_practical_tasks_task_id', table_name='practical_tasks')
    op.drop_table('practical_tasks')
