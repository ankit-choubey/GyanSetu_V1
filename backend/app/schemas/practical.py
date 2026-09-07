from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PracticalTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    title: str
    competency_id: int
    subskill_id: int | None = None
    scenario_type: str
    difficulty: str
    scenario_context: str
    instructions: str
    input_artifacts: dict[str, Any] = Field(default_factory=dict)
    expected_output_type: str
    rubric_version: str
    prerequisites: list[str] = Field(default_factory=list)
    provenance: str
    source: str
    version: int
    status: str
    created_at: datetime


class PracticalAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: str
    task_id: int
    user_id: int
    status: str
    task_version: int
    rubric_version: str
    started_at: datetime
    submitted_at: datetime | None = None
    score: float | None = None
    evaluator_type: str | None = None
    evaluator_version: str | None = None
    evaluation_result: dict[str, Any] | None = None
    evidence_id: int | None = None
    created_at: datetime


class PracticalSubmitRequest(BaseModel):
    submission: dict[str, Any] = Field(..., description="Learner calculated results and methodology notes")
    idempotency_key: str | None = Field(default=None, description="Optional idempotency key to prevent double evaluation")
    evaluator_type: str | None = Field(default=None, description="Evaluator strategy override: DETERMINISTIC or LLM_ASSISTED")


class PracticalSubmitResponse(BaseModel):
    attempt: PracticalAttemptRead
    evaluation: dict[str, Any] | None = None
    competency_update: dict[str, Any] | None = None
