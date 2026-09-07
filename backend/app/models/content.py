from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, JSON, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .competency import Competency, SubSkill
    from .user import User


class ContentItem(SQLModel, table=True):
    __tablename__ = "content_items"
    __table_args__ = (UniqueConstraint("content_id", name="uq_content_item_content_id"),)

    id: int | None = Field(default=None, primary_key=True)
    content_id: str = Field(max_length=255, index=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    original_filename: str = Field(max_length=500)
    content_type: str | None = Field(default=None, max_length=255)
    file_size: int = Field(ge=0)
    checksum: str = Field(max_length=64, index=True)
    storage_reference: str = Field(max_length=1000)
    status: str = Field(default="UPLOADED", max_length=40, index=True)
    ml_status: str | None = Field(default=None, max_length=20)
    source_reference: str | None = Field(default=None, max_length=1000)
    provider_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    warnings: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    errors: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    owner: "User" = Relationship()
    concepts: list["ContentConcept"] = Relationship(back_populates="content")
    mappings: list["ContentCompetencyMapping"] = Relationship(back_populates="content")


class ContentConcept(SQLModel, table=True):
    __tablename__ = "content_concepts"

    id: int | None = Field(default=None, primary_key=True)
    content_item_id: int = Field(foreign_key="content_items.id", index=True)
    concept: str = Field(max_length=500)
    description: str = Field(max_length=4000)
    subskills: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    content: ContentItem = Relationship(back_populates="concepts")


class ContentCompetencyMapping(SQLModel, table=True):
    __tablename__ = "content_competency_mappings"
    __table_args__ = (CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_content_mapping_confidence"),)

    id: int | None = Field(default=None, primary_key=True)
    content_item_id: int = Field(foreign_key="content_items.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    concept: str = Field(max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=4000)
    source_reference: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    content: ContentItem = Relationship(back_populates="mappings")
    competency: Optional["Competency"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()