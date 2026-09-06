from pydantic import BaseModel


class AssessmentItemCreate(BaseModel):
    competency_id: int
    subskill_id: int | None = None
    question_text: str
    options: list[str]
    correct_option: str
    difficulty: str | None = None
    source_reference: str | None = None


class AssessmentAnswer(BaseModel):
    question_id: int
    selected: str


class AnswerFeedback(BaseModel):
    question_id: int
    selected: str
    is_correct: bool
    feedback: str
    identified_gap: str | None = None


class AssessmentSubmitRequest(BaseModel):
    competency_id: int
    answers: list[AssessmentAnswer]


class AssessmentSubmitResponse(BaseModel):
    status: str
    message: str
    assessment_id: int | None = None
    score: float | None = None
    feedback: list[AnswerFeedback] = []
    competency_status: str | None = None
    mastery: float | None = None
    confidence: float | None = None
    next_best_action: dict | None = None


class AdaptiveQuestionRequest(BaseModel):
    competency_id: int
    session_history: list[dict] = []


class AdaptiveQuestionResponse(BaseModel):
    status: str
    sufficient_evidence: bool
    stop_reason: str
    question_id: int | None = None
    competency_id: int
    subskill_id: int | None = None
    question_text: str | None = None
    options: list[str] = []
    difficulty: str | None = None
