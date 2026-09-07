from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MonitoringEventType(str, Enum):
    ASSESSMENT_COMPLETED = "assessment_completed"
    REPEATED_FAILURE = "repeated_failure"
    EVIDENCE_STALE = "evidence_stale"
    DELAYED_CHECK_DUE = "delayed_check_due"
    COMPETENCY_REQUIREMENT_ADDED = "competency_requirement_added"
    INTERVENTION_COMPLETED = "intervention_completed"


class MonitoringEventRequest(BaseModel):
    event_type: MonitoringEventType
    learner_id: int = Field(gt=0)
    competency_id: int | None = Field(default=None, gt=0)
    subskill_id: int | None = Field(default=None, gt=0)
    source_entity_type: str | None = Field(default=None, max_length=100)
    source_entity_id: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] | None = None
    occurred_at: datetime | None = None
    scheduled_at: datetime | None = None


class MonitoringEventResponse(BaseModel):
    event_id: int
    event_type: MonitoringEventType
    significance: str
    status: str
    action: str
    result: dict[str, Any]