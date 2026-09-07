from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    intervention_type: str
    provider: str
    modality: str
    duration_minutes: int | None = None
    difficulty: str
    competency_id: int | None = None
    subskill_id: int | None = None
    availability: str
    status: str
    provenance: str
    source: str
    source_url: str | None = None
    version: str
    target_misconception_pattern: str | None = None
    created_at: datetime


class InterventionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    intervention_type: str = Field(min_length=2, max_length=50)
    provider: str = Field(default="INTERNAL", max_length=100)
    modality: str = Field(default="ONLINE_SELF_PACED", max_length=50)
    duration_minutes: int = Field(default=60, ge=1)
    difficulty: str = Field(default="intermediate", max_length=20)
    competency_id: int | None = None
    subskill_id: int | None = None
    availability: str = Field(default="ALWAYS_AVAILABLE", max_length=50)
    status: str = Field(default="ACTIVE", max_length=50)
    source: str = Field(default="SYSTEM", max_length=100)
    provenance: str = Field(default="[CURATED]", max_length=100)
    prerequisites_json: str | None = None
    target_misconception_pattern: str | None = None


class NextBestActionRequest(BaseModel):
    competency_id: int | None = None


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: str
    user_id: int
    competency_id: int | None
    target_subskill_id: int | None
    selected_intervention: InterventionRead | None = None
    action_type: str  # "INTERVENTION", "DIAGNOSTIC", "NO_SUITABLE_INTERVENTION"
    status: str
    objective: str | None = None
    confidence: float
    policy_version: str
    explanation: dict[str, Any]
    alternatives: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []
    created_at: datetime


class RecommendationFeedbackRequest(BaseModel):
    action: str = Field(..., description="Action: 'ACCEPTED', 'REJECTED', or 'SKIPPED'")
    notes: str | None = None


class InterventionOutcomeRequest(BaseModel):
    status: str = Field(default="COMPLETED", description="'COMPLETED' or 'ABANDONED'")
    completion_score: float | None = Field(default=None, ge=0.0, le=1.0)
    has_post_assessment_evidence: bool = Field(default=False)
    recommendation_id: str | None = None
    idempotency_key: str | None = None
    notes: str | None = None


class InterventionOutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    intervention_id: int
    recommendation_id: str | None = None
    status: str
    completion_score: float | None = None
    has_post_assessment_evidence: bool
    evidence_id: int | None = None
    pre_competency_mastery: float | None = None
    post_competency_mastery: float | None = None
    notes: str | None = None
    created_at: datetime
