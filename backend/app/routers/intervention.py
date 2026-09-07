from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.intervention import Intervention
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.schemas.intervention import (
    InterventionCreate,
    InterventionOutcomeRequest,
    InterventionOutcomeResponse,
    InterventionRead,
    NextBestActionRequest,
    RecommendationFeedbackRequest,
    RecommendationResponse,
)
from app.services.intervention_lifecycle_service import InterventionLifecycleService
from app.services.next_best_action_service import NextBestActionService

router = APIRouter(tags=["interventions"])

lifecycle_service = InterventionLifecycleService()
nba_service = NextBestActionService()


def _format_recommendation_response(rec: RecommendationRecord, db: Session) -> RecommendationResponse:
    sel_intervention = None
    if rec.selected_intervention_id:
        sel_intervention = db.get(Intervention, rec.selected_intervention_id)

    explanation_dict = json.loads(rec.explanation_json) if rec.explanation_json else {}
    alternatives_list = json.loads(rec.alternatives_json) if rec.alternatives_json else []
    rejected_list = json.loads(rec.rejected_candidates_json) if rec.rejected_candidates_json else []

    sel_read = None
    if sel_intervention:
        sel_read = InterventionRead.model_validate(sel_intervention)

    return RecommendationResponse(
        recommendation_id=rec.recommendation_id,
        user_id=rec.user_id,
        competency_id=rec.competency_id,
        target_subskill_id=rec.target_subskill_id,
        selected_intervention=sel_read,
        action_type=rec.action_type,
        status=rec.status,
        objective=rec.objective,
        confidence=rec.confidence,
        policy_version=rec.policy_version,
        explanation=explanation_dict,
        alternatives=alternatives_list,
        rejected_candidates=rejected_list,
        created_at=rec.created_at,
    )


# ---------------------------------------------------------------------------
# Intervention Catalogue Endpoints
# ---------------------------------------------------------------------------

@router.get("/interventions", response_model=list[InterventionRead])
def list_interventions(
    competency_id: int | None = Query(default=None),
    subskill_id: int | None = Query(default=None),
    provider: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InterventionRead]:
    query = select(Intervention)
    if competency_id is not None:
        query = query.where(Intervention.competency_id == competency_id)
    if subskill_id is not None:
        query = query.where(Intervention.subskill_id == subskill_id)
    if provider is not None:
        query = query.where(Intervention.provider == provider)
    if status_filter is not None:
        query = query.where(Intervention.status == status_filter)

    items = db.execute(query.offset(offset).limit(limit)).scalars().all()
    return [InterventionRead.model_validate(item) for item in items]


@router.get("/interventions/{intervention_id}", response_model=InterventionRead)
def get_intervention_details(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionRead:
    item = db.get(Intervention, intervention_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    return InterventionRead.model_validate(item)


@router.post("/interventions", response_model=InterventionRead, status_code=status.HTTP_201_CREATED)
def register_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> InterventionRead:
    item = Intervention(
        title=payload.title,
        description=payload.description,
        intervention_type=payload.intervention_type,
        provider=payload.provider,
        modality=payload.modality,
        duration_minutes=payload.duration_minutes,
        difficulty=payload.difficulty,
        competency_id=payload.competency_id,
        subskill_id=payload.subskill_id,
        availability=payload.availability,
        status=payload.status,
        source=payload.source,
        provenance=payload.provenance,
        prerequisites_json=payload.prerequisites_json,
        target_misconception_pattern=payload.target_misconception_pattern,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return InterventionRead.model_validate(item)


# ---------------------------------------------------------------------------
# Recommendation & Next Best Action Endpoints
# ---------------------------------------------------------------------------

@router.post("/recommendations/next-best-action", response_model=RecommendationResponse)
def compute_next_best_action(
    payload: NextBestActionRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    target_comp_id = payload.competency_id if payload else None
    rec = nba_service.get_next_best_action(db, learner=current_user, competency_id=target_comp_id)
    return _format_recommendation_response(rec, db)


@router.get("/recommendations/{recommendation_id}/explanation")
def get_recommendation_explanation(
    recommendation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    rec = db.execute(
        select(RecommendationRecord).where(
            RecommendationRecord.recommendation_id == recommendation_id
        )
    ).scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    # Strict learner isolation
    if rec.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to recommendation prohibited")

    explanation_dict = json.loads(rec.explanation_json) if rec.explanation_json else {}
    rejected_list = json.loads(rec.rejected_candidates_json) if rec.rejected_candidates_json else []
    alternatives_list = json.loads(rec.alternatives_json) if rec.alternatives_json else []

    return {
        "recommendation_id": rec.recommendation_id,
        "selected_intervention_id": rec.selected_intervention_id,
        "action_type": rec.action_type,
        "policy_version": rec.policy_version,
        "explanation": explanation_dict,
        "rejected_candidates": rejected_list,
        "alternatives": alternatives_list,
    }


@router.post("/recommendations/{recommendation_id}/feedback", response_model=RecommendationResponse)
def submit_recommendation_feedback(
    recommendation_id: str,
    payload: RecommendationFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    rec = db.execute(
        select(RecommendationRecord).where(
            RecommendationRecord.recommendation_id == recommendation_id
        )
    ).scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    if rec.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access prohibited")

    try:
        updated_rec = lifecycle_service.record_feedback(
            db, user=current_user, recommendation_id=recommendation_id, action=payload.action, notes=payload.notes
        )
        return _format_recommendation_response(updated_rec, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/start", response_model=RecommendationResponse)
def start_recommended_intervention(
    recommendation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    rec = db.execute(
        select(RecommendationRecord).where(
            RecommendationRecord.recommendation_id == recommendation_id
        )
    ).scalar_one_or_none()

    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    if rec.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access prohibited")

    try:
        updated_rec = lifecycle_service.start_intervention(db, user=current_user, recommendation_id=recommendation_id)
        return _format_recommendation_response(updated_rec, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Outcome Recording & Evidence Feedback Loop
# ---------------------------------------------------------------------------

@router.post("/interventions/{intervention_id}/outcome", response_model=InterventionOutcomeResponse)
def record_intervention_outcome(
    intervention_id: int,
    payload: InterventionOutcomeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionOutcomeResponse:
    try:
        outcome = lifecycle_service.record_outcome(
            db,
            user=current_user,
            intervention_id=intervention_id,
            status=payload.status,
            completion_score=payload.completion_score,
            has_post_assessment_evidence=payload.has_post_assessment_evidence,
            recommendation_id=payload.recommendation_id,
            idempotency_key=payload.idempotency_key,
            notes=payload.notes,
        )
        return InterventionOutcomeResponse.model_validate(outcome)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
