from pydantic import BaseModel, Field


class ChatbotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    competency_id: int | None = None


class ChatbotResponse(BaseModel):
    status: str
    answer: str
    sources: list[str] = []
    source_mode: str


class DocumentUploadResponse(BaseModel):
    status: str
    filename: str
    trusted: bool
    coverage: float
    successful_pages: list[int] = []
    failed_pages: list[int] = []
    ocr_used: bool = False
    warning: str | None = None


class CompetencyAnalytics(BaseModel):
    role_id: int | None
    role_name: str | None
    competency_id: int
    competency_name: str
    learner_count: int
    assessed_count: int
    average_mastery: float | None
    average_confidence: float
    average_coverage: float
    total_evidence: int
    status_distribution: dict[str, int]


class AdminAnalyticsResponse(BaseModel):
    competencies: list[CompetencyAnalytics]
    total_competencies: int
