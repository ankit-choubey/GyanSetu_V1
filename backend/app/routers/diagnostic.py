import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency
from app.models.competency_state import CompetencyState
from app.models.diagnostic import DiagnosticItem, DiagnosticSession
from app.models.user import User
from app.schemas.diagnostic import (
    DiagnosticAnswerRequest,
    DiagnosticAnswerResponse,
    DiagnosticQuestionPayload,
    DiagnosticSessionStatus,
    DiagnosticStartRequest,
    DiagnosticStartResponse,
)
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(tags=["diagnostic"])


@router.post("/diagnostic/start", response_model=DiagnosticStartResponse)
def start_diagnostic(
    payload: DiagnosticStartRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticStartResponse:
    try:
        db.rollback()
        with db.begin():
            competency = db.get(Competency, payload.competency_id)
            if not competency:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")

            service = DiagnosticService()
            try:
                session, first_question = service.start_session(
                    db,
                    user_id=user.id,
                    user_role_id=user.role_id,
                    competency_id=payload.competency_id,
                    max_questions=payload.max_questions,
                )
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

            # Fetch current competency state for baseline
            state = db.execute(
                select(CompetencyState).where(
                    CompetencyState.user_id == user.id,
                    CompetencyState.competency_id == payload.competency_id,
                )
            ).scalar_one_or_none()

            return DiagnosticStartResponse(
                session_id=session.id,
                competency_id=competency.id,
                competency_name=competency.name,
                status=session.status,
                baseline_mastery=state.mastery if state else None,
                baseline_confidence=state.confidence if state else 0.0,
                baseline_uncertainty=state.uncertainty if state else 1.0,
                first_question=first_question,
            )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to initialize diagnostic session") from exc


@router.get("/diagnostic/{session_id}/next", response_model=DiagnosticQuestionPayload)
def get_next_diagnostic_question(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticQuestionPayload:
    session = db.get(DiagnosticSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic session not found")
    if session.status != "IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Diagnostic session is {session.status}")

    # Check pending
    pending_item = db.execute(
        select(DiagnosticItem).where(
            DiagnosticItem.session_id == session.id,
            DiagnosticItem.answered_at.is_(None),
        )
    ).scalar_one_or_none()

    if pending_item:
        from app.models.assessment import AssessmentItem
        from app.models.competency import SubSkill
        from app.services.diagnostic_service import _format_question_payload
        source_item = db.get(AssessmentItem, pending_item.assessment_item_id)
        subskill = db.get(SubSkill, source_item.subskill_id) if source_item.subskill_id else None
        return _format_question_payload(
            session.id,
            source_item,
            subskill.name if subskill else None,
            pending_item.selected_difficulty,
            pending_item.selection_rationale or "Next adaptive question",
        )

    # Otherwise select next
    try:
        db.rollback()
        with db.begin():
            service = DiagnosticService()
            payload = service.select_and_present_next_question(db, session)
            if not payload:
                raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Diagnostic session completed; no more questions")
            return payload
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to retrieve next adaptive question") from exc


@router.post("/diagnostic/respond", response_model=DiagnosticAnswerResponse)
def respond_to_diagnostic_question(
    payload: DiagnosticAnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticAnswerResponse:
    try:
        db.rollback()
        with db.begin():
            service = DiagnosticService()
            try:
                res = service.submit_answer(
                    db,
                    session_id=payload.session_id,
                    user_id=user.id,
                    assessment_item_id=payload.assessment_item_id,
                    selected_option=payload.selected_option,
                    response_time_ms=payload.response_time_ms,
                    hints_used=payload.hints_used,
                )
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

            return DiagnosticAnswerResponse(
                session_id=res.session_id,
                is_correct=res.is_correct,
                score=res.score,
                correct_option=res.correct_option,
                explanation=res.explanation,
                misconception_flagged=res.misconception_flagged,
                updated_mastery=res.updated_mastery,
                updated_confidence=res.updated_confidence,
                updated_uncertainty=res.updated_uncertainty,
                is_complete=res.is_complete,
                stop_reason=res.stop_reason,
                next_question=res.next_question,
            )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process diagnostic response") from exc


@router.get("/diagnostic/{session_id}", response_model=DiagnosticSessionStatus)
def get_diagnostic_session_status(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticSessionStatus:
    session = db.get(DiagnosticSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic session not found")

    competency = db.get(Competency, session.competency_id)
    state = db.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == user.id,
            CompetencyState.competency_id == session.competency_id,
        )
    ).scalar_one_or_none()

    summary_dict = json.loads(session.summary_json) if session.summary_json else None

    return DiagnosticSessionStatus(
        session_id=session.id,
        learner_id=user.id,
        competency_id=session.competency_id,
        competency_name=competency.name if competency else None,
        status=session.status,
        questions_asked=session.questions_asked,
        max_questions=session.max_questions,
        current_mastery=state.mastery if state else None,
        current_confidence=state.confidence if state else 0.0,
        current_uncertainty=state.uncertainty if state else 1.0,
        stop_reason=session.stop_reason,
        summary=summary_dict,
    )
