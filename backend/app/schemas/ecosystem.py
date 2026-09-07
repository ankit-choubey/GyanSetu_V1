from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ProviderHealthResponse(BaseModel):
    provider: str
    status: str
    mode: str
    latency_ms: float
    resource_count: int
    details: Optional[str] = None
    checked_at: str


class ProviderSyncResponse(BaseModel):
    provider: str
    mode: str
    added_count: int
    updated_count: int
    skipped_count: int
    rejected_count: int
    total_processed: int
    synced_at: str


class EcosystemResourceResponse(BaseModel):
    id: int
    provider: str
    source_id: Optional[str]
    title: str
    description: Optional[str]
    intervention_type: str
    modality: str
    duration_minutes: Optional[int]
    difficulty: str
    competency_id: Optional[int]
    subskill_id: Optional[int]
    status: str
    availability: str
    integration_mode: str
    mapping_status: str
    mapping_confidence: float
    provenance: str
    source_url: Optional[str]
    last_verified_at: Optional[datetime]
    last_synced_at: Optional[datetime]


class LaunchInterventionResponse(BaseModel):
    provider: str
    provider_resource_id: str
    provider_activity_id: str
    learner_id: int
    integration_mode: str
    launch_url: Optional[str]
    status: str
    launched_at: str


class EcosystemOutcomeRequest(BaseModel):
    status: str = Field(default="COMPLETED")
    completion_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    has_post_assessment_evidence: bool = Field(default=False)
    provider_activity_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    notes: Optional[str] = None


class EcosystemOutcomeResponse(BaseModel):
    outcome_id: int
    status: str
    evidence_id: Optional[int]
    pre_competency_mastery: Optional[float]
    post_competency_mastery: Optional[float]
    competency_updated: bool
    idempotent_replay: bool
    message: str
