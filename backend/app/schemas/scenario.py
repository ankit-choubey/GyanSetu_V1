from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    scenario_type: str = Field(default="OPERATIONAL_PROCEDURE")
    competency_id: int
    subskill_id: int | None = None
    role_id: int | None = None
    difficulty: str = Field(default="medium")
    expected_outcomes: list[str] = Field(default_factory=list)
    evaluation_rubric: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScenarioGenerateRequest(BaseModel):
    competency_id: int
    subskill_id: int | None = None
    role_id: int | None = None
    difficulty: str = Field(default="medium")
    scenario_type: str = Field(default="OPERATIONAL_PROCEDURE")
    learning_objective: str = Field(default="Operational scenario practice")


class ScenarioResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_id: str
    title: str
    description: str
    scenario_type: str
    competency_id: int
    subskill_id: int | None
    role_id: int | None
    difficulty: str
    version: int
    status: str
    expected_outcomes: list[str]
    evaluation_rubric: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ScenarioAttemptResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: str
    scenario_id: int
    user_id: int
    status: str
    scenario_version: int
    started_at: datetime
    submitted_at: datetime | None = None
    score: float | None = None
    evaluation_id: int | None = None
    created_at: datetime


class ScenarioSubmissionRequest(BaseModel):
    response_payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class ScenarioEvaluationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: int
    score: float
    max_score: float
    normalized_score: float
    passed: bool
    competency_evidence: dict[str, Any]
    subskill_evidence: dict[str, Any]
    rubric_results: dict[str, Any]
    evaluator_type: str
    evaluator_version: str
    confidence: float
    review_required: bool
    provenance: str
    feedback: str | None = None
    created_at: datetime


class ScenarioSubmissionResultResponseSchema(BaseModel):
    attempt: ScenarioAttemptResponseSchema
    evaluation: ScenarioEvaluationResponseSchema | None = None
    competency_update: dict[str, Any] | None = None
