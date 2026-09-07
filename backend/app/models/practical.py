import json
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .evidence import Evidence
    from .user import User


class PracticalScenarioType(str, Enum):
    DATA_ANALYSIS = "DATA_ANALYSIS"
    STATISTICAL_PROCEDURE = "STATISTICAL_PROCEDURE"
    DATA_VALIDATION = "DATA_VALIDATION"
    DECISION = "DECISION"
    INTERPRETATION = "INTERPRETATION"
    LAB_EXECUTION = "LAB_EXECUTION"


class PracticalDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AttemptStatus(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class EvaluatorType(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    LLM_ASSISTED = "LLM_ASSISTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class PracticalTask(SQLModel, table=True):
    """Canonical model for structured practical statistical tasks and simulation workbenches."""

    __tablename__ = "practical_tasks"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(unique=True, index=True, max_length=100)
    title: str = Field(max_length=255)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    scenario_type: str = Field(default="STATISTICAL_PROCEDURE", max_length=50)
    difficulty: str = Field(default="medium", max_length=20)
    scenario_context: str = Field(default="")
    instructions: str = Field(default="")
    input_artifacts_json: str = Field(default="{}")
    expected_output_type: str = Field(default="NUMERICAL_JSON", max_length=50)
    rubric_json: str = Field(default="{}")
    rubric_version: str = Field(default="v1.0-rubric", max_length=50)
    prerequisites_json: str | None = Field(default=None)
    provenance: str = Field(default="[CURATED:SIMULATION]", max_length=100)
    source: str = Field(default="MOSPI_SIMULATION", max_length=100)
    version: int = Field(default=1)
    status: str = Field(default="ACTIVE", max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: Optional["Competency"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    attempts: list["PracticalAttempt"] = Relationship(back_populates="task")

    def get_input_artifacts(self) -> dict[str, Any]:
        try:
            return json.loads(self.input_artifacts_json) if self.input_artifacts_json else {}
        except Exception:
            return {}

    def get_rubric(self) -> dict[str, Any]:
        try:
            return json.loads(self.rubric_json) if self.rubric_json else {}
        except Exception:
            return {}

    def get_prerequisites(self) -> list[str]:
        try:
            return json.loads(self.prerequisites_json) if self.prerequisites_json else []
        except Exception:
            return []


class PracticalAttempt(SQLModel, table=True):
    """Lifecycle and evaluation record of a learner attempting a practical task."""

    __tablename__ = "practical_attempts"

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: str = Field(unique=True, index=True, max_length=128)
    task_id: int = Field(foreign_key="practical_tasks.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="CREATED", max_length=30)
    task_version: int = Field(default=1)
    rubric_version: str = Field(default="v1.0-rubric", max_length=50)
    submission_payload_json: str | None = Field(default=None)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: datetime | None = Field(default=None)
    evaluator_type: str | None = Field(default=None, max_length=50)
    evaluator_version: str | None = Field(default=None, max_length=50)
    score: float | None = Field(default=None)
    evaluation_result_json: str | None = Field(default=None)
    evidence_id: int | None = Field(default=None, foreign_key="evidence.id", index=True)
    idempotency_key: str | None = Field(default=None, unique=True, index=True, max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    task: Optional["PracticalTask"] = Relationship(back_populates="attempts")
    user: Optional["User"] = Relationship()
    evidence: Optional["Evidence"] = Relationship()

    def get_submission_payload(self) -> dict[str, Any]:
        try:
            return json.loads(self.submission_payload_json) if self.submission_payload_json else {}
        except Exception:
            return {}

    def get_evaluation_result(self) -> dict[str, Any]:
        try:
            return json.loads(self.evaluation_result_json) if self.evaluation_result_json else {}
        except Exception:
            return {}
