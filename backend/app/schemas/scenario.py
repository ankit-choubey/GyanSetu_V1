from pydantic import BaseModel


class ScenarioItemCreate(BaseModel):
    competency_id: int
    subskill_id: int | None = None
    title: str
    scenario_text: str
    context_data: dict | None = None
    question: str
    response_type: str = "structured_text"
    instructions: str
    expected_reasoning: dict
    rubric: dict
    difficulty: str
    cognitive_level: str
    source_reference: str | None = None


class ScenarioSubmitRequest(BaseModel):
    scenario_id: int
    response_text: str


class ScenarioSubmitResponse(BaseModel):
    status: str
    message: str
    scenario_id: int
    attempt_id: int | None = None
    score: float | None = None
    max_score: int = 10
    percentage: float | None = None
    overall_result: str | None = None
    feedback: dict | None = None
    demonstrated_competency: bool | None = None
    updated_competency: dict | None = None


class ScenarioItemResponse(BaseModel):
    scenario_id: int
    title: str
    scenario_text: str
    context_data: dict | None = None
    question: str
    response_type: str
    instructions: str
    difficulty: str
    cognitive_level: str
    source_reference: str | None = None