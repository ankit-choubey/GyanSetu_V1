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


class AssessmentSubmitRequest(BaseModel):
    competency_id: int
    answers: list[AssessmentAnswer]


class AssessmentSubmitResponse(BaseModel):
    status: str
    message: str
    assessment_id: int | None = None
    score: float | None = None
