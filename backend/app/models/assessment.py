from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
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
