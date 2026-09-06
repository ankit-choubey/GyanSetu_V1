from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .evidence import Evidence
    from .user import User


class Misconception(SQLModel, table=True):
    __tablename__ = "misconceptions"
    __table_args__ = (
        CheckConstraint("occurrences >= 0", name="ck_misconception_occurrences_nonnegative"),
        Index(
            "ix_misconception_pattern_scope",
            "learner_id",
            "competency_id",
            "subskill_id",
            "pattern_key",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    learner_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    pattern_key: str | None = Field(default=None, max_length=255)
    misconception_type: str = Field(max_length=100, index=True)
    description: str = Field(max_length=4000)
    occurrences: int = Field(default=0, ge=0)
    first_observed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_observed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    intervention_applied: bool = Field(default=False)
    resolved: bool = Field(default=False, index=True)
    resolution_evidence_id: int | None = Field(default=None, foreign_key="evidence.id", index=True)

    learner: "User" = Relationship()
    competency: "Competency" = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    resolution_evidence: Optional["Evidence"] = Relationship()