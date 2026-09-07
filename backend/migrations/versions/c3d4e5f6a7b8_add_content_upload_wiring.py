"""add content upload wiring

Revision ID: c3d4e5f6a7b8
Revises: bd2e3f4a5b6c
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision = "c3d4e5f6a7b8"
down_revision = "bd2e3f4a5b6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("storage_reference", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("ml_status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column("source_reference", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id", name="uq_content_item_content_id"),
        sa.CheckConstraint("file_size >= 0", name="ck_content_item_file_size_nonnegative"),
    )
    op.create_index("ix_content_items_content_id", "content_items", ["content_id"], unique=False)
    op.create_index("ix_content_items_owner_id", "content_items", ["owner_id"], unique=False)
    op.create_index("ix_content_items_checksum", "content_items", ["checksum"], unique=False)
    op.create_index("ix_content_items_status", "content_items", ["status"], unique=False)

    op.create_table(
        "content_concepts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_item_id", sa.Integer(), nullable=False),
        sa.Column("concept", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("subskills", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["content_item_id"], ["content_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_concepts_content_item_id", "content_concepts", ["content_item_id"], unique=False)

    op.create_table(
        "content_competency_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_item_id", sa.Integer(), nullable=False),
        sa.Column("competency_id", sa.Integer(), nullable=False),
        sa.Column("subskill_id", sa.Integer(), nullable=True),
        sa.Column("concept", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("source_reference", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["content_item_id"], ["content_items.id"]),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
        sa.ForeignKeyConstraint(["subskill_id"], ["subskills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_content_mapping_confidence"),
    )
    op.create_index("ix_content_competency_mappings_content_item_id", "content_competency_mappings", ["content_item_id"], unique=False)
    op.create_index("ix_content_competency_mappings_competency_id", "content_competency_mappings", ["competency_id"], unique=False)
    op.create_index("ix_content_competency_mappings_subskill_id", "content_competency_mappings", ["subskill_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_content_competency_mappings_subskill_id", table_name="content_competency_mappings")
    op.drop_index("ix_content_competency_mappings_competency_id", table_name="content_competency_mappings")
    op.drop_index("ix_content_competency_mappings_content_item_id", table_name="content_competency_mappings")
    op.drop_table("content_competency_mappings")
    op.drop_index("ix_content_concepts_content_item_id", table_name="content_concepts")
    op.drop_table("content_concepts")
    op.drop_index("ix_content_items_status", table_name="content_items")
    op.drop_index("ix_content_items_checksum", table_name="content_items")
    op.drop_index("ix_content_items_owner_id", table_name="content_items")
    op.drop_index("ix_content_items_content_id", table_name="content_items")
    op.drop_table("content_items")