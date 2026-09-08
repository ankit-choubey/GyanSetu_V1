import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.assessment import AssessmentAttempt
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.next_best_action_service import NextBestActionService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/learner", response_model=DashboardResponse)
def get_learner_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    role = db.get(Role, user.role_id) if user.role_id else None
    competencies = db.execute(
        select(Competency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .where(RoleCompetency.role_id == user.role_id)
        .order_by(Competency.id)
    ).scalars().all()

    competency_summaries: list[dict[str, Any]] = []
    for competency in competencies:
        state = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == user.id,
                CompetencyState.competency_id == competency.id,
            )
        ).scalar_one_or_none()
        if state is None:
            state_payload = {
                "competency_id": competency.id,
                "competency_name": competency.name,
                "mastery": None,
                "confidence": 0.0,
                "coverage": 0.0,
                "evidence_count": 0,
                "status": "UNASSESSED",
            }
        else:
            state_payload = {
                "competency_id": competency.id,
                "competency_name": competency.name,
                "mastery": state.mastery,
                "confidence": state.confidence,
                "coverage": state.coverage,
                "evidence_count": state.evidence_count,
                "status": state.status,
            }
        competency_summaries.append(state_payload)

    # Calculate real activity & work completed by this specific user
    total_evidence = db.execute(
        select(func.count(Evidence.id)).where(Evidence.user_id == user.id)
    ).scalar_one() or 0

    sum_comp_evidence = sum(c.get("evidence_count", 0) for c in competency_summaries)
    total_evidence = max(total_evidence, sum_comp_evidence)

    evaluations_completed = db.execute(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.user_id == user.id,
        )
    ).scalar_one() or 0

    is_admin = (role and "admin" in role.name.lower()) or user.role_id == 9

    nba_payload: dict[str, Any] | None = None
    try:
        nba_service = NextBestActionService()
        rec = nba_service.get_next_best_action(db, user)
        if rec and rec.selected_intervention_id:
            sel_int = db.get(Intervention, rec.selected_intervention_id)
            expl_data = json.loads(rec.explanation_json) if rec.explanation_json else {}
            reason_str = expl_data.get("why") or expl_data.get("reason") or "Targeted skill calibration recommended."
            int_type = "PRACTICE"
            if sel_int and hasattr(sel_int, "intervention_type"):
                int_type = str(sel_int.intervention_type.value if hasattr(sel_int.intervention_type, "value") else sel_int.intervention_type)
            nba_payload = {
                "target_subskill_id": rec.target_subskill_id,
                "gap_reason": rec.objective or "Targeted skill gap identified",
                "selected_intervention": {
                    "id": sel_int.id if sel_int else rec.selected_intervention_id,
                    "title": sel_int.title if sel_int else "Core Statistical Practice",
                    "type": int_type,
                    "reason": reason_str,
                },
                "explanation": reason_str,
                "uncertainty": round(1.0 - (rec.confidence or 0.7), 2),
            }
    except Exception:
        pass

    return DashboardResponse(
        user_id=user.id,
        full_name=user.full_name,
        role_name=role.name if role else ("Administrator" if is_admin else "Statistical Officer"),
        designation="Workforce Platform Administrator" if is_admin else "Statistical Officer",
        department="DIID & Training Planning (MoSPI)" if is_admin else "National Accounts Division (NAD)",
        competencies=competency_summaries,
        total_competencies=len(competency_summaries),
        evaluations_completed=evaluations_completed,
        total_evidence_records=total_evidence,
        next_best_action=nba_payload,
    )
