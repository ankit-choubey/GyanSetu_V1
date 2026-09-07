from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .assessment import AssessmentItem
    from .competency import Competency, SubSkill
    from .user import User


class DiagnosticSession(SQLModel, table=True):
    __tablename__ = "diagnostic_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    competency_id: int = Field(foreign_key="competencies.id", index=True)
    status: str = Field(default="IN_PROGRESS", max_length=50, index=True)  # IN_PROGRESS, COMPLETED
    current_difficulty: str = Field(default="easy", max_length=20)
    target_subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    questions_asked: int = Field(default=0)
    max_questions: int = Field(default=5)
    stop_reason: str | None = Field(default=None, max_length=255)
    summary_json: str | None = Field(default=None, max_length=4000)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    user: Optional["User"] = Relationship()
    competency: Optional["Competency"] = Relationship()
    target_subskill: Optional["SubSkill"] = Relationship()
    items: list["DiagnosticItem"] = Relationship(back_populates="session")


class DiagnosticItem(SQLModel, table=True):
    __tablename__ = "diagnostic_items"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="diagnostic_sessions.id", index=True)
    assessment_item_id: int = Field(foreign_key="assessment_items.id", index=True)
    subskill_id: int | None = Field(default=None, foreign_key="subskills.id", index=True)
    selected_difficulty: str = Field(default="easy", max_length=20)
    selection_rationale: str | None = Field(default=None, max_length=1000)
    presented_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answered_at: datetime | None = None
    selected_option: str | None = Field(default=None, max_length=20)
    is_correct: bool | None = None
    score: float | None = None

    session: Optional[DiagnosticSession] = Relationship(back_populates="items")
    assessment_item: Optional["AssessmentItem"] = Relationship()
    subskill: Optional["SubSkill"] = Relationship()
