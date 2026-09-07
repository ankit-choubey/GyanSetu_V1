from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, SubSkill
from app.models.evidence import Evidence
from app.models.user import User
from app.schemas.evidence import EvidenceLedgerResponse, EvidenceRead

router = APIRouter(tags=["evidence"])


@router.get("/evidence", response_model=EvidenceLedgerResponse)
def get_evidence_ledger(
    competency_id: int | None = Query(default=None, description="Filter by competency ID"),
    evidence_type: str | None = Query(default=None, description="Filter by evidence type"),
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceLedgerResponse:
    query = select(Evidence).where(Evidence.user_id == user.id)

    if competency_id is not None:
        query = query.where(Evidence.competency_id == competency_id)
    if evidence_type is not None:
        query = query.where(Evidence.evidence_type == evidence_type)

    query = query.order_by(Evidence.observed_at.desc()).limit(limit)
    records = db.execute(query).scalars().all()

    items: list[EvidenceRead] = []
    for r in records:
        comp = db.get(Competency, r.competency_id) if r.competency_id else None
        sub = db.get(SubSkill, r.subskill_id) if r.subskill_id else None
        items.append(
            EvidenceRead(
                id=r.id,
                user_id=r.user_id,
                competency_id=r.competency_id,
                competency_name=comp.name if comp else None,
                subskill_id=r.subskill_id,
                subskill_name=sub.name if sub else None,
                evidence_type=str(r.evidence_type.value if hasattr(r.evidence_type, "value") else r.evidence_type),
                title=r.title,
                description=r.description,
                score=r.score,
                weight=r.weight,
                source=r.source or "INTERNAL",
                provenance=r.provenance or "[CURATED]",
                reliability_status=r.reliability_status or "VERIFIED",
                assessment_item_id=r.assessment_item_id,
                version=r.version or 1,
                evidence_metadata=r.evidence_metadata,
                observed_at=r.observed_at,
                created_at=r.created_at,
            )
        )

    return EvidenceLedgerResponse(
        learner_id=user.id,
        total_records=len(items),
        evidence=items,
    )
