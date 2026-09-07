"""add phase 5x scenario and content models

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-09-07 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. scenarios table
    if 'scenarios' not in existing_tables:
        op.create_table(
            'scenarios',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.String(), server_default='', nullable=False),
            sa.Column('scenario_type', sa.String(length=50), server_default='OPERATIONAL_PROCEDURE', nullable=False),
            sa.Column('role_id', sa.Integer(), nullable=True),
            sa.Column('competency_id', sa.Integer(), nullable=False),
            sa.Column('subskill_id', sa.Integer(), nullable=True),
            sa.Column('difficulty', sa.String(length=20), server_default='medium', nullable=False),
            sa.Column('source', sa.String(length=100), server_default='MOSPI_OPERATIONAL', nullable=False),
            sa.Column('provenance', sa.String(length=100), server_default='[SANDBOX DATA]', nullable=False),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
            sa.Column('expected_outcomes_json', sa.String(), server_default='[]', nullable=False),
            sa.Column('evaluation_rubric_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('metadata_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
            sa.ForeignKeyConstraint(['subskill_id'], ['subskills.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_scenarios_scenario_id', 'scenarios', ['scenario_id'], unique=True)
        op.create_index('ix_scenarios_competency_id', 'scenarios', ['competency_id'], unique=False)
        op.create_index('ix_scenarios_role_id', 'scenarios', ['role_id'], unique=False)
        op.create_index('ix_scenarios_subskill_id', 'scenarios', ['subskill_id'], unique=False)

    # 2. scenario_evaluations table
    if 'scenario_evaluations' not in existing_tables:
        op.create_table(
            'scenario_evaluations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('attempt_id', sa.Integer(), nullable=False),
            sa.Column('score', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('max_score', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('normalized_score', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('passed', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('competency_evidence_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('subskill_evidence_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('rubric_results_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('evaluator_type', sa.String(length=50), server_default='DETERMINISTIC', nullable=False),
            sa.Column('evaluator_version', sa.String(length=50), server_default='v1.0', nullable=False),
            sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('review_required', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('provenance', sa.String(length=100), server_default='[SANDBOX DATA]', nullable=False),
            sa.Column('feedback', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_scenario_evaluations_attempt_id', 'scenario_evaluations', ['attempt_id'], unique=True)

    # 3. scenario_attempts table
    if 'scenario_attempts' not in existing_tables:
        op.create_table(
            'scenario_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('attempt_id', sa.String(length=128), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=30), server_default='STARTED', nullable=False),
            sa.Column('scenario_version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('score', sa.Float(), nullable=True),
            sa.Column('evaluation_id', sa.Integer(), nullable=True),
            sa.Column('idempotency_key', sa.String(length=128), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['evaluation_id'], ['scenario_evaluations.id'], ),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_scenario_attempts_attempt_id', 'scenario_attempts', ['attempt_id'], unique=True)
        op.create_index('ix_scenario_attempts_idempotency_key', 'scenario_attempts', ['idempotency_key'], unique=True)
        op.create_index('ix_scenario_attempts_scenario_id', 'scenario_attempts', ['scenario_id'], unique=False)
        op.create_index('ix_scenario_attempts_user_id', 'scenario_attempts', ['user_id'], unique=False)
        op.create_index('ix_scenario_attempts_evaluation_id', 'scenario_attempts', ['evaluation_id'], unique=False)

    # 4. scenario_responses table
    if 'scenario_responses' not in existing_tables:
        op.create_table(
            'scenario_responses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('attempt_id', sa.Integer(), nullable=False),
            sa.Column('response_payload_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('submitted_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['attempt_id'], ['scenario_attempts.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_scenario_responses_attempt_id', 'scenario_responses', ['attempt_id'], unique=False)

    # 5. content_assets table
    if 'content_assets' not in existing_tables:
        op.create_table(
            'content_assets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('asset_id', sa.String(length=100), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('media_type', sa.String(length=100), nullable=False),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
            sa.Column('storage_path', sa.String(length=500), server_default='', nullable=False),
            sa.Column('source', sa.String(length=100), server_default='MOSPI_TRAINING', nullable=False),
            sa.Column('provenance', sa.String(length=100), server_default='[SANDBOX DATA]', nullable=False),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='UPLOADED', nullable=False),
            sa.Column('error_message', sa.String(length=1000), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_content_assets_asset_id', 'content_assets', ['asset_id'], unique=True)
        op.create_index('ix_content_assets_checksum_sha256', 'content_assets', ['checksum_sha256'], unique=False)
        op.create_index('ix_content_assets_status', 'content_assets', ['status'], unique=False)

    # 6. content_versions table
    if 'content_versions' not in existing_tables:
        op.create_table(
            'content_versions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('asset_id', sa.Integer(), nullable=False),
            sa.Column('version_number', sa.Integer(), server_default='1', nullable=False),
            sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('change_summary', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['asset_id'], ['content_assets.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_content_versions_asset_id', 'content_versions', ['asset_id'], unique=False)

    # 7. content_chunks table
    if 'content_chunks' not in existing_tables:
        op.create_table(
            'content_chunks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('asset_id', sa.Integer(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=True),
            sa.Column('chunk_index', sa.Integer(), server_default='0', nullable=False),
            sa.Column('chunk_type', sa.String(length=50), server_default='TEXT', nullable=False),
            sa.Column('content', sa.String(), server_default='', nullable=False),
            sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('metadata_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['asset_id'], ['content_assets.id'], ),
            sa.ForeignKeyConstraint(['version_id'], ['content_versions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_content_chunks_asset_id', 'content_chunks', ['asset_id'], unique=False)
        op.create_index('ix_content_chunks_version_id', 'content_chunks', ['version_id'], unique=False)

    # 8. processing_jobs table
    if 'processing_jobs' not in existing_tables:
        op.create_table(
            'processing_jobs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.String(length=128), nullable=False),
            sa.Column('asset_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=30), server_default='QUEUED', nullable=False),
            sa.Column('current_stage', sa.String(length=50), server_default='UPLOADED', nullable=False),
            sa.Column('stage_progress_json', sa.String(), server_default='{}', nullable=False),
            sa.Column('error_details', sa.String(), nullable=True),
            sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['asset_id'], ['content_assets.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_processing_jobs_job_id', 'processing_jobs', ['job_id'], unique=True)
        op.create_index('ix_processing_jobs_asset_id', 'processing_jobs', ['asset_id'], unique=False)
        op.create_index('ix_processing_jobs_status', 'processing_jobs', ['status'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'processing_jobs' in existing_tables:
        op.drop_table('processing_jobs')

    if 'content_chunks' in existing_tables:
        op.drop_table('content_chunks')

    if 'content_versions' in existing_tables:
        op.drop_table('content_versions')

    if 'content_assets' in existing_tables:
        op.drop_table('content_assets')

    if 'scenario_responses' in existing_tables:
        op.drop_table('scenario_responses')

    if 'scenario_attempts' in existing_tables:
        op.drop_table('scenario_attempts')

    if 'scenario_evaluations' in existing_tables:
        op.drop_table('scenario_evaluations')

    if 'scenarios' in existing_tables:
        op.drop_table('scenarios')
