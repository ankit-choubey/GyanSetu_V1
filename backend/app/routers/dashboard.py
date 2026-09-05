from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, Role
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.schemas.dashboard import DashboardResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/learner", response_model=DashboardResponse)
def get_learner_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    role = db.get(Role, user.role_id) if user.role_id else None
    competencies = db.execute(select(Competency).where(Competency.role_id == user.role_id)).scalars().all()

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

    return DashboardResponse(
        user_id=user.id,
        full_name=user.full_name,
        role_name=role.name if role else None,
        competencies=competency_summaries,
        total_competencies=len(competency_summaries),
    )
