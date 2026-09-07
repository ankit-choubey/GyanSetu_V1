from datetime import datetime
from pydantic import BaseModel


class MisconceptionRead(BaseModel):
    id: int
    learner_id: int
    competency_id: int
    competency_name: str | None = None
    subskill_id: int | None = None
    subskill_name: str | None = None
    pattern_key: str | None = None
    misconception_type: str
    description: str
    occurrences: int
    first_observed: datetime
    last_observed: datetime
    intervention_applied: bool
    resolved: bool
    resolution_evidence_id: int | None = None


class MisconceptionsResponse(BaseModel):
    learner_id: int
    total_misconceptions: int
    active_count: int
    resolved_count: int
    misconceptions: list[MisconceptionRead]
