from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentItem
from app.models.competency import Competency
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.user import User
from app.services.adapters import list_all_adapters


class OperationalHealthService:
    """Operational health diagnostics, provider circuit-breakers, and database telemetry."""

    @classmethod
    def check_system_health(cls, db: Session) -> dict[str, Any]:
        """Performs a multi-subsystem liveness and readiness check."""
        now = datetime.now(timezone.utc)
        subsystems: dict[str, Any] = {}
        is_degraded = False

        # 1. Database Check
        t0 = time.perf_counter()
        try:
            db.execute(text("SELECT 1")).scalar_one()
            db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            subsystems["database"] = {
                "status": "HEALTHY",
                "latency_ms": db_latency_ms,
            }
        except Exception as exc:
            subsystems["database"] = {
                "status": "UNAVAILABLE",
                "error": str(exc),
            }
            return {
                "status": "UNAVAILABLE",
                "timestamp": now.isoformat(),
                "subsystems": subsystems,
            }

        # 2. Provider Check
        providers_status: dict[str, Any] = {}
        unavailable_providers = 0
        for adapter in list_all_adapters():
            name = adapter.get_provider_name()
            health = adapter.health_check()
            providers_status[name] = {
                "status": health.status.value,
                "mode": adapter.get_integration_mode().value,
                "latency_ms": health.latency_ms,
            }
            if health.status.value != "HEALTHY":
                unavailable_providers += 1

        if unavailable_providers > 0:
            is_degraded = True

        subsystems["providers"] = {
            "status": "DEGRADED" if unavailable_providers > 0 else "HEALTHY",
            "total_providers": len(providers_status),
            "healthy_providers": len(providers_status) - unavailable_providers,
            "details": providers_status,
        }

        overall_status = "DEGRADED" if is_degraded else "HEALTHY"

        return {
            "status": overall_status,
            "timestamp": now.isoformat(),
            "subsystems": subsystems,
            "provenance": "[OPERATIONAL_HEALTH:RUNTIME_PROBE]",
        }

    @classmethod
    def get_providers_health(cls) -> dict[str, Any]:
        """Inspects all ecosystem learning provider adapters and returns explicit runtime modes."""
        results: list[dict[str, Any]] = []
        for adapter in list_all_adapters():
            health = adapter.health_check()
            results.append({
                "provider": adapter.get_provider_name(),
                "mode": adapter.get_integration_mode().value,
                "status": health.status.value,
                "latency_ms": health.latency_ms,
                "details": health.details,
                "checked_at": health.checked_at.isoformat(),
            })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers_count": len(results),
            "providers": results,
            "provenance": "[PROVIDER_HEALTH:ACTIVE_PROBE]",
        }

    @classmethod
    def get_admin_system_status(cls, db: Session) -> dict[str, Any]:
        """Provides an authoritative system-of-record metrics dashboard for administrators."""
        health = cls.check_system_health(db)

        # Record counts
        user_count = db.execute(select(func.count(User.id))).scalar_one() or 0
        comp_count = db.execute(select(func.count(Competency.id))).scalar_one() or 0
        item_count = db.execute(select(func.count(AssessmentItem.id))).scalar_one() or 0
        ev_count = db.execute(select(func.count(Evidence.id))).scalar_one() or 0
        intervention_count = db.execute(select(func.count(Intervention.id))).scalar_one() or 0

        return {
            "system_status": health["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "table_record_counts": {
                "users": user_count,
                "competencies": comp_count,
                "assessment_items": item_count,
                "evidence_records": ev_count,
                "interventions": intervention_count,
            },
            "subsystems": health["subsystems"],
            "deployment_mode": "DEVELOPMENT_SIMULATION",
            "provenance": "[SYSTEM_STATUS:ADMIN_METRICS]",
        }
