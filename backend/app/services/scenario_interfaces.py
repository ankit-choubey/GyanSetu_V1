from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

ResponseType = Literal["structured_text", "multiple_choice", "numeric", "structured_input"]
Difficulty = Literal["easy", "medium", "hard"]
CognitiveLevel = Literal["application", "analysis", "evaluation"]
CriterionResultValue = Literal["met", "partially_met", "not_met"]
OverallResult = Literal["correct", "partially_correct", "incorrect"]


class ScenarioTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1)
    response_type: ResponseType
    instructions: str = Field(min_length=1)


class ScenarioContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    context: str = Field(min_length=1)
    context_data: dict[str, Any] = Field(default_factory=dict)
    task: ScenarioTask


class ReasoningContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key_points: list[str] = Field(default_factory=list)
    reference_answer: str = ""


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    max_score: float = Field(ge=0)


class Rubric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criteria: list[RubricCriterion] = Field(min_length=1)
    max_score: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_criteria_total(self) -> "Rubric":
        if sum(item.max_score for item in self.criteria) > self.max_score + 1e-6:
            raise ValueError("Rubric criterion maximum cannot exceed rubric max_score")
        return self


class ScenarioProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")
    content_id: str | None = None
    chunk_ids: list[str] = Field(default_factory=list)


class ProviderMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None
    generator_version: str | None = None
    evaluator_version: str | None = None
    generated_at: datetime | None = None
    evaluated_at: datetime | None = None
    environment: str | None = None


class ScenarioGeneratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(min_length=1, max_length=255)
    competency_id: int = Field(gt=0)
    competency_code: str | None = None
    competency_name: str | None = None
    subskill_id: int | None = Field(default=None, gt=0)
    subskill_code: str | None = None
    subskill_name: str | None = None
    scenario: ScenarioContent
    expected_reasoning: ReasoningContract
    rubric: Rubric
    difficulty: Difficulty
    cognitive_level: CognitiveLevel
    source: ScenarioProvenance = Field(default_factory=ScenarioProvenance)
    metadata: ProviderMetadata = Field(default_factory=ProviderMetadata)


class ScenarioGeneratorRequest(BaseModel):
    competency_id: int = Field(gt=0)
    subskill_id: int | None = Field(default=None, gt=0)


class ScenarioEvaluatorRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    competency_id: int = Field(gt=0)
    subskill_id: int | None = Field(default=None, gt=0)
    scenario: ScenarioContent
    learner_response: dict[str, Any]
    expected_reasoning: ReasoningContract
    rubric: Rubric
    configuration: dict[str, Any] = Field(default_factory=dict)


class CriterionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str = Field(min_length=1)
    result: CriterionResultValue
    score: float = Field(ge=0)
    feedback: str = ""


class EvaluationDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    percentage: float = Field(ge=0, le=100)
    criterion_results: list[CriterionResult] = Field(default_factory=list)
    overall_result: OverallResult

    @model_validator(mode="after")
    def validate_score(self) -> "EvaluationDetails":
        if self.score > self.max_score:
            raise ValueError("Evaluation score cannot exceed max_score")
        normalized = round(self.score / self.max_score * 100, 4)
        if abs(normalized - self.percentage) > 0.01:
            raise ValueError("Evaluation percentage is inconsistent with score and max_score")
        return self


class EvaluationFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    recommended_next_step: str = ""


class EvaluationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demonstrated_competency: bool
    evidence_type: Literal["scenario_assessment"]
    confidence: float = Field(ge=0, le=1)


class ScenarioEvaluationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(min_length=1)
    competency_id: int = Field(gt=0)
    subskill_id: int | None = Field(default=None, gt=0)
    evaluation: EvaluationDetails
    feedback: EvaluationFeedback
    evidence: EvaluationEvidence
    metadata: ProviderMetadata = Field(default_factory=ProviderMetadata)


class ScenarioProviderUnavailable(RuntimeError):
    pass


class ScenarioGenerator(Protocol):
    def generate(self, request: ScenarioGeneratorRequest) -> ScenarioGeneratorOutput:
        ...


class ScenarioEvaluator(Protocol):
    def evaluate(self, request: ScenarioEvaluatorRequest) -> ScenarioEvaluationOutput:
        ...


class UnavailableScenarioGenerator:
    def generate(self, request: ScenarioGeneratorRequest) -> ScenarioGeneratorOutput:
        raise ScenarioProviderUnavailable("Scenario generator provider is unavailable")


class UnavailableScenarioEvaluator:
    def evaluate(self, request: ScenarioEvaluatorRequest) -> ScenarioEvaluationOutput:
        raise ScenarioProviderUnavailable("Scenario evaluator provider is unavailable")