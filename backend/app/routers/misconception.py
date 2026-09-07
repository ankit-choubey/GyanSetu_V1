from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, SubSkill
from app.models.misconception import Misconception
from app.models.user import User
from app.schemas.misconception import MisconceptionRead, MisconceptionsResponse

router = APIRouter(tags=["misconception"])


@router.get("/misconceptions", response_model=MisconceptionsResponse)
def get_learner_misconceptions(
    competency_id: int | None = Query(default=None, description="Filter by competency ID"),
    resolved: bool | None = Query(default=None, description="Filter by resolved status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MisconceptionsResponse:
    query = select(Misconception).where(Misconception.learner_id == user.id)

    if competency_id is not None:
        query = query.where(Misconception.competency_id == competency_id)
    if resolved is not None:
        query = query.where(Misconception.resolved == resolved)

    query = query.order_by(Misconception.last_observed.desc())
    records = db.execute(query).scalars().all()

    items: list[MisconceptionRead] = []
    active_count = 0
    resolved_count = 0

    for m in records:
        if m.resolved:
            resolved_count += 1
        else:
            active_count += 1

        comp = db.get(Competency, m.competency_id) if m.competency_id else None
        sub = db.get(SubSkill, m.subskill_id) if m.subskill_id else None
        items.append(
            MisconceptionRead(
                id=m.id,
                learner_id=m.learner_id,
                competency_id=m.competency_id,
                competency_name=comp.name if comp else None,
                subskill_id=m.subskill_id,
                subskill_name=sub.name if sub else None,
                pattern_key=m.pattern_key,
                misconception_type=m.misconception_type,
                description=m.description,
                occurrences=m.occurrences,
                first_observed=m.first_observed,
                last_observed=m.last_observed,
                intervention_applied=m.intervention_applied,
                resolved=m.resolved,
                resolution_evidence_id=m.resolution_evidence_id,
            )
        )

    return MisconceptionsResponse(
        learner_id=user.id,
        total_misconceptions=len(items),
        active_count=active_count,
        resolved_count=resolved_count,
        misconceptions=items,
    )
