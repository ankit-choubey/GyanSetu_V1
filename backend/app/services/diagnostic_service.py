from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.assessment_signal import AssessmentSignal
from app.models.competency import Competency, RoleCompetency, SubSkill
from app.models.diagnostic import DiagnosticItem, DiagnosticSession
from app.models.evidence import Evidence, EvidenceType
from app.models.misconception import Misconception
from app.schemas.diagnostic import DiagnosticQuestionPayload
from app.services.misconception_tracker import track_response
from app.services.orchestrator import recalculate_competency_state

logger = logging.getLogger("gyansetu.diagnostic")


@dataclass(frozen=True)
class DiagnosticAnswerResult:
    session_id: int
    is_correct: bool
    score: float
    correct_option: str | None
    explanation: str | None
    misconception_flagged: bool
    updated_mastery: float | None
    updated_confidence: float
    updated_uncertainty: float
    is_complete: bool
    stop_reason: str | None
    next_question: DiagnosticQuestionPayload | None


def _format_question_payload(
    session_id: int,
    item: AssessmentItem,
    subskill_name: str | None,
    difficulty: str,
    rationale: str,
) -> DiagnosticQuestionPayload:
    options_raw = json.loads(item.options_json) if item.options_json else []
    return DiagnosticQuestionPayload(
        question_id=item.id,
        competency_id=item.competency_id,
        subskill_id=item.subskill_id,
        subskill_name=subskill_name,
        difficulty=difficulty,
        question_text=item.question_text,
        options=[str(opt) for opt in options_raw],
        source_reference=item.source_reference,
        selection_rationale=rationale,
    )


def select_adaptive_or_fallback(
    item_bank: list[dict[str, Any]],
    session_history: list[dict[str, Any]],
    competency_name: str | None = None,
) -> dict[str, Any]:
    """Connect to ML AdaptiveSelector with deterministic fallback guarantee."""
    try:
        from ml_pipeline.adaptive_selector import select_next_question as ml_select
        result = ml_select(item_bank, session_history, competency=competency_name)
        if isinstance(result, dict) and "next_question" in result:
            return result
    except Exception as exc:
        logger.warning(f"ML adaptive selector fallback triggered: {exc}")

    # Deterministic fallback algorithm
    answered_ids = {h.get("question_id") for h in session_history if h.get("question_id")}
    available = [q for q in item_bank if q.get("question_id") not in answered_ids]
    if not available:
        return {
            "next_question": None,
            "target_difficulty": "medium",
            "target_subskill": None,
            "is_complete": True,
            "reason": "Deterministic fallback: all candidate items attempted.",
        }

    target_diff = "easy" if not session_history else ("medium" if session_history[-1].get("is_correct") else "easy")
    matched = [q for q in available if q.get("difficulty", "medium").lower() == target_diff]
    candidate = matched[0] if matched else available[0]
    return {
        "next_question": candidate,
        "target_difficulty": candidate.get("difficulty", "medium"),
        "target_subskill": candidate.get("subskill"),
        "is_complete": False,
        "reason": f"Deterministic fallback selected item matching difficulty '{target_diff}'.",
    }


class DiagnosticService:
    """Manages adaptive diagnostic session state, item presentation, and evidence loop."""

    def start_session(
        self,
        db: Session,
        user_id: int,
        user_role_id: int | None,
        competency_id: int,
        max_questions: int = 5,
    ) -> tuple[DiagnosticSession, DiagnosticQuestionPayload | None]:
        competency = db.get(Competency, competency_id)
        if not competency:
            raise ValueError(f"Competency {competency_id} not found")

        if user_role_id is not None:
            authorized = db.execute(
                select(RoleCompetency.id).where(
                    RoleCompetency.role_id == user_role_id,
                    RoleCompetency.competency_id == competency_id,
                )
            ).scalar_one_or_none()
            if authorized is None:
                raise PermissionError("Competency is outside the authenticated user's role scope")

        # Reuse existing in-progress session if any
        existing_session = db.execute(
            select(DiagnosticSession).where(
                DiagnosticSession.user_id == user_id,
                DiagnosticSession.competency_id == competency_id,
                DiagnosticSession.status == "IN_PROGRESS",
            )
        ).scalar_one_or_none()

        if existing_session:
            # Check if there is an unanswered item
            pending_item = db.execute(
                select(DiagnosticItem).where(
                    DiagnosticItem.session_id == existing_session.id,
                    DiagnosticItem.answered_at.is_(None),
                )
            ).scalar_one_or_none()
            if pending_item:
                assessment_item = db.get(AssessmentItem, pending_item.assessment_item_id)
                subskill = db.get(SubSkill, assessment_item.subskill_id) if assessment_item.subskill_id else None
                payload = _format_question_payload(
                    existing_session.id,
                    assessment_item,
                    subskill.name if subskill else None,
                    pending_item.selected_difficulty,
                    pending_item.selection_rationale or "Resumed diagnostic item.",
                )
                return existing_session, payload

            # Otherwise select next question
            next_payload = self.select_and_present_next_question(db, existing_session)
            return existing_session, next_payload

        # Create new session
        session = DiagnosticSession(
            user_id=user_id,
            competency_id=competency_id,
            status="IN_PROGRESS",
            current_difficulty="easy",
            max_questions=max_questions,
            questions_asked=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.flush()

        first_payload = self.select_and_present_next_question(db, session)
        return session, first_payload

    def select_and_present_next_question(
        self,
        db: Session,
        session: DiagnosticSession,
    ) -> DiagnosticQuestionPayload | None:
        """Selects the next adaptive question, records the presented DiagnosticItem, and returns payload."""
        if session.status != "IN_PROGRESS":
            return None

        if session.questions_asked >= session.max_questions:
            session.status = "COMPLETED"
            session.completed_at = datetime.now(timezone.utc)
            session.stop_reason = "MAX_QUESTIONS_REACHED"
            db.flush()
            return None

        # Build session history
        past_items = db.execute(
            select(DiagnosticItem).where(
                DiagnosticItem.session_id == session.id,
                DiagnosticItem.answered_at.is_not(None),
            ).order_by(DiagnosticItem.id)
        ).scalars().all()

        session_history = []
        attempted_ids = set()
        for pi in past_items:
            attempted_ids.add(pi.assessment_item_id)
            sub = db.get(SubSkill, pi.subskill_id) if pi.subskill_id else None
            session_history.append({
                "question_id": pi.assessment_item_id,
                "subskill": sub.name if sub else None,
                "difficulty": pi.selected_difficulty,
                "is_correct": bool(pi.is_correct),
            })

        # Load candidate assessment items from DB
        items = db.execute(
            select(AssessmentItem).where(
                AssessmentItem.competency_id == session.competency_id,
                AssessmentItem.user_id.is_(None),
            )
        ).scalars().all()

        competency = db.get(Competency, session.competency_id)
        comp_name = competency.name if competency else None

        item_pool = []
        for itm in items:
            sub = db.get(SubSkill, itm.subskill_id) if itm.subskill_id else None
            item_pool.append({
                "question_id": itm.id,
                "question": itm.question_text,
                "subskill": sub.name if sub else None,
                "competency": comp_name,
                "difficulty": (itm.difficulty or "medium").lower(),
                "source_reference": itm.source_reference,
            })

        selection = select_adaptive_or_fallback(item_pool, session_history, comp_name)

        chosen_candidate = selection.get("next_question")
        if not chosen_candidate or selection.get("is_complete"):
            session.status = "COMPLETED"
            session.completed_at = datetime.now(timezone.utc)
            session.stop_reason = "POOL_EXHAUSTED"
            db.flush()
            return None

        chosen_id = chosen_candidate.get("question_id")
        source_item = db.get(AssessmentItem, chosen_id)
        if not source_item:
            session.status = "COMPLETED"
            session.stop_reason = "ITEM_RETRIEVAL_ERROR"
            db.flush()
            return None

        target_diff = selection.get("target_difficulty", source_item.difficulty or "medium")
        target_subskill_name = chosen_candidate.get("subskill")
        rationale = (
            f"Selected because: {selection.get('reason', 'Adaptive progression')} "
            f"[Target difficulty: {target_diff}, Subskill: {target_subskill_name or 'General'}]."
        )

        diagnostic_item = DiagnosticItem(
            session_id=session.id,
            assessment_item_id=source_item.id,
            subskill_id=source_item.subskill_id,
            selected_difficulty=target_diff,
            selection_rationale=rationale,
            presented_at=datetime.now(timezone.utc),
        )
        db.add(diagnostic_item)
        session.questions_asked += 1
        session.current_difficulty = target_diff
        session.target_subskill_id = source_item.subskill_id
        db.flush()

        return _format_question_payload(
            session.id,
            source_item,
            target_subskill_name,
            target_diff,
            rationale,
        )

    def submit_answer(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        assessment_item_id: int,
        selected_option: str,
        response_time_ms: int | None = None,
        hints_used: int = 0,
    ) -> DiagnosticAnswerResult:
        session = db.get(DiagnosticSession, session_id)
        if not session or session.user_id != user_id:
            raise PermissionError("Diagnostic session not found or outside learner scope")

        if session.status != "IN_PROGRESS":
            raise ValueError(f"Diagnostic session is {session.status}, cannot submit answers")

        diag_item = db.execute(
            select(DiagnosticItem).where(
                DiagnosticItem.session_id == session_id,
                DiagnosticItem.assessment_item_id == assessment_item_id,
                DiagnosticItem.answered_at.is_(None),
            )
        ).scalar_one_or_none()

        if not diag_item:
            raise ValueError(f"No pending question found for assessment item {assessment_item_id} in this session")

        source_item = db.get(AssessmentItem, assessment_item_id)
        if not source_item:
            raise ValueError(f"Assessment item {assessment_item_id} does not exist")

        options = json.loads(source_item.options_json) if source_item.options_json else []
        labels = {str(opt).split(".", 1)[0].strip().upper() for opt in options}
        clean_selected = selected_option.strip().upper()
        if clean_selected not in labels:
            raise ValueError(f"Selected option '{selected_option}' does not match available choices: {labels}")

        is_correct = clean_selected == source_item.correct_option.strip().upper()
        score = 1.0 if is_correct else 0.0

        # Update diagnostic item
        diag_item.answered_at = datetime.now(timezone.utc)
        diag_item.selected_option = clean_selected
        diag_item.is_correct = is_correct
        diag_item.score = score

        # Create or update attempt tracking
        attempt = db.execute(
            select(AssessmentAttempt).where(
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.competency_id == session.competency_id,
            ).order_by(AssessmentAttempt.id.desc())
        ).scalars().first()

        existing_resp = None
        if attempt:
            existing_resp = db.execute(
                select(AssessmentResponse).where(
                    AssessmentResponse.attempt_id == attempt.id,
                    AssessmentResponse.assessment_item_id == source_item.id,
                )
            ).scalar_one_or_none()

        if not attempt or attempt.completed_at is not None or existing_resp is not None:
            attempt = AssessmentAttempt(
                user_id=user_id,
                competency_id=session.competency_id,
                started_at=datetime.now(timezone.utc),
            )
            db.add(attempt)
            db.flush()

        resp = AssessmentResponse(
            attempt_id=attempt.id,
            assessment_item_id=source_item.id,
            competency_id=source_item.competency_id,
            subskill_id=source_item.subskill_id,
            selected_option=clean_selected,
            is_correct=is_correct,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(resp)
        db.flush()

        # Track signals if provided
        if response_time_ms is not None or hints_used > 0:
            signal = AssessmentSignal(
                attempt_id=attempt.id,
                assessment_response_id=resp.id,
                response_time_ms=response_time_ms or 0,
                hints_used=hints_used,
            )
            db.add(signal)

        # Track misconception on wrong answers
        misconception_flagged = False
        if not is_correct:
            track_res = track_response(db, resp)
            misconception_flagged = track_res.misconception is not None

        # Record Evidence in the Evidence Ledger
        subskill = db.get(SubSkill, source_item.subskill_id) if source_item.subskill_id else None
        evidence = Evidence(
            user_id=user_id,
            competency_id=session.competency_id,
            subskill_id=source_item.subskill_id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title=f"Adaptive Diagnostic: {source_item.difficulty or 'medium'} question",
            description=f"Automated diagnostic question on {subskill.name if subskill else 'general competency'}",
            score=score,
            weight=0.20,
            source="ADAPTIVE_DIAGNOSTIC",
            provenance="[LIVE INTEGRATION]",
            reliability_status="VERIFIED",
            assessment_item_id=source_item.id,
            version=1,
            evidence_metadata=json.dumps({
                "session_id": session_id,
                "difficulty": diag_item.selected_difficulty,
                "is_correct": is_correct,
                "response_time_ms": response_time_ms,
            }),
            observed_at=datetime.now(timezone.utc),
        )
        db.add(evidence)
        db.flush()

        # Atomic recalculation of CompetencyState and CompetencyHistory
        orch = recalculate_competency_state(
            db,
            user_id=user_id,
            competency_id=session.competency_id,
            triggering_evidence_id=evidence.id,
        )

        # Check stopping criteria
        is_complete = False
        stop_reason = None
        next_q = None

        if orch.state.status == "verified" or (orch.state.confidence or 0.0) >= 0.80:
            is_complete = True
            stop_reason = "CONFIDENCE_CONVERGENCE"
        elif session.questions_asked >= session.max_questions:
            is_complete = True
            stop_reason = "MAX_QUESTIONS_REACHED"
        else:
            next_q = self.select_and_present_next_question(db, session)
            if next_q is None:
                is_complete = True
                stop_reason = session.stop_reason or "POOL_EXHAUSTED"

        if is_complete:
            session.status = "COMPLETED"
            session.completed_at = datetime.now(timezone.utc)
            session.stop_reason = stop_reason
            session.summary_json = json.dumps({
                "final_mastery": orch.state.mastery,
                "final_confidence": orch.state.confidence,
                "final_status": orch.state.status,
                "questions_asked": session.questions_asked,
                "stop_reason": stop_reason,
            })

        db.flush()

        explanation = (
            f"Correct! Item tested {subskill.name if subskill else 'competency'}."
            if is_correct
            else f"Incorrect. Correct answer is {source_item.correct_option}. Item tested {subskill.name if subskill else 'competency'}."
        )

        return DiagnosticAnswerResult(
            session_id=session.id,
            is_correct=is_correct,
            score=score,
            correct_option=source_item.correct_option,
            explanation=explanation,
            misconception_flagged=misconception_flagged,
            updated_mastery=orch.state.mastery,
            updated_confidence=orch.state.confidence,
            updated_uncertainty=orch.state.uncertainty,
            is_complete=is_complete,
            stop_reason=stop_reason,
            next_question=next_q,
        )
