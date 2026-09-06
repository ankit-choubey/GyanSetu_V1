from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .assessment_signal import AssessmentSignal
    from .competency import Competency, SubSkill
    from .user import User


class AssessmentItem(SQLModel, table=True):
    __tablename__ = "assessment_items"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    competency_id: int | None = Field(default=None, foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    question_text: str = Field(max_length=2000)
    options_json: str = Field(max_length=4000)
    correct_option: str | None = Field(default=None, max_length=20)
    difficulty: str | None = Field(default=None, max_length=50)
    source_reference: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="assessments")
    competency: Optional["Competency"] = Relationship(back_populates="assessments")
    subskill: Optional["SubSkill"] = Relationship(back_populates="assessments")


class AssessmentAttempt(SQLModel, table=True):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 1)", name="ck_attempt_score_range"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="assessment_attempts")
    competency: "Competency" = Relationship(back_populates="assessment_attempts")
    responses: list["AssessmentResponse"] = Relationship(back_populates="attempt")
    signals: list["AssessmentSignal"] = Relationship(back_populates="attempt")


class AssessmentResponse(SQLModel, table=True):
    __tablename__ = "assessment_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "assessment_item_id", name="uq_attempt_assessment_item_response"),
    )

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="assessment_attempts.id", index=True)
    assessment_item_id: int = Field(foreign_key="assessment_items.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    selected_option: str = Field(max_length=20)
    is_correct: bool
    answered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    attempt: AssessmentAttempt = Relationship(back_populates="responses")
    assessment_item: AssessmentItem = Relationship()
    competency: "Competency" = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
    signals: list["AssessmentSignal"] = Relationship(back_populates="assessment_response")
