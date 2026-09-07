from datetime import datetime
from pydantic import BaseModel


class EvidenceRead(BaseModel):
    id: int
    user_id: int
    competency_id: int
    competency_name: str | None = None
    subskill_id: int | None = None
    subskill_name: str | None = None
    evidence_type: str
    title: str
    description: str | None = None
    score: float | None = None
    weight: float | None = None
    source: str | None = "INTERNAL"
    provenance: str = "[CURATED]"
    reliability_status: str = "VERIFIED"
    assessment_item_id: int | None = None
    version: int = 1
    evidence_metadata: str | None = None
    observed_at: datetime
    created_at: datetime


class EvidenceLedgerResponse(BaseModel):
    learner_id: int
    total_records: int
    evidence: list[EvidenceRead]
