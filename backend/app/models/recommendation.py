from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .intervention import Intervention
    from .user import User


class RecommendationRecord(SQLModel, table=True):
    __tablename__ = "recommendation_records"

    id: int | None = Field(default=None, primary_key=True)
    recommendation_id: str = Field(unique=True, index=True, max_length=64)
    user_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    target_subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    selected_intervention_id: int | None = Field(default=None, foreign_key="interventions.id", index=True)

    action_type: str = Field(default="INTERVENTION", max_length=50, index=True)
    status: str = Field(default="RECOMMENDED", max_length=50, index=True)
    objective: str | None = Field(default=None, max_length=500)
    confidence: float = Field(default=0.5)
    policy_version: str = Field(default="v1.0-deterministic-baseline", max_length=50)

    explanation_json: str | None = Field(default=None)
    rejected_candidates_json: str | None = Field(default=None)
    alternatives_json: str | None = Field(default=None)
    feedback_notes: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship()
    competency: Optional["Competency"] = Relationship()
    target_subskill: Optional["SubSkill"] = Relationship()
    selected_intervention: Optional["Intervention"] = Relationship()
