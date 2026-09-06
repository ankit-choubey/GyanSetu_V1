import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import get_current_user, get_db
from app.models.assessment import AssessmentItem
from app.models.competency import Competency
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.schemas.assessment import (
    AdaptiveQuestionRequest,
    AdaptiveQuestionResponse,
    AnswerFeedback,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
)
from app.services.ml_providers import AdaptiveItemQuestionSelector
from app.services.orchestrator import (
    coordinate_diagnostic,
    coordinate_intervention,
    recalculate_competency_state,
)
from ml_pipeline.api_interface import evaluate_officer_submission

router = APIRouter(tags=["assessment"])


@router.post("/assessment/next", response_model=AdaptiveQuestionResponse)
def get_next_question(
    payload: AdaptiveQuestionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdaptiveQuestionResponse:
    competency = db.get(Competency, payload.competency_id)
    if not competency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")
    if competency.role_id != user.role_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Competency is outside the authenticated user's scope")

    selector = AdaptiveItemQuestionSelector(db, session_history=payload.session_history)
    try:
        orch_res, decision = coordinate_diagnostic(db, user.id, payload.competency_id, selector)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if decision.sufficient_evidence or not decision.next_question:
        return AdaptiveQuestionResponse(
            status="SUFFICIENT_EVIDENCE",
            sufficient_evidence=True,
            stop_reason=decision.stop_reason,
            competency_id=payload.competency_id,
            subskill_id=decision.target_subskill_id,
        )

    q = decision.next_question
    return AdaptiveQuestionResponse(
        status="QUESTION_PROPOSED",
        sufficient_evidence=False,
        stop_reason=decision.stop_reason,
        question_id=q.question_id,
        competency_id=q.competency_id,
        subskill_id=q.subskill_id,
        question_text=q.question_text,
        options=list(q.options),
        difficulty=q.difficulty,
    )


@router.post("/assessment/submit", response_model=AssessmentSubmitResponse)
def submit_assessment(
    payload: AssessmentSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentSubmitResponse:
    if not payload.answers:
        raise HTTPException(status_code=400, detail="At least one answer is required")
    question_ids = [answer.question_id for answer in payload.answers]
    if len(set(question_ids)) != len(question_ids):
        raise HTTPException(status_code=400, detail="Duplicate question IDs are not valid")

    try:
        # Current-user resolution may have opened a read transaction on this shared session.
        db.rollback()
        with db.begin():
            competency = db.get(Competency, payload.competency_id)
            if not competency:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")
            if competency.role_id != user.role_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Competency is outside the authenticated user's scope")

            items = db.execute(
                select(AssessmentItem).where(
                    AssessmentItem.id.in_(question_ids),
                    AssessmentItem.competency_id == payload.competency_id,
                    AssessmentItem.user_id.is_(None),
                )
            ).scalars().all()
            items_by_id = {item.id: item for item in items}
            if len(items_by_id) != len(question_ids):
                raise HTTPException(status_code=400, detail="One or more assessment questions are invalid")

            correct = 0
            snapshots: list[AssessmentItem] = []
            feedbacks: list[AnswerFeedback] = []

            for answer in payload.answers:
                source_item = items_by_id[answer.question_id]
                try:
                    options = json.loads(source_item.options_json)
                except json.JSONDecodeError as exc:
                    raise HTTPException(status_code=500, detail="Stored assessment item is malformed") from exc
                labels = {str(option).split(".", 1)[0].strip().upper() for option in options}
                selected = answer.selected.strip().upper()
                if selected not in labels:
                    raise HTTPException(status_code=400, detail="Answer does not match the stored question options")
                if selected == source_item.correct_option.strip().upper():
                    correct += 1

                # Generate diagnostic feedback via ML pipeline
                mcq_dict = {
                    "question": source_item.question_text,
                    "options": options,
                    "correct_answer": source_item.correct_option,
                    "subskill": str(source_item.subskill_id or ""),
                }
                try:
                    fb_res = evaluate_officer_submission(mcq_dict, selected)
                    feedbacks.append(
                        AnswerFeedback(
                            question_id=answer.question_id,
                            selected=selected,
                            is_correct=fb_res.get("is_correct", False),
                            feedback=fb_res.get("feedback", ""),
                            identified_gap=fb_res.get("identified_gap"),
                        )
                    )
                except Exception:
                    feedbacks.append(
                        AnswerFeedback(
                            question_id=answer.question_id,
                            selected=selected,
                            is_correct=selected == source_item.correct_option.strip().upper(),
                            feedback="Response recorded.",
                        )
                    )

                snapshots.append(
                    AssessmentItem(
                        user_id=user.id,
                        competency_id=source_item.competency_id,
                        subskill_id=source_item.subskill_id,
                        question_text=source_item.question_text,
                        options_json=source_item.options_json,
                        correct_option=source_item.correct_option,
                        difficulty=source_item.difficulty,
                        source_reference=source_item.source_reference,
                    )
                )

            score = correct / len(payload.answers)
            db.add_all(snapshots)
            db.flush()
            db.add(
                Evidence(
                    user_id=user.id,
                    competency_id=payload.competency_id,
                    evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
                    title="Diagnostic assessment submission",
                    description="Server-scored assessment evidence",
                    score=score,
                    weight=1.0,
                    evidence_metadata=json.dumps({"question_ids": question_ids}),
                )
            )
            db.flush()

            orchestration = recalculate_competency_state(
                db,
                user.id,
                payload.competency_id,
            )

            # Determine next best action for identified gap
            nba_dict = None
            try:
                nba = coordinate_intervention(db, user.id, orchestration)
                nba_dict = {
                    "target_subskill_id": nba.target_subskill_id,
                    "gap_reason": nba.gap_reason,
                    "selected_intervention": {
                        "id": nba.selected.intervention_id,
                        "title": nba.selected.title,
                        "type": nba.selected.intervention_type,
                        "reason": nba.selected.reason,
                    } if nba.selected else None,
                    "explanation": nba.explanation,
                    "uncertainty": nba.uncertainty,
                }
            except Exception:
                pass

            return AssessmentSubmitResponse(
                status="success",
                message="Assessment submitted successfully",
                assessment_id=snapshots[0].id,
                score=score,
                feedback=feedbacks,
                competency_status=orchestration.state.status,
                mastery=orchestration.state.mastery,
                confidence=orchestration.state.confidence,
                next_best_action=nba_dict,
            )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Assessment submission failed; no changes were saved") from exc
