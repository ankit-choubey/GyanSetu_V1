from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class MonitoringEvent(SQLModel, table=True):
    __tablename__ = "monitoring_events"

    id: int | None = Field(default=None, primary_key=True)
    event_type: str = Field(max_length=100, index=True)
    significance: str = Field(default="NORMAL", max_length=50, index=True)
    status: str = Field(default="PENDING", max_length=50, index=True)
    learner_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    source_entity_type: str | None = Field(default=None, max_length=100)
    source_entity_id: int | None = Field(default=None, index=True)
    event_metadata: str | None = Field(default=None, max_length=4000)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_for: datetime | None = Field(default=None, index=True)
    processed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    learner: Optional["User"] = Relationship()
    competency: Optional["Competency"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()