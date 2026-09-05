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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="interventions")
    competency: Optional["Competency"] = Relationship(back_populates="interventions")
    subskill: Optional["SubSkill"] = Relationship(back_populates="interventions")
