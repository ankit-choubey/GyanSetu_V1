"""repair role competency links if revision was partially applied

Revision ID: 7f8a9b0c1d2e
Revises: 6e7f8a9b0c1d
Create Date: 2026-09-06

"""

from alembic import op
import sqlalchemy as sa


revision = "7f8a9b0c1d2e"
down_revision = "6e7f8a9b0c1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "role_competencies" not in inspector.get_table_names():
        op.create_table(
            "role_competencies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("competency_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
            sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("role_id", "competency_id", name="uq_role_competency"),
        )
    existing_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("role_competencies")}
    if "ix_role_competencies_role_id" not in existing_indexes:
        op.create_index("ix_role_competencies_role_id", "role_competencies", ["role_id"], unique=False)
    if "ix_role_competencies_competency_id" not in existing_indexes:
        op.create_index("ix_role_competencies_competency_id", "role_competencies", ["competency_id"], unique=False)
    op.get_bind().execute(
        sa.text(
            "INSERT INTO role_competencies (role_id, competency_id, created_at) "
            "SELECT c.role_id, c.id, CURRENT_TIMESTAMP FROM competencies c "
            "WHERE c.role_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM role_competencies rc "
            "WHERE rc.role_id = c.role_id AND rc.competency_id = c.id)"
        )
    )


def downgrade() -> None:
    if "role_competencies" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_index("ix_role_competencies_competency_id", table_name="role_competencies", if_exists=True)
        op.drop_index("ix_role_competencies_role_id", table_name="role_competencies", if_exists=True)
        op.drop_table("role_competencies")
