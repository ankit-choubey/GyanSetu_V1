from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class ScenarioItem(SQLModel, table=True):
    __tablename__ = "scenario_items"

    id: int | None = Field(default=None, primary_key=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    title: str = Field(max_length=255)
    scenario_text: str = Field(max_length=6000)
    context_data: str | None = Field(default=None, max_length=6000)
    question: str = Field(max_length=4000)
    response_type: str = Field(max_length=50)
    instructions: str = Field(max_length=2000)
    expected_reasoning: str = Field(max_length=6000)
    rubric: str = Field(max_length=6000)
    difficulty: str = Field(max_length=50)
    cognitive_level: str = Field(max_length=50)
    source_reference: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: Optional["Competency"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    attempts: list["ScenarioAttempt"] = Relationship(back_populates="scenario")


class ScenarioAttempt(SQLModel, table=True):
    __tablename__ = "scenario_attempts"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 10)",
            name="ck_scenario_attempt_score_range",
        ),
        CheckConstraint(
            "percentage IS NULL OR (percentage >= 0 AND percentage <= 100)",
            name="ck_scenario_attempt_percentage_range",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scenario_attempt_confidence_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    scenario_id: int = Field(foreign_key="scenario_items.id", index=True)
    response_text: str = Field(max_length=10000)
    score: int | None = Field(default=None)
    percentage: float | None = Field(default=None)
    overall_result: str | None = Field(default=None, max_length=50)
    evaluation_feedback: str | None = Field(default=None, max_length=10000)
    evaluation_criterion_results: str | None = Field(default=None, max_length=10000)
    confidence: float | None = Field(default=None)
    demonstrated_competency: bool | None = Field(default=None)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_at: datetime | None = Field(default=None)

    user: Optional["User"] = Relationship(back_populates="scenario_attempts")
    scenario: Optional["ScenarioItem"] = Relationship(back_populates="attempts")