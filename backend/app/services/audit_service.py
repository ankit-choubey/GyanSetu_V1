from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


class AuditService:
    """Enterprise-grade, auditable event logging and provenance service."""

    @classmethod
    def log_event(
        cls,
        db: Session,
        action: str,
        entity_type: str,
        actor_id: int | None = None,
        actor_role: str = "SYSTEM",
        entity_id: str | int | None = None,
        correlation_id: str | None = None,
        result: str = "SUCCESS",
        reason: str | None = None,
        source: str | None = "SYSTEM",
        provider: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Records an auditable event record into the immutable ledger."""
        event = AuditEvent(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:12]}",
            result=result,
            reason=reason,
            source=source or "SYSTEM",
            provider=provider,
            before_state_json=json.dumps(before_state) if before_state else None,
            after_state_json=json.dumps(after_state) if after_state else None,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def get_audit_events(
        cls,
        db: Session,
        action: str | None = None,
        entity_type: str | None = None,
        actor_id: int | None = None,
        result: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        """Queries audit event records with filtering and pagination."""
        stmt = select(AuditEvent)

        if action:
            stmt = stmt.where(AuditEvent.action == action)
        if entity_type:
            stmt = stmt.where(AuditEvent.entity_type == entity_type)
        if actor_id is not None:
            stmt = stmt.where(AuditEvent.actor_id == actor_id)
        if result:
            stmt = stmt.where(AuditEvent.result == result)
        if correlation_id:
            stmt = stmt.where(AuditEvent.correlation_id == correlation_id)

        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar_one()

        # Fetch page ordered by most recent
        stmt = stmt.order_by(desc(AuditEvent.timestamp)).offset(offset).limit(limit)
        events = db.execute(stmt).scalars().all()

        return list(events), total

    @classmethod
    def get_event_by_id(cls, db: Session, identifier: str) -> AuditEvent | None:
        """Retrieves a single audit event record by event_id or numeric ID."""
        if identifier.isdigit():
            return db.execute(select(AuditEvent).where(AuditEvent.id == int(identifier))).scalar_one_or_none()
        return db.execute(select(AuditEvent).where(AuditEvent.event_id == identifier)).scalar_one_or_none()

    @classmethod
    def get_audit_summary(cls, db: Session) -> dict[str, Any]:
        """Calculates aggregate summary statistics of recorded audit events."""
        total_events = db.execute(select(func.count(AuditEvent.id))).scalar_one() or 0
        success_count = db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.result == "SUCCESS")).scalar_one() or 0
        failure_count = db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.result != "SUCCESS")).scalar_one() or 0

        # Action breakdown
        action_rows = db.execute(
            select(AuditEvent.action, func.count(AuditEvent.id))
            .group_by(AuditEvent.action)
            .order_by(desc(func.count(AuditEvent.id)))
            .limit(10)
        ).all()

        # Entity type breakdown
        entity_rows = db.execute(
            select(AuditEvent.entity_type, func.count(AuditEvent.id))
            .group_by(AuditEvent.entity_type)
            .order_by(desc(func.count(AuditEvent.id)))
            .limit(10)
        ).all()

        return {
            "total_events": total_events,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_count / total_events, 4) if total_events > 0 else 1.0,
            "top_actions": {row[0]: row[1] for row in action_rows},
            "top_entity_types": {row[0]: row[1] for row in entity_rows},
            "latest_event_timestamp": (
                db.execute(select(func.max(AuditEvent.timestamp))).scalar_one()
            ),
        }
