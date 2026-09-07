from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .assessment import AssessmentAttempt, AssessmentItem
    from .scenario import ScenarioAttempt
    from .competency import Competency, Role
    from .competency_state import CompetencyState
    from .evidence import Evidence
    from .intervention import Intervention


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=255)
    password_hash: str = Field(max_length=500)
    role_id: int | None = Field(default=None, foreign_key="roles.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    role: Optional["Role"] = Relationship(back_populates="users")
    evidence: list["Evidence"] = Relationship(back_populates="user")
    assessments: list["AssessmentItem"] = Relationship(back_populates="user")
    assessment_attempts: list["AssessmentAttempt"] = Relationship(back_populates="user")
    scenario_attempts: list["ScenarioAttempt"] = Relationship(back_populates="user")
    interventions: list["Intervention"] = Relationship(back_populates="user")
    competency_states: list["CompetencyState"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    email: str
    full_name: str
    password: str
    role_id: int | None = None


class UserRead(SQLModel):
    id: int
    email: str
    full_name: str
    role_id: int | None = None
    is_active: bool = True
