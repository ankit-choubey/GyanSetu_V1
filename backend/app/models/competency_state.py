from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency
    from .user import User


class CompetencyState(SQLModel, table=True):
    __tablename__ = "competency_states"
    __table_args__ = (UniqueConstraint("user_id", "competency_id", name="uq_competency_state_user_competency"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    mastery: float | None = None
    confidence: float = Field(default=0.0)
    coverage: float = Field(default=0.0)
    evidence_count: int = Field(default=0)
    evidence_diversity: int = Field(default=0)
    status: str = Field(default="UNASSESSED", max_length=50)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="competency_states")
    competency: Optional["Competency"] = Relationship(back_populates="competency_states")
