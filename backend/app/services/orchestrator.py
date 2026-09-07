from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.services.competency_engine import CompetencyCalculation, calculate_competency_state, identify_gaps


@dataclass(frozen=True)
class OrchestrationResult:
    state: CompetencyState
    calculation: CompetencyCalculation


def recalculate_competency_state(
    db: Session,
    user_id: int,
    competency_id: int,
    *,
    triggering_evidence_id: int | None = None,
    now: datetime | None = None,
) -> OrchestrationResult:
    """Recalculate state inside the caller's transaction; this function never commits."""
    competency = db.get(Competency, competency_id)
    if competency is None:
        raise ValueError(f"Competency {competency_id} does not exist")

    evidence = db.execute(
        select(Evidence).where(
            Evidence.user_id == user_id,
            Evidence.competency_id == competency_id,
        ).order_by(Evidence.id)
    ).scalars().all()
    subskills = list(competency.subskills)
    calculation = calculate_competency_state(evidence, len(subskills), now=now)
    calculation = CompetencyCalculation(
        mastery=calculation.mastery,
        confidence=calculation.confidence,
        coverage=calculation.coverage,
        evidence_count=calculation.evidence_count,
        evidence_diversity=calculation.evidence_diversity,
        status=calculation.status,
        gaps=identify_gaps(evidence, subskills, calculation),
        message=calculation.message,
    )

    state = db.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == user_id,
            CompetencyState.competency_id == competency_id,
        )
    ).scalar_one_or_none()

    prev_mastery = state.mastery if state else None
    prev_confidence = state.confidence if state else 0.0
    prev_status = state.status if state else "UNASSESSED"
    prev_version = getattr(state, "state_version", 0) if state else 0

    if state is None:
        state = CompetencyState(user_id=user_id, competency_id=competency_id)
        db.add(state)

    state.mastery = calculation.mastery
    state.confidence = calculation.confidence
    state.coverage = calculation.coverage
    state.evidence_count = calculation.evidence_count
    state.evidence_diversity = calculation.evidence_diversity
    state.status = (
        "UNASSESSED"
        if calculation.evidence_count == 0
        else "CONFLICTING_EVIDENCE"
        if calculation.status == "CONFLICTING_EVIDENCE"
        else "ASSESSED"
    )
    state.state_version = prev_version + 1
    state.last_assessed_at = now or datetime.now(timezone.utc)
    state.updated_at = now or datetime.now(timezone.utc)
    db.flush()

    # Record versioned history transition
    latest_evidence_id = triggering_evidence_id or (evidence[-1].id if evidence else None)
    history_entry = CompetencyHistory(
        user_id=user_id,
        competency_id=competency_id,
        previous_mastery=prev_mastery,
        new_mastery=state.mastery,
        previous_confidence=prev_confidence,
        new_confidence=state.confidence,
        previous_status=prev_status,
        new_status=state.status,
        triggering_evidence_id=latest_evidence_id,
        calculation_version="v2.0-deterministic",
        state_version=state.state_version,
        timestamp=now or datetime.now(timezone.utc),
    )
    db.add(history_entry)
    db.flush()

    return OrchestrationResult(state=state, calculation=calculation)


def coordinate_diagnostic(db: Session, user_id: int, competency_id: int, selector):
    """Calculate once, then pass the result to the backend diagnostic workflow."""
    from app.services.diagnostic_agent import DiagnosticAgent

    result = recalculate_competency_state(db, user_id, competency_id)
    decision = DiagnosticAgent().decide(competency_id, result.calculation, selector)
    return result, decision


def coordinate_intervention(db: Session, user_id: int, result: OrchestrationResult):
    """Use the engine-produced gap without recalculating competency."""
    from app.services.intervention_agent import InterventionAgent

    gap = result.calculation.gaps[0] if result.calculation.gaps else {}
    return InterventionAgent().rank(db, user_id, result.state.competency_id, gap)
