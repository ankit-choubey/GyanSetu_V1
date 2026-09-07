from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.monitoring_event import MonitoringEvent
from app.models.user import User
from app.schemas.monitoring import MonitoringEventRequest, MonitoringEventType
from app.services.ml_interfaces import ProposedQuestion, QuestionSelector
from app.services.orchestrator import coordinate_diagnostic, recalculate_competency_state


@dataclass(frozen=True)
class MonitoringResult:
    event_id: int
    event_type: MonitoringEventType
    significance: str
    status: str
    action: str
    result: dict[str, Any]


_SIGNIFICANCE_BY_EVENT: dict[MonitoringEventType, str] = {
    MonitoringEventType.ASSESSMENT_COMPLETED: "SIGNIFICANT",
    MonitoringEventType.REPEATED_FAILURE: "HIGH",
    MonitoringEventType.EVIDENCE_STALE: "HIGH",
    MonitoringEventType.DELAYED_CHECK_DUE: "HIGH",
    MonitoringEventType.COMPETENCY_REQUIREMENT_ADDED: "SIGNIFICANT",
    MonitoringEventType.INTERVENTION_COMPLETED: "SIGNIFICANT",
}


class MonitoringAgent:
    """Persist monitoring events and coordinate deterministic backend workflows."""

    def handle_event(
        self,
        db: Session,
        request: MonitoringEventRequest,
        *,
        diagnostic_selector: QuestionSelector | None = None,
    ) -> MonitoringResult:
        self._validate_context(db, request)
        event = MonitoringEvent(
            event_type=request.event_type.value,
            significance=_SIGNIFICANCE_BY_EVENT[request.event_type],
            status="PENDING",
            learner_id=request.learner_id,
            competency_id=request.competency_id,
            subskill_id=request.subskill_id,
            source_entity_type=request.source_entity_type,
            source_entity_id=request.source_entity_id,
            event_metadata=self._serialize_metadata(request.metadata or {}),
            occurred_at=request.occurred_at or datetime.now(timezone.utc),
            scheduled_for=request.scheduled_at,
        )
        db.add(event)
        db.flush()

        action, status, result = self._dispatch(
            db,
            request,
            diagnostic_selector=diagnostic_selector,
        )
        event.status = status
        event.event_metadata = self._serialize_metadata({**(request.metadata or {}), **result})
        db.flush()
        return MonitoringResult(
            event_id=event.id,
            event_type=request.event_type,
            significance=event.significance,
            status=status,
            action=action,
            result=result,
        )

    def _dispatch(
        self,
        db: Session,
        request: MonitoringEventRequest,
        *,
        diagnostic_selector: QuestionSelector | None,
    ) -> tuple[str, str, dict[str, Any]]:
        if request.event_type is MonitoringEventType.ASSESSMENT_COMPLETED:
            self._require_competency(request)
            orchestration = recalculate_competency_state(db, request.learner_id, request.competency_id)
            return (
                "COMPETENCY_STATE_RECALCULATED",
                "PROCESSED",
                {
                    "competency_state_id": orchestration.state.id,
                    "competency_status": orchestration.state.status,
                    "gap_count": len(orchestration.calculation.gaps),
                },
            )

        if request.event_type is MonitoringEventType.REPEATED_FAILURE:
            self._require_competency(request)
            if diagnostic_selector is None:
                return (
                    "DIAGNOSTIC_PENDING",
                    "PROVIDER_UNAVAILABLE",
                    {"reason": "Question selector provider is unavailable."},
                )
            _, decision = coordinate_diagnostic(
                db,
                request.learner_id,
                request.competency_id,
                diagnostic_selector,
            )
            return (
                "DIAGNOSTIC_TRIGGERED",
                "PROCESSED",
                {
                    "sufficient_evidence": decision.sufficient_evidence,
                    **(
                        {"next_question": self._serialize_question(decision.next_question)}
                        if decision.next_question is not None
                        else {}
                    ),
                },
            )

        if request.event_type is MonitoringEventType.EVIDENCE_STALE:
            evidence = self._validate_stale_evidence(db, request)
            return (
                "RETENTION_CHECK_PENDING",
                "PROVIDER_UNAVAILABLE",
                {
                    "reason": "Retention provider is unavailable; no interval was predicted.",
                    "evidence_observed_at": evidence.observed_at.isoformat(),
                },
            )

        if request.event_type is MonitoringEventType.DELAYED_CHECK_DUE:
            self._require_competency(request)
            return (
                "REASSESSMENT_PENDING",
                "PENDING",
                {"reason": "A reassessment is due and awaits an assessment workflow."},
            )

        if request.event_type is MonitoringEventType.COMPETENCY_REQUIREMENT_ADDED:
            self._require_competency(request)
            state = db.execute(
                select(CompetencyState).where(
                    CompetencyState.user_id == request.learner_id,
                    CompetencyState.competency_id == request.competency_id,
                )
            ).scalar_one_or_none()
            gap = state is None or state.mastery is None or state.mastery < 0.70
            return (
                "REQUIREMENT_GAP_EVALUATED",
                "PROCESSED",
                {
                    "required_competency_id": request.competency_id,
                    "competency_state_id": state.id if state is not None else None,
                    "gap": gap,
                    "reason": "No assessed competency state exists."
                    if state is None
                    else "Competency mastery is below the configured threshold."
                    if gap
                    else "Existing competency state meets the configured threshold.",
                },
            )

        if request.event_type is MonitoringEventType.INTERVENTION_COMPLETED:
            self._require_competency(request)
            return (
                "POST_ASSESSMENT_PENDING",
                "PENDING",
                {"reason": "Explicit intervention completion received; post-assessment awaits scheduling."},
            )

        raise ValueError(f"Unsupported monitoring event type: {request.event_type}")

    @staticmethod
    def _serialize_metadata(metadata: dict[str, Any]) -> str:
        try:
            return json.dumps(metadata, default=str)
        except (TypeError, ValueError) as exc:
            raise ValueError("Monitoring metadata must be JSON-serializable") from exc

    @staticmethod
    def _serialize_question(question: ProposedQuestion) -> dict[str, Any]:
        return {
            "question_id": question.question_id,
            "competency_id": question.competency_id,
            "subskill_id": question.subskill_id,
            "question_text": question.question_text,
            "options": list(question.options),
            "difficulty": question.difficulty,
            "source_reference": question.source_reference,
        }

    @staticmethod
    def _require_competency(request: MonitoringEventRequest) -> None:
        if request.competency_id is None:
            raise ValueError(f"{request.event_type.value} requires competency_id")

    @staticmethod
    def _validate_stale_evidence(db: Session, request: MonitoringEventRequest) -> Evidence:
        if request.source_entity_id is None or request.source_entity_type != "evidence":
            raise ValueError("evidence_stale requires source_entity_type='evidence' and source_entity_id")
        evidence = db.get(Evidence, request.source_entity_id)
        if evidence is None or evidence.user_id != request.learner_id:
            raise ValueError("Evidence does not belong to the learner")
        if request.competency_id is not None and evidence.competency_id != request.competency_id:
            raise ValueError("Evidence does not belong to the requested competency")
        stale_before = (request.metadata or {}).get("stale_before")
        if stale_before is not None:
            if not isinstance(stale_before, str):
                raise ValueError("metadata.stale_before must be an ISO timestamp")
            try:
                threshold = datetime.fromisoformat(stale_before)
            except ValueError as exc:
                raise ValueError("metadata.stale_before must be an ISO timestamp") from exc
            observed_at = evidence.observed_at
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=timezone.utc)
            if threshold.tzinfo is None:
                threshold = threshold.replace(tzinfo=timezone.utc)
            if observed_at >= threshold:
                raise ValueError("Evidence is not stale at the supplied threshold")
        return evidence

    @staticmethod
    def _validate_context(db: Session, request: MonitoringEventRequest) -> None:
        if db.get(User, request.learner_id) is None:
            raise ValueError("Learner not found")
        if request.competency_id is not None:
            if db.get(Competency, request.competency_id) is None:
                raise ValueError("Competency not found")
            allowed = db.execute(
                select(RoleCompetency.id)
                .join(User, User.role_id == RoleCompetency.role_id)
                .where(User.id == request.learner_id, RoleCompetency.competency_id == request.competency_id)
            ).scalar_one_or_none()
            if allowed is None:
                raise ValueError("Competency is outside the learner's scope")
        if request.subskill_id is not None:
            subskill = db.get(SubSkill, request.subskill_id)
            if subskill is None or (
                request.competency_id is not None and subskill.competency_id != request.competency_id
            ):
                raise ValueError("Subskill does not belong to the requested competency")