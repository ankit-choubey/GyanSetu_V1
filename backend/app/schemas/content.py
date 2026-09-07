from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContentAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    filename: str
    media_type: str
    file_size: int
    checksum_sha256: str
    source: str
    provenance: str
    version: int
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ContentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    version_number: int
    checksum_sha256: str
    file_size: int
    change_summary: str | None = None
    created_at: datetime


class ContentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    version_id: int | None = None
    chunk_index: int
    chunk_type: str
    content: str
    token_count: int
    metadata: dict[str, Any]
    created_at: datetime


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    asset_id: int
    status: str
    current_stage: str
    stage_progress: dict[str, Any]
    error_details: str | None = None
    retry_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class CandidateAssessmentResponse(BaseModel):
    prompt: str
    item_type: str
    options: list[str]
    correct_answer: str
    competency_id: int
    subskill_id: int | None = None
    difficulty: str
    provenance: str
    rubric: dict[str, Any]
    metadata: dict[str, Any]
