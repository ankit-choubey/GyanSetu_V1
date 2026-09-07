import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlmodel import Field, Relationship, SQLModel


class ContentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    STRUCTURED = "STRUCTURED"
    MAPPED = "MAPPED"
    READY = "READY"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    RETIRED = "RETIRED"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ContentAsset(SQLModel, table=True):
    """Canonical model for ingested documents and learning content assets (5.3b)."""

    __tablename__ = "content_assets"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(unique=True, index=True, max_length=100)
    filename: str = Field(max_length=255)
    media_type: str = Field(max_length=100)
    file_size: int = Field(default=0)
    checksum_sha256: str = Field(index=True, max_length=64)
    storage_path: str = Field(default="", max_length=500)
    source: str = Field(default="MOSPI_TRAINING", max_length=100)
    provenance: str = Field(default="[SANDBOX DATA]", max_length=100)
    version: int = Field(default=1)
    status: str = Field(default="UPLOADED", max_length=30)
    error_message: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    versions: list["ContentVersion"] = Relationship(back_populates="asset")
    chunks: list["ContentChunk"] = Relationship(back_populates="asset")
    jobs: list["ProcessingJob"] = Relationship(back_populates="asset")


class ContentVersion(SQLModel, table=True):
    """Immutable version snapshot of an ingested content asset."""

    __tablename__ = "content_versions"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="content_assets.id", index=True)
    version_number: int = Field(default=1)
    checksum_sha256: str = Field(max_length=64)
    file_size: int = Field(default=0)
    change_summary: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    asset: Optional["ContentAsset"] = Relationship(back_populates="versions")
    chunks: list["ContentChunk"] = Relationship(back_populates="version")


class ContentChunk(SQLModel, table=True):
    """Extracted and chunked content block mapped to taxonomy concepts."""

    __tablename__ = "content_chunks"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="content_assets.id", index=True)
    version_id: int | None = Field(default=None, foreign_key="content_versions.id", index=True)
    chunk_index: int = Field(default=0)
    chunk_type: str = Field(default="TEXT", max_length=50)  # TEXT, TABLE, HEADING, PROCEDURE
    content: str = Field(default="")
    token_count: int = Field(default=0)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    asset: Optional["ContentAsset"] = Relationship(back_populates="chunks")
    version: Optional["ContentVersion"] = Relationship(back_populates="chunks")

    def get_metadata(self) -> dict[str, Any]:
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}


class ProcessingJob(SQLModel, table=True):
    """Execution state machine and progress tracking for content ingestion."""

    __tablename__ = "processing_jobs"

    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True, max_length=128)
    asset_id: int = Field(foreign_key="content_assets.id", index=True)
    status: str = Field(default="QUEUED", max_length=30)
    current_stage: str = Field(default="UPLOADED", max_length=50)
    stage_progress_json: str = Field(default="{}")
    error_details: str | None = Field(default=None)
    retry_count: int = Field(default=0)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    asset: Optional["ContentAsset"] = Relationship(back_populates="jobs")

    def get_stage_progress(self) -> dict[str, Any]:
        try:
            return json.loads(self.stage_progress_json) if self.stage_progress_json else {}
        except Exception:
            return {}
