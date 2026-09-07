from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import Field, SQLModel


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:16]}",
        max_length=64,
        index=True,
        unique=True,
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
    actor_id: int | None = Field(default=None, index=True)
    actor_role: str = Field(default="SYSTEM", max_length=100, index=True)
    action: str = Field(max_length=100, index=True)
    entity_type: str = Field(max_length=100, index=True)
    entity_id: str | None = Field(default=None, max_length=100, index=True)
    correlation_id: str | None = Field(default=None, max_length=100, index=True)
    result: str = Field(default="SUCCESS", max_length=50, index=True)
    reason: str | None = Field(default=None, max_length=500)
    source: str | None = Field(default="SYSTEM", max_length=100)
    provider: str | None = Field(default=None, max_length=100)
    before_state_json: str | None = Field(default=None)
    after_state_json: str | None = Field(default=None)
    metadata_json: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def get_metadata(self) -> dict[str, Any]:
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except Exception:
            return {}

    def get_before_state(self) -> dict[str, Any] | None:
        if not self.before_state_json:
            return None
        try:
            return json.loads(self.before_state_json)
        except Exception:
            return None

    def get_after_state(self) -> dict[str, Any] | None:
        if not self.after_state_json:
            return None
        try:
            return json.loads(self.after_state_json)
        except Exception:
            return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "correlation_id": self.correlation_id,
            "result": self.result,
            "reason": self.reason,
            "source": self.source,
            "provider": self.provider,
            "before_state": json.loads(self.before_state_json) if self.before_state_json else None,
            "after_state": json.loads(self.after_state_json) if self.after_state_json else None,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
