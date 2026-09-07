"""add phase 4 ecosystem adapters and provider tracking

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-09-07 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('interventions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('integration_mode', sa.String(length=20), server_default='REPLAY', nullable=False))
        batch_op.add_column(sa.Column('external_metadata_json', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('mapping_status', sa.String(length=50), server_default='CURATED', nullable=False))
        batch_op.add_column(sa.Column('mapping_confidence', sa.Float(), server_default='1.0', nullable=False))
        batch_op.add_column(sa.Column('last_synced_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_interventions_integration_mode', ['integration_mode'], unique=False)
        batch_op.create_index('ix_interventions_mapping_status', ['mapping_status'], unique=False)

    with op.batch_alter_table('intervention_outcomes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('provider', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('provider_resource_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('provider_activity_id', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('integration_mode', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('started_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_intervention_outcomes_provider', ['provider'], unique=False)
        batch_op.create_index('ix_intervention_outcomes_provider_activity_id', ['provider_activity_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('intervention_outcomes', schema=None) as batch_op:
        batch_op.drop_index('ix_intervention_outcomes_provider_activity_id')
        batch_op.drop_index('ix_intervention_outcomes_provider')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('started_at')
        batch_op.drop_column('integration_mode')
        batch_op.drop_column('provider_activity_id')
        batch_op.drop_column('provider_resource_id')
        batch_op.drop_column('provider')

    with op.batch_alter_table('interventions', schema=None) as batch_op:
        batch_op.drop_index('ix_interventions_mapping_status')
        batch_op.drop_index('ix_interventions_integration_mode')
        batch_op.drop_column('last_synced_at')
        batch_op.drop_column('mapping_confidence')
        batch_op.drop_column('mapping_status')
        batch_op.drop_column('external_metadata_json')
        batch_op.drop_column('integration_mode')
