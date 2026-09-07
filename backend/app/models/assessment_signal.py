from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .assessment import AssessmentAttempt, AssessmentResponse


class AssessmentSignal(SQLModel, table=True):
    __tablename__ = "assessment_signals"
    __table_args__ = (
        CheckConstraint("response_time IS NULL OR response_time >= 0", name="ck_signal_response_time_nonnegative"),
        CheckConstraint("retries IS NULL OR retries >= 0", name="ck_signal_retries_nonnegative"),
        CheckConstraint("hints_requested IS NULL OR hints_requested >= 0", name="ck_signal_hints_nonnegative"),
        CheckConstraint("skips IS NULL OR skips >= 0", name="ck_signal_skips_nonnegative"),
        CheckConstraint("repeated_errors IS NULL OR repeated_errors >= 0", name="ck_signal_errors_nonnegative"),
        CheckConstraint("session_duration IS NULL OR session_duration >= 0", name="ck_signal_duration_nonnegative"),
    )

    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(foreign_key="assessment_attempts.id", index=True)
    assessment_response_id: int | None = Field(default=None, foreign_key="assessment_responses.id", index=True)
    is_session_aggregate: bool = Field(default=False, index=True)
    response_time: float | None = Field(default=None, ge=0.0)
    retries: int | None = Field(default=None, ge=0)
    hints_requested: int | None = Field(default=None, ge=0)
    skips: int | None = Field(default=None, ge=0)
    repeated_errors: int | None = Field(default=None, ge=0)
    session_duration: float | None = Field(default=None, ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    attempt: "AssessmentAttempt" = Relationship(back_populates="signals")
    assessment_response: Optional["AssessmentResponse"] = Relationship(back_populates="signals")