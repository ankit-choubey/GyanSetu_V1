from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.schemas.competency import CompetencyHistoryRead, CompetencyStateDetailRead

router = APIRouter(tags=["competency"])


@router.get("/competencies/{role_id}")
def get_role_competencies(
    role_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if user.role_id != role_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is outside the authenticated user's scope")

    competencies = db.execute(
        select(Competency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .where(RoleCompetency.role_id == role_id)
        .order_by(Competency.id)
    ).scalars().all()
    return {
        "role_id": role.id,
        "role_name": role.name,
        "competencies": [
            {
                "id": comp.id,
                "name": comp.name,
                "description": comp.description,
            }
            for comp in competencies
        ],
        "user_id": user.id,
    }


@router.get("/competency/state", response_model=list[CompetencyStateDetailRead])
def get_all_competency_states(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CompetencyStateDetailRead]:
    # Query competencies assigned to learner's role
    comps = db.execute(
        select(Competency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .where(RoleCompetency.role_id == user.role_id)
        .order_by(Competency.id)
    ).scalars().all()

    results: list[CompetencyStateDetailRead] = []
    for c in comps:
        st = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == user.id,
                CompetencyState.competency_id == c.id,
            )
        ).scalar_one_or_none()

        if st:
            results.append(
                CompetencyStateDetailRead(
                    competency_id=c.id,
                    competency_name=c.name,
                    mastery=st.mastery,
                    confidence=st.confidence,
                    uncertainty=st.uncertainty,
                    coverage=st.coverage,
                    evidence_count=st.evidence_count,
                    evidence_diversity=st.evidence_diversity,
                    status=st.status,
                    state_version=st.state_version,
                    last_assessed_at=st.last_assessed_at,
                    updated_at=st.updated_at,
                )
            )
        else:
            results.append(
                CompetencyStateDetailRead(
                    competency_id=c.id,
                    competency_name=c.name,
                    mastery=None,
                    confidence=0.0,
                    uncertainty=1.0,
                    coverage=0.0,
                    evidence_count=0,
                    evidence_diversity=0,
                    status="UNASSESSED",
                    state_version=1,
                    last_assessed_at=None,
                    updated_at=None,
                )
            )
    return results


@router.get("/competency/state/{competency_id}", response_model=CompetencyStateDetailRead)
def get_single_competency_state(
    competency_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompetencyStateDetailRead:
    comp = db.get(Competency, competency_id)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")

    st = db.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == user.id,
            CompetencyState.competency_id == competency_id,
        )
    ).scalar_one_or_none()

    if not st:
        return CompetencyStateDetailRead(
            competency_id=comp.id,
            competency_name=comp.name,
            mastery=None,
            confidence=0.0,
            uncertainty=1.0,
            coverage=0.0,
            evidence_count=0,
            evidence_diversity=0,
            status="UNASSESSED",
            state_version=1,
            last_assessed_at=None,
            updated_at=None,
        )

    return CompetencyStateDetailRead(
        competency_id=comp.id,
        competency_name=comp.name,
        mastery=st.mastery,
        confidence=st.confidence,
        uncertainty=st.uncertainty,
        coverage=st.coverage,
        evidence_count=st.evidence_count,
        evidence_diversity=st.evidence_diversity,
        status=st.status,
        state_version=st.state_version,
        last_assessed_at=st.last_assessed_at,
        updated_at=st.updated_at,
    )


@router.get("/competency/history/{competency_id}", response_model=list[CompetencyHistoryRead])
def get_competency_history(
    competency_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CompetencyHistoryRead]:
    comp = db.get(Competency, competency_id)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")

    records = db.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == user.id,
            CompetencyHistory.competency_id == competency_id,
        ).order_by(CompetencyHistory.timestamp.asc(), CompetencyHistory.id.asc())
    ).scalars().all()

    return [
        CompetencyHistoryRead(
            id=r.id,
            competency_id=r.competency_id,
            previous_mastery=r.previous_mastery,
            new_mastery=r.new_mastery,
            previous_confidence=r.previous_confidence,
            new_confidence=r.new_confidence,
            previous_status=r.previous_status,
            new_status=r.new_status,
            triggering_evidence_id=r.triggering_evidence_id,
            calculation_version=r.calculation_version,
            state_version=r.state_version,
            timestamp=r.timestamp,
        )
        for r in records
    ]


@router.get("/competency/timeline")
def get_learner_longitudinal_timeline(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieves multi-competency longitudinal progression timeline for the authenticated learner."""
    from app.services.longitudinal_analytics_service import LongitudinalAnalyticsService
    return LongitudinalAnalyticsService.get_learner_timeline(db, user_id=user.id)


@router.get("/competency/timeline/{competency_id}")
def get_learner_competency_longitudinal_history(
    competency_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieves detailed longitudinal state transitions and evidence trajectory for a specific competency."""
    from app.services.longitudinal_analytics_service import LongitudinalAnalyticsService
    res = LongitudinalAnalyticsService.get_competency_history(db, user_id=user.id, competency_id=competency_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res

