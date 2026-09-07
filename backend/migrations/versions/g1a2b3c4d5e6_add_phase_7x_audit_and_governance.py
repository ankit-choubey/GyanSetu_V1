"""add phase 7x audit and governance

Revision ID: g1a2b3c4d5e6
Revises: f1a2b3c4d5e6
Create Date: 2026-09-08 00:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1a2b3c4d5e6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_role', sa.String(length=100), server_default='SYSTEM', nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('result', sa.String(length=50), server_default='SUCCESS', nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=100), server_default='SYSTEM', nullable=True),
        sa.Column('provider', sa.String(length=100), nullable=True),
        sa.Column('before_state_json', sa.Text(), nullable=True),
        sa.Column('after_state_json', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_event_id', 'audit_events', ['event_id'], unique=True)
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'], unique=False)
    op.create_index('ix_audit_events_actor_id', 'audit_events', ['actor_id'], unique=False)
    op.create_index('ix_audit_events_actor_role', 'audit_events', ['actor_role'], unique=False)
    op.create_index('ix_audit_events_action', 'audit_events', ['action'], unique=False)
    op.create_index('ix_audit_events_entity_type', 'audit_events', ['entity_type'], unique=False)
    op.create_index('ix_audit_events_entity_id', 'audit_events', ['entity_id'], unique=False)
    op.create_index('ix_audit_events_correlation_id', 'audit_events', ['correlation_id'], unique=False)
    op.create_index('ix_audit_events_result', 'audit_events', ['result'], unique=False)
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_events_created_at', table_name='audit_events')
    op.drop_index('ix_audit_events_result', table_name='audit_events')
    op.drop_index('ix_audit_events_correlation_id', table_name='audit_events')
    op.drop_index('ix_audit_events_entity_id', table_name='audit_events')
    op.drop_index('ix_audit_events_entity_type', table_name='audit_events')
    op.drop_index('ix_audit_events_action', table_name='audit_events')
    op.drop_index('ix_audit_events_actor_role', table_name='audit_events')
    op.drop_index('ix_audit_events_actor_id', table_name='audit_events')
    op.drop_index('ix_audit_events_timestamp', table_name='audit_events')
    op.drop_index('ix_audit_events_event_id', table_name='audit_events')
    op.drop_table('audit_events')
