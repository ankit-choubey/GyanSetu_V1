from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency
    from .evidence import Evidence
    from .user import User


class CompetencyHistory(SQLModel, table=True):
    __tablename__ = "competency_histories"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    previous_mastery: float | None = None
    new_mastery: float | None = None
    previous_confidence: float = Field(default=0.0)
    new_confidence: float = Field(default=0.0)
    previous_status: str = Field(default="UNASSESSED", max_length=50)
    new_status: str = Field(default="UNASSESSED", max_length=50)
    triggering_evidence_id: int | None = Field(default=None, foreign_key="evidence.id", index=True)
    calculation_version: str = Field(default="v2.0-deterministic", max_length=50)
    state_version: int = Field(default=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    user: Optional["User"] = Relationship()
    competency: Optional["Competency"] = Relationship()
    triggering_evidence: Optional["Evidence"] = Relationship()
