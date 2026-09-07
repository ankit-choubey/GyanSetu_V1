"""add phase 7 governance and workforce audit

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-09-07 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'competency_governance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), server_default='v1.0', nullable=False),
        sa.Column('review_status', sa.String(length=50), server_default='CURATED', nullable=False),
        sa.Column('mapping_provenance', sa.String(length=100), server_default='[CURATED:MOSPI_TAXONOMY]', nullable=False),
        sa.Column('expert_review_notes', sa.String(length=1000), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('is_deprecated', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_competency_governance_competency_id', 'competency_governance', ['competency_id'], unique=True)
    op.create_index('ix_competency_governance_review_status', 'competency_governance', ['review_status'], unique=False)
    op.create_index('ix_competency_governance_is_deprecated', 'competency_governance', ['is_deprecated'], unique=False)

    op.create_table(
        'model_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), server_default='v1.0', nullable=False),
        sa.Column('model_type', sa.String(length=100), nullable=False),
        sa.Column('scientific_status', sa.String(length=50), server_default='PRODUCTION BASELINE', nullable=False),
        sa.Column('training_data_description', sa.String(length=500), nullable=False),
        sa.Column('evaluation_reference', sa.String(length=500), nullable=False),
        sa.Column('limitations', sa.String(length=1000), nullable=False),
        sa.Column('production_status', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_model_registry_name', 'model_registry', ['name'], unique=True)
    op.create_index('ix_model_registry_model_type', 'model_registry', ['model_type'], unique=False)
    op.create_index('ix_model_registry_scientific_status', 'model_registry', ['scientific_status'], unique=False)

    op.create_table(
        'workforce_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('actor_role', sa.String(length=100), server_default='ADMINISTRATOR', nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('requested_scope', sa.String(length=255), server_default='ALL', nullable=False),
        sa.Column('suppressed_groups_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('authorization_decision', sa.String(length=50), server_default='AUTHORIZED', nullable=False),
        sa.Column('insights_generated_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fairness_audit_status', sa.String(length=50), nullable=True),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workforce_audit_logs_actor_id', 'workforce_audit_logs', ['actor_id'], unique=False)
    op.create_index('ix_workforce_audit_logs_endpoint', 'workforce_audit_logs', ['endpoint'], unique=False)
    op.create_index('ix_workforce_audit_logs_created_at', 'workforce_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_workforce_audit_logs_created_at', table_name='workforce_audit_logs')
    op.drop_index('ix_workforce_audit_logs_endpoint', table_name='workforce_audit_logs')
    op.drop_index('ix_workforce_audit_logs_actor_id', table_name='workforce_audit_logs')
    op.drop_table('workforce_audit_logs')

    op.drop_index('ix_model_registry_scientific_status', table_name='model_registry')
    op.drop_index('ix_model_registry_model_type', table_name='model_registry')
    op.drop_index('ix_model_registry_name', table_name='model_registry')
    op.drop_table('model_registry')

    op.drop_index('ix_competency_governance_is_deprecated', table_name='competency_governance')
    op.drop_index('ix_competency_governance_review_status', table_name='competency_governance')
    op.drop_index('ix_competency_governance_competency_id', table_name='competency_governance')
    op.drop_table('competency_governance')
