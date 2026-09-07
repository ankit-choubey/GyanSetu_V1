from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .evidence import Evidence
    from .intervention import Intervention
    from .user import User


class InterventionOutcome(SQLModel, table=True):
    __tablename__ = "intervention_outcomes"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    intervention_id: int = Field(foreign_key="interventions.id", index=True)
    recommendation_id: str | None = Field(default=None, index=True, max_length=64)

    status: str = Field(default="COMPLETED", max_length=50, index=True)  # COMPLETED, ABANDONED
    completion_score: float | None = Field(default=None)  # 0.0 to 1.0 if assessment/task scored
    has_post_assessment_evidence: bool = Field(default=False)
    evidence_id: int | None = Field(default=None, foreign_key="evidence.id", index=True)

    pre_competency_mastery: float | None = Field(default=None)
    post_competency_mastery: float | None = Field(default=None)

    # Phase 4 Ecosystem Provider Tracking
    provider: str | None = Field(default=None, max_length=100, index=True)
    provider_resource_id: str | None = Field(default=None, max_length=100, index=True)
    provider_activity_id: str | None = Field(default=None, max_length=128, index=True)
    integration_mode: str | None = Field(default=None, max_length=20)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    idempotency_key: str | None = Field(default=None, unique=True, index=True, max_length=128)
    notes: str | None = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship()
    intervention: Optional["Intervention"] = Relationship()
    evidence: Optional["Evidence"] = Relationship()
