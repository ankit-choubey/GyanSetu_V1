from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.schemas.evening import AdminAnalyticsResponse, CompetencyAnalytics

router = APIRouter(tags=["admin"])


@router.get("/admin/analytics/competencies", response_model=AdminAnalyticsResponse)
def competency_analytics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminAnalyticsResponse:
    roles = {role.id: role for role in db.execute(select(Role)).scalars().all()}
    users = db.execute(select(User).where(User.role_id.is_not(None))).scalars().all()
    states = db.execute(select(CompetencyState)).scalars().all()
    states_by_competency: dict[int, list[CompetencyState]] = {}
    for state in states:
        if state.competency_id is not None:
            states_by_competency.setdefault(state.competency_id, []).append(state)

    analytics: list[CompetencyAnalytics] = []
    for competency in db.execute(select(Competency).order_by(Competency.id)).scalars().all():
        role_links = db.execute(
            select(RoleCompetency).where(RoleCompetency.competency_id == competency.id)
        ).scalars().all()
        role_ids = {link.role_id for link in role_links}
        role = roles.get(next(iter(role_ids))) if len(role_ids) == 1 else None
        role_users = [user for user in users if user.role_id in role_ids]
        competency_states = states_by_competency.get(competency.id, [])
        mastery_values = [state.mastery for state in competency_states if state.mastery is not None]
        status_distribution = Counter(state.status for state in competency_states)
        analytics.append(
            CompetencyAnalytics(
                role_id=next(iter(role_ids)) if len(role_ids) == 1 else None,
                role_name=role.name if role else None,
                competency_id=competency.id,
                competency_name=competency.name,
                learner_count=len(role_users),
                assessed_count=len(mastery_values),
                average_mastery=round(sum(mastery_values) / len(mastery_values), 2) if mastery_values else None,
                average_confidence=round(sum(state.confidence for state in competency_states) / len(competency_states), 2) if competency_states else 0.0,
                average_coverage=round(sum(state.coverage for state in competency_states) / len(competency_states), 2) if competency_states else 0.0,
                total_evidence=sum(state.evidence_count for state in competency_states),
                status_distribution=dict(status_distribution),
            )
        )

    return AdminAnalyticsResponse(competencies=analytics, total_competencies=len(analytics))


@router.get("/admin/validation/scientific-audit")
def get_scientific_audit(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve comprehensive scientific validation audit, provenance catalog, and calibration report."""
    from app.services.scientific_validation_service import ScientificValidationService
    return ScientificValidationService.get_full_audit(db=db)


@router.get("/admin/validation/model-selection-gate")
def get_model_selection_gate(
    admin: User = Depends(get_current_admin),
) -> list[dict]:
    """Retrieve formal model selection gates with candidate status, decisions, and justifications."""
    from app.services.scientific_validation_service import ScientificValidationService
    return ScientificValidationService.get_model_gates()

