import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import get_current_user, get_db
from datetime import datetime, timezone

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, RoleCompetency
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.schemas.assessment import AssessmentSubmitRequest, AssessmentSubmitResponse
from app.services.misconception_tracker import track_response
from app.services.orchestrator import recalculate_competency_state

from pydantic import BaseModel

class AssessmentNextRequest(BaseModel):
    competency_id: int | None = None
    subskill_id: int | None = None

router = APIRouter(tags=["assessment"])


@router.post("/assessment/next")
def get_next_assessment_question(
    payload: AssessmentNextRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    competency_id = payload.competency_id if payload else None
    subskill_id = payload.subskill_id if payload else None

    query = select(AssessmentItem).where(AssessmentItem.user_id.is_(None))
    if subskill_id is not None:
        query = query.where(AssessmentItem.subskill_id == subskill_id)
    elif competency_id is not None:
        query = query.where(AssessmentItem.competency_id == competency_id)

    answered_subquery = (
        select(AssessmentResponse.assessment_item_id)
        .join(AssessmentAttempt, AssessmentAttempt.id == AssessmentResponse.attempt_id)
        .where(AssessmentAttempt.user_id == user.id)
    )
    unanswered_item = db.execute(
        query.where(AssessmentItem.id.notin_(answered_subquery)).order_by(AssessmentItem.id)
    ).scalars().first()

    item = unanswered_item
    if not item:
        fallback_q = select(AssessmentItem).where(AssessmentItem.user_id.is_(None))
        if competency_id:
            fallback_q = fallback_q.where(AssessmentItem.competency_id == competency_id)
        item = db.execute(fallback_q.order_by(AssessmentItem.id)).scalars().first()

    if not item:
        return {
            "status": "SUFFICIENT_EVIDENCE",
            "sufficient_evidence": True,
            "stop_reason": "No questions available for this module.",
        }

    try:
        options = json.loads(item.options_json) if isinstance(item.options_json, str) else item.options_json
    except Exception:
        options = ["Option A", "Option B", "Option C", "Option D"]

    return {
        "status": "QUESTION_PROPOSED",
        "sufficient_evidence": False,
        "question_id": item.id,
        "competency_id": item.competency_id,
        "subskill_id": item.subskill_id,
        "question_text": item.question_text,
        "options": options,
        "difficulty": item.difficulty or "medium",
    }


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
            authorized = db.execute(
                select(RoleCompetency.id).where(
                    RoleCompetency.role_id == user.role_id,
                    RoleCompetency.competency_id == competency.id,
                )
            ).scalar_one_or_none()
            if authorized is None:
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

            attempt = AssessmentAttempt(user_id=user.id, competency_id=payload.competency_id)
            db.add(attempt)
            db.flush()
            correct = 0
            snapshots: list[AssessmentItem] = []
            responses: list[AssessmentResponse] = []
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
                responses.append(
                    AssessmentResponse(
                        attempt_id=attempt.id,
                        assessment_item_id=source_item.id,
                        competency_id=source_item.competency_id,
                        subskill_id=source_item.subskill_id,
                        selected_option=selected,
                        is_correct=selected == source_item.correct_option.strip().upper(),
                        answered_at=datetime.now(timezone.utc),
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
            attempt.score = score
            attempt.completed_at = datetime.now(timezone.utc)
            db.add_all(responses)
            db.add_all(snapshots)
            db.flush()
            for response in responses:
                track_response(db, response)
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

            return AssessmentSubmitResponse(
                status="success",
                message="Assessment submitted successfully",
                assessment_id=snapshots[0].id,
                score=score,
                evidence_id=attempt.id,
            )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Database error during submission") from exc


class RunnerAssessmentSubmitRequest(BaseModel):
    competency_id: int = 1
    tier: str = "easy"
    score: int
    passed: bool
    total_questions: int
    correct_count: int


@router.post("/assessment/runner-submit")
def runner_submit_assessment(
    payload: RunnerAssessmentSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        db.rollback()
        with db.begin():
            attempt = AssessmentAttempt(
                user_id=user.id,
                competency_id=payload.competency_id,
                score=payload.score / 100.0,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(attempt)
            db.flush()

            db.add(
                Evidence(
                    user_id=user.id,
                    competency_id=payload.competency_id,
                    evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
                    title=f"Assessment Tier {payload.tier.upper()} ({payload.score}%)",
                    description=f"Completed {payload.total_questions}-question assessment. Score: {payload.score}% ({payload.correct_count}/{payload.total_questions} correct).",
                    score=payload.score / 100.0,
                    weight=1.0,
                    evidence_metadata=json.dumps({
                        "tier": payload.tier,
                        "total_questions": payload.total_questions,
                        "correct_count": payload.correct_count,
                        "passed": payload.passed,
                    }),
                )
            )
            db.flush()

            try:
                recalculate_competency_state(db, user.id, payload.competency_id)
            except Exception as orch_err:
                print(f"[WARN] Failed recalculating competency state: {orch_err}")

        return {
            "status": "success",
            "message": "Assessment and evidence recorded successfully",
            "attempt_id": attempt.id,
            "user_id": user.id,
            "score": payload.score,
            "passed": payload.passed,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
