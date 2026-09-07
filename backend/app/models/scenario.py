import json
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, Role, SubSkill
    from .user import User


class ScenarioStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ScenarioAttemptStatus(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"


class Scenario(SQLModel, table=True):
    """Canonical model for structured realistic application scenarios (5.2b)."""

    __tablename__ = "scenarios"

    id: int | None = Field(default=None, primary_key=True)
    scenario_id: str = Field(unique=True, index=True, max_length=100)
    title: str = Field(max_length=255)
    description: str = Field(default="")
    scenario_type: str = Field(default="OPERATIONAL_PROCEDURE", max_length=50)
    role_id: int | None = Field(default=None, foreign_key="roles.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    difficulty: str = Field(default="medium", max_length=20)
    source: str = Field(default="MOSPI_OPERATIONAL", max_length=100)
    provenance: str = Field(default="[SANDBOX DATA]", max_length=100)
    version: int = Field(default=1)
    status: str = Field(default="ACTIVE", max_length=20)
    expected_outcomes_json: str = Field(default="[]")
    evaluation_rubric_json: str = Field(default="{}")
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: Optional["Competency"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    role: Optional["Role"] = Relationship()
    attempts: list["ScenarioAttempt"] = Relationship(back_populates="scenario")

    def get_expected_outcomes(self) -> list[str]:
        try:
            return json.loads(self.expected_outcomes_json) if self.expected_outcomes_json else []
        except Exception:
            return []

    def get_rubric(self) -> dict[str, Any]:
        try:
            return json.loads(self.evaluation_rubric_json) if self.evaluation_rubric_json else {}
        except Exception:
            return {}

    def get_metadata(self) -> dict[str, Any]:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}


class ScenarioAttempt(SQLModel, table=True):
    """Lifecycle record for a learner attempting a scenario."""

    __tablename__ = "scenario_attempts"

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: str = Field(unique=True, index=True, max_length=128)
    scenario_id: int = Field(foreign_key="scenarios.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="STARTED", max_length=30)
    scenario_version: int = Field(default=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: datetime | None = Field(default=None)
    score: float | None = Field(default=None)
    evaluation_id: int | None = Field(default=None, foreign_key="scenario_evaluations.id", index=True)
    idempotency_key: str | None = Field(default=None, unique=True, index=True, max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    scenario: Optional["Scenario"] = Relationship(back_populates="attempts")
    user: Optional["User"] = Relationship()
    responses: list["ScenarioResponse"] = Relationship(back_populates="attempt")
    evaluation: Optional["ScenarioEvaluation"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ScenarioAttempt.evaluation_id]"}
    )


class ScenarioResponse(SQLModel, table=True):
    """Learner submitted response/decisions for a scenario attempt."""

    __tablename__ = "scenario_responses"

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="scenario_attempts.id", index=True)
    response_payload_json: str = Field(default="{}")
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    attempt: Optional["ScenarioAttempt"] = Relationship(back_populates="responses")

    def get_response_payload(self) -> dict[str, Any]:
        try:
            return json.loads(self.response_payload_json) if self.response_payload_json else {}
        except Exception:
            return {}


class ScenarioEvaluation(SQLModel, table=True):
    """Evaluator outcome and multi-dimensional rubric results for a scenario attempt."""

    __tablename__ = "scenario_evaluations"

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="scenario_attempts.id", unique=True, index=True)
    score: float = Field(default=0.0)
    max_score: float = Field(default=1.0)
    normalized_score: float = Field(default=0.0)
    passed: bool = Field(default=False)
    competency_evidence_json: str = Field(default="{}")
    subskill_evidence_json: str = Field(default="{}")
    rubric_results_json: str = Field(default="{}")
    evaluator_type: str = Field(default="DETERMINISTIC", max_length=50)
    evaluator_version: str = Field(default="v1.0", max_length=50)
    confidence: float = Field(default=1.0)
    review_required: bool = Field(default=False)
    provenance: str = Field(default="[SANDBOX DATA]", max_length=100)
    feedback: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_competency_evidence(self) -> dict[str, Any]:
        try:
            return json.loads(self.competency_evidence_json) if self.competency_evidence_json else {}
        except Exception:
            return {}

    def get_subskill_evidence(self) -> dict[str, Any]:
        try:
            return json.loads(self.subskill_evidence_json) if self.subskill_evidence_json else {}
        except Exception:
            return {}

    def get_rubric_results(self) -> dict[str, Any]:
        try:
            return json.loads(self.rubric_results_json) if self.rubric_results_json else {}
        except Exception:
            return {}
