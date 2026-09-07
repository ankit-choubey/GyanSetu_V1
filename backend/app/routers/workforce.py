"""Phase 7: Workforce Intelligence, Governance, and Fairness API Router.

Strict Non-Autonomous HR Decision Support:
- Read-only, advisory aggregates.
- Protected by administrative authorization (get_current_admin).
- Learners rejected with 403 Forbidden.
- Small-cell suppression (N < 5).
- Zero learner IDs in responses.
- Automatic WorkforceAuditLog recording.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_admin
from app.services.workforce_analytics_service import WorkforceAnalyticsService
from app.services.fairness_audit_service import FairnessAuditService
from app.services.data_quality_service import DataQualityService
from app.services.governance_service import GovernanceService
from app.models.governance import ReviewStatus

router = APIRouter(
    prefix="/workforce",
    tags=["Workforce Intelligence & Governance"],
)


@router.get("/overview")
def read_workforce_overview(
    minimum_group_size: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Return high-level workforce capability overview with small-cell privacy suppression."""
    return WorkforceAnalyticsService.get_overview(
        db,
        actor=admin,
        min_group_size=minimum_group_size,
    )


@router.get("/competencies")
def read_competency_aggregates(
    minimum_group_size: int = Query(5, ge=1, le=100),
    role_id: Optional[int] = Query(None),
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Aggregated competency distribution across operational cohorts."""
    return WorkforceAnalyticsService.get_competencies_aggregate(
        db,
        role_id=role_id,
        domain_name=domain,
        actor=admin,
        min_group_size=minimum_group_size,
    )


@router.get("/gaps")
def read_gap_triage(
    minimum_group_size: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Confidence-aware organizational gap triage: ACTIONABLE vs NEEDS_MORE_EVIDENCE."""
    return WorkforceAnalyticsService.get_prioritized_gaps(
        db,
        actor=admin,
        min_group_size=minimum_group_size,
    )


@router.get("/trends")
def read_longitudinal_trends(
    minimum_group_size: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Longitudinal competency trajectory monitoring (IMPROVING, STABLE, DECLINING)."""
    return WorkforceAnalyticsService.get_longitudinal_trends(
        db,
        actor=admin,
        min_group_size=minimum_group_size,
    )


@router.get("/interventions")
def read_intervention_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Intervention outcome associations using non-causal language."""
    return WorkforceAnalyticsService.get_intervention_analytics(
        db,
        actor=admin,
    )


@router.get("/retention")
def read_retention_monitoring(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Observed vs modelled retention monitoring distinguishing fresh evidence from decayed states."""
    return WorkforceAnalyticsService.get_retention_monitoring(
        db,
        actor=admin,
    )


@router.get("/emerging-skills")
def read_emerging_skills(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Conservative emerging skills radar with explicit time window and provenance."""
    return WorkforceAnalyticsService.get_emerging_skills_radar(
        db,
        actor=admin,
    )


@router.get("/fairness")
def read_fairness_audit(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Four-fifths disparity checks across operational cohorts. Safely handles missing demographics."""
    res = FairnessAuditService.audit_operational_fairness(db)
    WorkforceAnalyticsService.log_audit_event(
        db,
        endpoint="/api/workforce/fairness",
        actor=admin,
        requested_scope="OPERATIONAL_ROLES",
        fairness_status=res.get("overall_classification"),
    )
    return res


@router.get("/data-quality")
def read_data_quality_audit(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Data quality & integrity diagnostics (stale, conflicting, low confidence, under review)."""
    res = DataQualityService.audit_data_quality(db)
    WorkforceAnalyticsService.log_audit_event(
        db,
        endpoint="/api/workforce/data-quality",
        actor=admin,
        requested_scope="ALL_DIAGNOSTICS",
        insights_count=len(res.get("quality_warnings", [])),
    )
    return res


@router.get("/quality")
def read_workforce_quality(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Canonical alias for data quality audit diagnostics."""
    return read_data_quality_audit(db=db, admin=admin)


@router.get("/insights")
def read_administrative_insights(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Explainable administrative insights linking findings to underlying evidence."""
    return WorkforceAnalyticsService.get_administrative_insights(
        db,
        actor=admin,
    )


@router.get("/governance/competency/{competency_id}")
def read_competency_governance(
    competency_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Get governance status and lifecycle of a specific competency."""
    gov = GovernanceService.get_competency_governance(db, competency_id)
    if not gov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competency ID {competency_id} not found in governance registry.",
        )
    return gov


@router.post("/governance/competency/{competency_id}")
def update_competency_governance_record(
    competency_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Update review status and governance metadata for a competency."""
    new_status = payload.get("review_status")
    review_notes = payload.get("review_notes")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="review_status is required.",
        )
    try:
        status_enum = ReviewStatus(new_status)
    except ValueError:
        valid = [s.value for s in ReviewStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review_status. Must be one of {valid}",
        )
    try:
        admin_name = admin.full_name or admin.email
        updated = GovernanceService.update_review_status(
            db,
            competency_id=competency_id,
            review_status=status_enum,
            notes=review_notes,
            reviewer=f"{admin_name} (Admin ID {admin.id})",
        )
        return {"status": "success", "governance": updated}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/governance/models")
def read_model_registry(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Model registry listing all analytical and diagnostic models with statuses."""
    models = GovernanceService.get_model_registry(db)
    return {
        "model_registry": models,
        "total_registered": len(models),
    }


@router.get("/audit-logs")
def read_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Retrieve recorded administrative workforce access audit logs."""
    logs = WorkforceAnalyticsService.get_audit_logs(db, limit=limit)
    return {
        "audit_logs": [
            {
                "id": log.id,
                "actor_id": log.actor_id,
                "actor_email": log.actor_email,
                "actor_role": log.actor_role,
                "endpoint": log.endpoint,
                "requested_scope": log.requested_scope,
                "suppressed_groups_count": log.suppressed_groups_count,
                "authorization_decision": log.authorization_decision,
                "insights_generated_count": log.insights_generated_count,
                "fairness_audit_status": log.fairness_audit_status,
                "data_timestamp": log.data_timestamp.isoformat() if log.data_timestamp else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
