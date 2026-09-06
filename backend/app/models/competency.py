from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Enum as SAEnum, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .assessment import AssessmentAttempt, AssessmentItem
    from .competency_state import CompetencyState
    from .evidence import Evidence
    from .intervention import Intervention
    from .user import User


class CompetencyDomain(str, Enum):
    STATISTICAL = "Statistical"
    TECHNICAL_DIGITAL = "Technical/Digital"
    DIGITAL_GOVERNANCE = "Digital Governance"
    BEHAVIOURAL_MANAGERIAL = "Behavioural/Managerial"


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=255)
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    users: list["User"] = Relationship(back_populates="role")
    competencies: list["Competency"] = Relationship(back_populates="role")
    role_competency_links: list["RoleCompetency"] = Relationship(back_populates="role")


class Competency(SQLModel, table=True):
    __tablename__ = "competencies"

    id: int | None = Field(default=None, primary_key=True)
    # Deprecated compatibility field. RoleCompetency is authoritative.
    role_id: int | None = Field(default=None, foreign_key="roles.id", index=True)
    name: str = Field(index=True, max_length=255)
    domain: CompetencyDomain = Field(
        default=CompetencyDomain.STATISTICAL,
        sa_column=Column(
            SAEnum(
                CompetencyDomain,
                values_callable=lambda enum: [item.value for item in enum],
                native_enum=False,
                create_constraint=True,
                name="competencydomain",
            ),
            nullable=False,
            index=True,
        ),
    )
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    role: Optional["Role"] = Relationship(back_populates="competencies")
    subskills: list["SubSkill"] = Relationship(back_populates="competency")
    evidence: list["Evidence"] = Relationship(back_populates="competency")
    assessments: list["AssessmentItem"] = Relationship(back_populates="competency")
    assessment_attempts: list["AssessmentAttempt"] = Relationship(back_populates="competency")
    interventions: list["Intervention"] = Relationship(back_populates="competency")
    competency_states: list["CompetencyState"] = Relationship(back_populates="competency")
    role_competency_links: list["RoleCompetency"] = Relationship(back_populates="competency")


class SubSkill(SQLModel, table=True):
    __tablename__ = "subskills"

    id: int | None = Field(default=None, primary_key=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    name: str = Field(index=True, max_length=255)
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: Optional["Competency"] = Relationship(back_populates="subskills")
    evidence: list["Evidence"] = Relationship(back_populates="subskill")
    assessments: list["AssessmentItem"] = Relationship(back_populates="subskill")
    interventions: list["Intervention"] = Relationship(back_populates="subskill")


class RoleCompetency(SQLModel, table=True):
    __tablename__ = "role_competencies"
    __table_args__ = (UniqueConstraint("role_id", "competency_id", name="uq_role_competency"),)

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    role: "Role" = Relationship(back_populates="role_competency_links")
    competency: "Competency" = Relationship(back_populates="role_competency_links")
