from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.audit_service import AuditService


class PolicyService:
    """Centralized, versioned operational policy and configuration governance service."""

    _POLICIES: dict[str, dict[str, Any]] = {
        "STALENESS_THRESHOLD_DAYS": {
            "value": 180,
            "type": "int",
            "description": "Maximum days before an external learning resource or evidence record is marked STALE.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "PRIVACY_SUPPRESSION_THRESHOLD": {
            "value": 5,
            "type": "int",
            "description": "Minimum cohort size (N) required to display aggregate workforce metrics without privacy suppression.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "DIAGNOSTIC_MAX_QUESTIONS": {
            "value": 10,
            "type": "int",
            "description": "Maximum question depth permitted during an adaptive diagnostic session before forced convergence.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "CONFIDENCE_TARGET_THRESHOLD": {
            "value": 0.75,
            "type": "float",
            "description": "Target competency state confidence threshold indicating robust multi-modal evidence convergence.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "FOUR_FIFTHS_THRESHOLD": {
            "value": 0.80,
            "type": "float",
            "description": "Adverse impact ratio threshold (80%) for institutional role selection parity screening.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "LAUNCH_TOKEN_EXPIRY_SECONDS": {
            "value": 1800,
            "type": "int",
            "description": "Validity window (30 minutes) for external provider SSO launch tokens.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "NON_MASTERY_CAP": {
            "value": 0.50,
            "type": "float",
            "description": "Upper mastery bound imposed when an intervention or practical evaluation is incomplete or failed.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "MIN_ITEM_RESPONSES_FOR_ANALYSIS": {
            "value": 5,
            "type": "int",
            "description": "Minimum response count required for psychometric evaluation and quality review.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
        "RETENTION_WINDOW_DAYS": {
            "value": 90,
            "type": "int",
            "description": "Competency retention window before refresher recommendations are triggered.",
            "version": "1.0",
            "last_modified_by": "SYSTEM",
            "last_modified_at": "2026-09-08T00:00:00Z",
        },
    }

    @classmethod
    def get_all_policies(cls) -> dict[str, dict[str, Any]]:
        """Returns all operational policies and governance metadata."""
        return cls._POLICIES.copy()

    @classmethod
    def get_policy(cls, key: str) -> dict[str, Any] | None:
        """Retrieves a single policy configuration by key."""
        return cls._POLICIES.get(key)

    @classmethod
    def update_policy(
        cls,
        db: Session,
        key: str,
        new_value: Any,
        actor_id: int,
        actor_role: str,
        reason: str,
    ) -> dict[str, Any]:
        """Updates an operational policy, increments its version, and logs an auditable event."""
        if key not in cls._POLICIES:
            raise KeyError(f"Policy '{key}' does not exist.")

        policy = cls._POLICIES[key]
        old_val = policy["value"]

        # Typecast and validate
        if policy["type"] == "int":
            val = int(new_value)
            if val < 0:
                raise ValueError(f"Policy '{key}' value cannot be negative.")
        elif policy["type"] == "float":
            val = float(new_value)
            if val < 0:
                raise ValueError(f"Policy '{key}' value cannot be negative.")
        else:
            val = str(new_value)

        # Version increment
        current_ver = float(policy.get("version", "1.0"))
        new_ver = f"{round(current_ver + 0.1, 1)}"
        now_str = datetime.now(timezone.utc).isoformat()

        # Update in-memory policy registry
        policy["value"] = val
        policy["version"] = new_ver
        policy["last_modified_by"] = f"USER_{actor_id}"
        policy["last_modified_at"] = now_str

        # Audit the policy change
        AuditService.log_event(
            db=db,
            action="POLICY_UPDATED",
            entity_type="POLICY",
            actor_id=actor_id,
            actor_role=actor_role,
            entity_id=key,
            result="SUCCESS",
            reason=reason,
            source="ADMIN_GOVERNANCE",
            before_state={"value": old_val, "version": current_ver},
            after_state={"value": val, "version": new_ver},
            metadata={"policy_key": key, "reason": reason},
        )

        return policy
