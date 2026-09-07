from pydantic import BaseModel


class CompetencySummary(BaseModel):
    competency_id: int
    competency_name: str
    mastery: float | None = None
    confidence: float = 0.0
    coverage: float = 0.0
    evidence_count: int = 0
    status: str = "UNASSESSED"


class DashboardResponse(BaseModel):
    user_id: int
    full_name: str
    role_name: str | None = None
    designation: str | None = "Statistical Officer"
    department: str | None = "National Accounts Division (NAD)"
    competencies: list[CompetencySummary] = []
    total_competencies: int = 0
    evaluations_completed: int = 0
    total_evidence_records: int = 0
