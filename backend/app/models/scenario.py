from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, JSON, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class ScenarioItem(SQLModel, table=True):
    __tablename__ = "scenario_items"
    __table_args__ = (UniqueConstraint("scenario_id", name="uq_scenario_item_scenario_id"),)

    id: int | None = Field(default=None, primary_key=True)
    scenario_id: str = Field(max_length=255, index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    title: str = Field(max_length=500)
    context: str = Field(max_length=10000)
    context_data: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    task_question: str = Field(max_length=5000)
    response_type: str = Field(max_length=50)
    instructions: str = Field(max_length=5000)
    expected_reasoning: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    rubric: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    difficulty: str = Field(max_length=20)
    cognitive_level: str = Field(max_length=20)
    source_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    generator_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    status: str = Field(default="AVAILABLE", max_length=40, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: "Competency" = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    attempts: list["ScenarioAttempt"] = Relationship(back_populates="scenario")


class ScenarioAttempt(SQLModel, table=True):
    __tablename__ = "scenario_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ATTEMPTED', 'SUBMITTED', 'PENDING_EVALUATION', 'EVALUATED', 'PROVIDER_UNAVAILABLE', 'FAILED')",
            name="ck_scenario_attempt_status",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    scenario_item_id: int = Field(foreign_key="scenario_items.id", index=True)
    scenario_id: str = Field(max_length=255, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    submitted_response: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: str = Field(default="ATTEMPTED", max_length=40, index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def response_text(self) -> str | None:
        if not isinstance(self.submitted_response, dict):
            return None
        value = self.submitted_response.get("text")
        return value if isinstance(value, str) else None

    @response_text.setter
    def response_text(self, value: str) -> None:
        self.submitted_response = {"text": value}

    scenario: ScenarioItem = Relationship(back_populates="attempts")
    user: "User" = Relationship(back_populates="scenario_attempts")
    competency: "Competency" = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    evaluation: Optional["ScenarioEvaluation"] = Relationship(back_populates="attempt")


class ScenarioEvaluation(SQLModel, table=True):
    __tablename__ = "scenario_evaluations"

    id: int | None = Field(default=None, primary_key=True)
    scenario_attempt_id: int = Field(foreign_key="scenario_attempts.id", unique=True, index=True)
    scenario_id: str = Field(max_length=255, index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    score: float = Field(ge=0.0)
    max_score: float = Field(gt=0.0)
    percentage: float = Field(ge=0.0, le=100.0)
    overall_result: str = Field(max_length=40)
    criterion_results: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    feedback: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    demonstrated_competency: bool
    evaluator_confidence: float = Field(ge=0.0, le=1.0)
    evaluator_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    attempt: ScenarioAttempt = Relationship(back_populates="evaluation")