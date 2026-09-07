from typing import Any
from pydantic import BaseModel, Field


class DiagnosticStartRequest(BaseModel):
    competency_id: int
    max_questions: int = Field(default=5, ge=1, le=20)


class DiagnosticQuestionPayload(BaseModel):
    question_id: int
    competency_id: int
    subskill_id: int | None = None
    subskill_name: str | None = None
    difficulty: str
    question_text: str
    options: list[str]
    source_reference: str | None = None
    selection_rationale: str


class DiagnosticStartResponse(BaseModel):
    session_id: int
    competency_id: int
    competency_name: str
    status: str
    baseline_mastery: float | None = None
    baseline_confidence: float = 0.0
    baseline_uncertainty: float = 1.0
    first_question: DiagnosticQuestionPayload | None = None


class DiagnosticAnswerRequest(BaseModel):
    session_id: int
    assessment_item_id: int
    selected_option: str
    response_time_ms: int | None = None
    hints_used: int = 0


class DiagnosticAnswerResponse(BaseModel):
    session_id: int
    is_correct: bool
    score: float
    correct_option: str | None = None
    explanation: str | None = None
    misconception_flagged: bool = False
    updated_mastery: float | None = None
    updated_confidence: float = 0.0
    updated_uncertainty: float = 1.0
    is_complete: bool = False
    stop_reason: str | None = None
    next_question: DiagnosticQuestionPayload | None = None


class DiagnosticSessionStatus(BaseModel):
    session_id: int
    learner_id: int
    competency_id: int
    competency_name: str | None = None
    status: str
    questions_asked: int
    max_questions: int
    current_mastery: float | None = None
    current_confidence: float = 0.0
    current_uncertainty: float = 1.0
    stop_reason: str | None = None
    summary: dict[str, Any] | None = None
