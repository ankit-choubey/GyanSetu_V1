from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.governance import LifecycleUpdateRequest, PolicyUpdateRequest
from app.services.assessment_analytics_service import AssessmentAnalyticsService
from app.services.audit_service import AuditService
from app.services.data_quality_service import DataQualityService
from app.services.longitudinal_analytics_service import LongitudinalAnalyticsService
from app.services.operational_health_service import OperationalHealthService
from app.services.outcome_analytics_service import OutcomeAnalyticsService
from app.services.policy_service import PolicyService

router = APIRouter(tags=["governance"])


# ==============================================================================
# Operational Health & Observability (Task 7.8)
# ==============================================================================

@router.get("/health")
def get_system_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Public liveness & readiness operational health probe."""
    return OperationalHealthService.check_system_health(db)


@router.get("/health/providers")
def get_providers_health() -> dict[str, Any]:
    """Public ecosystem learning providers runtime health and integration modes."""
    return OperationalHealthService.get_providers_health()


@router.get("/admin/system-status")
@router.get("/admin/health/subsystems")
def get_admin_system_status(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Authoritative administrative system telemetry and table counts."""
    return OperationalHealthService.get_admin_system_status(db)


# ==============================================================================
# Audit & Provenance Ledger (Task 7.1)
# ==============================================================================

@router.get("/admin/audit-logs")
@router.get("/admin/audit/events")
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    actor_id: Optional[int] = Query(None, description="Filter by actor ID"),
    result: Optional[str] = Query(None, description="Filter by result: SUCCESS/FAILURE/DENIED"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieves paginated audit event records with multi-dimensional filtering."""
    events, total = AuditService.get_audit_events(
        db=db,
        action=action,
        entity_type=entity_type,
        actor_id=actor_id,
        result=result,
        correlation_id=correlation_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total_matches": total,
        "returned_count": len(events),
        "limit": limit,
        "offset": offset,
        "events": [e.to_dict() for e in events],
    }


@router.get("/admin/audit-logs/summary")
def get_audit_summary(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Calculates summary statistics and distribution of system audit records."""
    return AuditService.get_audit_summary(db)


@router.get("/admin/audit-logs/{event_id}")
def get_audit_event_by_id(
    event_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieves a single auditable event by event_id or numeric ID."""
    event = AuditService.get_event_by_id(db, identifier=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event '{event_id}' not found.",
        )
    return event.to_dict()


# ==============================================================================
# Data Quality & Integrity Engine (Task 7.1b)
# ==============================================================================

@router.get("/admin/data-quality")
@router.get("/admin/data-quality/diagnostics")
def get_data_quality_audit(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Runs a complete system-wide diagnostic scan of taxonomy, evidence, items, and state."""
    res = DataQualityService.audit_data_quality(db)
    AuditService.log_event(
        db=db,
        action="DATA_QUALITY_SCAN",
        entity_type="SYSTEM",
        actor_id=admin.id,
        actor_role=getattr(admin.role, "name", "ADMINISTRATOR") if admin.role else "ADMINISTRATOR",
        result="SUCCESS",
        metadata={"overall_health_score": res["overall_data_health_score"]},
    )
    return res


@router.get("/admin/data-quality/summary")
def get_data_quality_summary(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """High-level summary scorecard of data health, categorized issues, and overall rating."""
    return DataQualityService.get_summary(db)


@router.get("/admin/data-quality/{category}")
def get_data_quality_category(
    category: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Targeted diagnostic for a specific domain (taxonomy, evidence, assessment, intervention, competency_state)."""
    res = DataQualityService.audit_category(db, category=category)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res["error"])
    return res


# ==============================================================================
# Assessment & Item Analytics (Task 7.2)
# ==============================================================================

@router.get("/admin/assessment/items/analytics")
def get_question_bank_analytics(
    competency_id: Optional[int] = Query(None),
    subskill_id: Optional[int] = Query(None),
    quality_flag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated assessment item response analytics with psychometric filtering."""
    return AssessmentAnalyticsService.get_question_bank_analytics(
        db=db,
        competency_id=competency_id,
        subskill_id=subskill_id,
        quality_flag=quality_flag,
        limit=limit,
        offset=offset,
    )


@router.get("/admin/assessment/items/{item_id}/analytics")
def get_item_statistics(
    item_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Detailed response statistics, difficulty, distractor utilization, and discrimination for an item."""
    res = AssessmentAnalyticsService.get_item_statistics(db, item_id=item_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@router.get("/admin/assessment/items/{item_id}/quality")
def get_item_quality(
    item_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Item quality flags, sample adequacy, and lifecycle recommendation."""
    res = AssessmentAnalyticsService.get_item_statistics(db, item_id=item_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return {
        "item_id": res["item_id"],
        "status": res["status"],
        "sample_size": res["sample_size"],
        "quality_flags": res["quality_flags"],
        "lifecycle_recommendation": res["lifecycle_recommendation"],
    }


# ==============================================================================
# Recommendation & Intervention Outcome Analytics (Task 7.4)
# ==============================================================================

@router.get("/admin/analytics/recommendations")
def get_recommendation_funnel(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Recommendation funnel conversion metrics (generated, accepted, started, completed)."""
    return OutcomeAnalyticsService.get_recommendation_funnel_analytics(db)


@router.get("/admin/analytics/interventions/outcomes")
def get_intervention_outcomes(
    provider: Optional[str] = Query(None),
    competency_id: Optional[int] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Intervention completion rates, observed competency gains, and provider breakdowns."""
    return OutcomeAnalyticsService.get_intervention_outcome_analytics(
        db=db,
        provider=provider,
        competency_id=competency_id,
    )


# ==============================================================================
# Longitudinal Competency Trajectory (Task 7.3)
# ==============================================================================

@router.get("/admin/analytics/learners/{user_id}/longitudinal")
def get_admin_learner_longitudinal(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Administrative multi-competency longitudinal overview for an individual learner."""
    return LongitudinalAnalyticsService.get_learner_timeline(db, user_id=user_id)


@router.get("/admin/analytics/learners/{user_id}/longitudinal/{competency_id}")
def get_admin_learner_competency_longitudinal(
    user_id: int,
    competency_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Administrative detailed competency longitudinal trajectory for an individual learner."""
    res = LongitudinalAnalyticsService.get_competency_history(db, user_id=user_id, competency_id=competency_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


# ==============================================================================
# Policy & Configuration Governance (Task 7.6)
# ==============================================================================

@router.get("/admin/policies")
def get_policies(
    admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Read-only operational policy and threshold configurations."""
    return {
        "policies": PolicyService.get_all_policies(),
        "provenance": "[POLICY_REGISTRY:READ_ONLY]",
    }


@router.post("/admin/policies/{policy_key}")
def update_policy(
    policy_key: str,
    req: PolicyUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Updates an operational policy with audit justification and version incrementation."""
    try:
        updated = PolicyService.update_policy(
            db=db,
            key=policy_key,
            new_value=req.value,
            actor_id=admin.id,
            actor_role=getattr(admin.role, "name", "ADMINISTRATOR") if admin.role else "ADMINISTRATOR",
            reason=req.reason,
        )
        return {
            "policy_key": policy_key,
            "updated_policy": updated,
            "status": "UPDATED",
        }
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
