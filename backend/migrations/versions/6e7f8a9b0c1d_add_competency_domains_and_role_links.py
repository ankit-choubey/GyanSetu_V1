"""add competency domains and role competency links

Revision ID: 6e7f8a9b0c1d
Revises: 5d6e8f9a2b3c
Create Date: 2026-09-06

"""

from alembic import op
import sqlalchemy as sa


revision = "6e7f8a9b0c1d"
down_revision = "5d6e8f9a2b3c"
branch_labels = None
depends_on = None

_DOMAIN_VALUES = (
    "Statistical",
    "Technical/Digital",
    "Digital Governance",
    "Behavioural/Managerial",
)
_LEGACY_DOMAINS = {
    "Sampling Design": "Statistical",
    "Data Quality": "Statistical",
    "Python for Analytics": "Technical/Digital",
}


def upgrade() -> None:
    domain_type = sa.Enum(*_DOMAIN_VALUES, name="competencydomain", native_enum=False, create_constraint=True)
    with op.batch_alter_table("competencies") as batch_op:
        batch_op.add_column(sa.Column("domain", domain_type, nullable=True))
        batch_op.create_index("ix_competencies_domain", ["domain"], unique=False)

    connection = op.get_bind()
    legacy_rows = connection.execute(sa.text("SELECT id, name FROM competencies")).mappings().all()
    unknown = sorted({row["name"] for row in legacy_rows if row["name"] not in _LEGACY_DOMAINS})
    if unknown:
        raise RuntimeError(
            "Cannot migrate legacy competencies without explicit domain mappings: "
            + ", ".join(unknown)
        )
    for row in legacy_rows:
        connection.execute(
            sa.text("UPDATE competencies SET domain = :domain WHERE id = :id"),
            {"domain": _LEGACY_DOMAINS[row["name"]], "id": row["id"]},
        )

    with op.batch_alter_table("competencies") as batch_op:
        batch_op.alter_column("domain", existing_type=domain_type, nullable=False)

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
    op.create_index("ix_role_competencies_role_id", "role_competencies", ["role_id"], unique=False)
    op.create_index("ix_role_competencies_competency_id", "role_competencies", ["competency_id"], unique=False)
    connection.execute(
        sa.text(
            "INSERT INTO role_competencies (role_id, competency_id, created_at) "
            "SELECT role_id, id, CURRENT_TIMESTAMP FROM competencies WHERE role_id IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_role_competencies_competency_id", table_name="role_competencies")
    op.drop_index("ix_role_competencies_role_id", table_name="role_competencies")
    op.drop_table("role_competencies")
    domain_type = sa.Enum(*_DOMAIN_VALUES, name="competencydomain", native_enum=False, create_constraint=True)
    with op.batch_alter_table("competencies") as batch_op:
        batch_op.drop_index("ix_competencies_domain")
        batch_op.drop_column("domain")
