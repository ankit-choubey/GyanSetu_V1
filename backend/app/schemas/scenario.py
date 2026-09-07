from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.scenario_interfaces import ScenarioContent, ScenarioGeneratorRequest


class ScenarioGenerateRequest(ScenarioGeneratorRequest):
    pass


class ScenarioDeliveryResponse(BaseModel):
    status: str
    task_id: int | None = None
    scenario_id: str | None = None
    competency_id: int | None = None
    subskill_id: int | None = None
    scenario: ScenarioContent | None = None
    difficulty: str | None = None
    cognitive_level: str | None = None
    source: dict[str, Any] | None = None


class ScenarioAttemptCreateResponse(BaseModel):
    status: str
    attempt_id: int | None = None
    scenario_id: str


class ScenarioSubmitRequest(BaseModel):
    response: dict[str, Any]


class ScenarioDirectSubmitRequest(BaseModel):
    scenario_id: int = Field(gt=0)
    response_text: str = Field(min_length=1)


class ScenarioSubmitResponse(BaseModel):
    status: str
    attempt_id: int
    scenario_id: str
    evaluation_id: int | None = None
    evaluation: dict[str, Any] | None = None


class ScenarioEvaluationResponse(BaseModel):
    status: str
    attempt_id: int
    scenario_id: str
    evaluation: dict[str, Any] | None = None