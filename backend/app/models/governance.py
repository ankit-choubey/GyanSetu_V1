from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency


class ReviewStatus(str, Enum):
    VERIFIED = "VERIFIED"
    CURATED = "CURATED"
    PROVISIONAL = "PROVISIONAL"
    UNDER_REVIEW = "UNDER_REVIEW"


class ModelStatus(str, Enum):
    PRODUCTION_BASELINE = "PRODUCTION BASELINE"
    RESEARCH = "RESEARCH"
    EXPERIMENTAL = "EXPERIMENTAL"
    ENGINEERING_HEURISTIC = "ENGINEERING HEURISTIC"


class CompetencyGovernance(SQLModel, table=True):
    __tablename__ = "competency_governance"

    id: int | None = Field(default=None, primary_key=True)
    competency_id: int = Field(foreign_key="competencies.id", unique=True, index=True)
    version: str = Field(default="v1.0", max_length=20)
    review_status: str = Field(default=ReviewStatus.CURATED.value, max_length=50, index=True)
    mapping_provenance: str = Field(default="[CURATED:MOSPI_TAXONOMY]", max_length=100)
    expert_review_notes: str | None = Field(default=None, max_length=1000)
    reviewed_by: str | None = Field(default=None, max_length=255)
    reviewed_at: datetime | None = None
    is_deprecated: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    competency: Optional["Competency"] = Relationship()


class ModelRegistryRecord(SQLModel, table=True):
    __tablename__ = "model_registry"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    version: str = Field(default="v1.0", max_length=50)
    model_type: str = Field(max_length=100, index=True)
    scientific_status: str = Field(default=ModelStatus.PRODUCTION_BASELINE.value, max_length=50, index=True)
    training_data_description: str = Field(max_length=500)
    evaluation_reference: str = Field(max_length=500)
    limitations: str = Field(max_length=1000)
    production_status: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkforceAuditLog(SQLModel, table=True):
    __tablename__ = "workforce_audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    actor_id: int | None = Field(default=None, index=True)
    actor_email: str | None = Field(default=None, max_length=255)
    actor_role: str = Field(default="ADMINISTRATOR", max_length=100)
    endpoint: str = Field(max_length=255, index=True)
    requested_scope: str = Field(default="ALL", max_length=255)
    suppressed_groups_count: int = Field(default=0)
    authorization_decision: str = Field(default="AUTHORIZED", max_length=50)
    insights_generated_count: int = Field(default=0)
    fairness_audit_status: str | None = Field(default=None, max_length=50)
    data_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
