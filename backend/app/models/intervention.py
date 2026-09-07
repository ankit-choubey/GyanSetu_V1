from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class Intervention(SQLModel, table=True):
    __tablename__ = "interventions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    title: str = Field(max_length=255)
    description: str | None = None
    intervention_type: str = Field(index=True, max_length=50)
    priority: int = Field(default=1)

    # Canonical Phase 3 fields
    provider: str = Field(default="INTERNAL", max_length=100, index=True)
    modality: str = Field(default="ONLINE_SELF_PACED", max_length=50)
    duration_minutes: int | None = Field(default=60)
    difficulty: str = Field(default="intermediate", max_length=20)
    prerequisites_json: str | None = Field(default=None)
    availability: str = Field(default="ALWAYS_AVAILABLE", max_length=50)
    status: str = Field(default="ACTIVE", max_length=50, index=True)
    source: str = Field(default="SYSTEM", max_length=100)
    source_id: str | None = Field(default=None, max_length=100, index=True)
    source_url: str | None = Field(default=None, max_length=500)
    provenance: str = Field(default="[CURATED]", max_length=100)
    version: str = Field(default="v1.0", max_length=20)
    last_verified_at: datetime | None = Field(default=None)
    target_misconception_pattern: str | None = Field(default=None, max_length=255, index=True)

    # Phase 4 Ecosystem Integration fields
    integration_mode: str = Field(default="REPLAY", max_length=20, index=True)  # LIVE, SANDBOX, REPLAY
    external_metadata_json: str | None = Field(default=None)
    mapping_status: str = Field(default="CURATED", max_length=50, index=True)  # VERIFIED, CURATED, PROVISIONAL, UNDER_REVIEW
    mapping_confidence: float = Field(default=1.0)
    last_synced_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="interventions")
    competency: Optional["Competency"] = Relationship(back_populates="interventions")
    subskill: Optional["SubSkill"] = Relationship(back_populates="interventions")

