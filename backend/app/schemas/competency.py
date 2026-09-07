from datetime import datetime
from pydantic import BaseModel


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None


class CompetencyRead(BaseModel):
    id: int
    role_id: int | None = None
    name: str
    description: str | None = None


class CompetencyStateDetailRead(BaseModel):
    competency_id: int
    competency_name: str
    mastery: float | None = None
    confidence: float = 0.0
    uncertainty: float = 1.0
    coverage: float = 0.0
    evidence_count: int = 0
    evidence_diversity: int = 0
    status: str = "UNASSESSED"
    state_version: int = 1
    last_assessed_at: datetime | None = None
    updated_at: datetime | None = None


class CompetencyHistoryRead(BaseModel):
    id: int
    competency_id: int
    previous_mastery: float | None = None
    new_mastery: float | None = None
    previous_confidence: float = 0.0
    new_confidence: float = 0.0
    previous_status: str = "UNASSESSED"
    new_status: str = "UNASSESSED"
    triggering_evidence_id: int | None = None
    calculation_version: str = "v2.0-deterministic"
    state_version: int = 1
    timestamp: datetime
