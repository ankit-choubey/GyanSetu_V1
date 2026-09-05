from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class EvidenceType(str, Enum):
    KNOWLEDGE_ASSESSMENT = "KNOWLEDGE_ASSESSMENT"
    APPLICATION_SCENARIO = "APPLICATION_SCENARIO"
    PRACTICAL_TASK = "PRACTICAL_TASK"
    TRAINING_HISTORY = "TRAINING_HISTORY"
    SELF_REPORT = "SELF_REPORT"
    WORKPLACE_SIGNAL = "WORKPLACE_SIGNAL"


class Evidence(SQLModel, table=True):
    __tablename__ = "evidence"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    evidence_type: EvidenceType = Field(index=True, max_length=50)
    title: str = Field(max_length=255)
    description: str | None = None
    score: float | None = None
    weight: float | None = None
    evidence_metadata: str | None = Field(default=None, max_length=4000)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="evidence")
    competency: Optional["Competency"] = Relationship(back_populates="evidence")
    subskill: Optional["SubSkill"] = Relationship(back_populates="evidence")
