from datetime import datetime, timezone
import json
from typing import Any, Optional
from sqlmodel import Field, SQLModel


class UserLibraryDocument(SQLModel, table=True):
    """Stores ingested training documents, slides, and lectures for learners."""

    __tablename__ = "user_library_documents"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    source_type: str = Field(max_length=50)  # "pdf", "pptx", "youtube"
    source_url: str | None = Field(default=None, max_length=500)
    filename: str | None = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, max_length=500)
    file_size: int = Field(default=0)
    competency_mapped: str = Field(default="Official Statistics", max_length=150)
    summary: str | None = Field(default=None)
    extracted_concepts_json: str | None = Field(default=None)
    questions_json: str = Field(default="[]")
    questions_count: int = Field(default=15)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_questions(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.questions_json) if self.questions_json else []
        except Exception:
            return []

    def get_concepts(self) -> list[str]:
        try:
            return json.loads(self.extracted_concepts_json) if self.extracted_concepts_json else []
        except Exception:
            return []
