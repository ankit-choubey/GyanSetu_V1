from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from app.models.evidence import Evidence, EvidenceType

EVIDENCE_WEIGHTS: dict[EvidenceType, float] = {
    EvidenceType.APPLICATION_SCENARIO: 0.35,
    EvidenceType.PRACTICAL_TASK: 0.30,
    EvidenceType.KNOWLEDGE_ASSESSMENT: 0.20,
    EvidenceType.TRAINING_HISTORY: 0.10,
    EvidenceType.WORKPLACE_SIGNAL: 0.05,
    EvidenceType.SELF_REPORT: 0.02,
}


@dataclass(frozen=True)
class CompetencyCalculation:
    mastery: float | None
    confidence: float
    coverage: float
    evidence_count: int
    evidence_diversity: int
    status: str
    gaps: tuple[dict[str, object], ...]
    message: str | None = None


def _recency_weight(observed_at: datetime, now: datetime) -> float:
    timestamp = observed_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - timestamp).days)
    return max(0.3, 1.0 - (age_days * 0.01))


def calculate_competency_state(
    evidence: Iterable[Evidence],
    total_subskills: int,
    *,
    now: datetime | None = None,
) -> CompetencyCalculation:
    evidence_list = list(evidence)
    if not evidence_list:
        return CompetencyCalculation(
            mastery=None,
            confidence=0.0,
            coverage=0.0,
            evidence_count=0,
            evidence_diversity=0,
            status="UNASSESSED",
            gaps=(),
            message="No evidence recorded. Status: Unassessed (Not low competency).",
        )

    current_time = now or datetime.now(timezone.utc)
    distinct_types = len({entry.evidence_type for entry in evidence_list})
    distinct_subskills = {entry.subskill_id for entry in evidence_list if entry.subskill_id is not None}

    weighted_scores: list[float] = []
    total_weight = 0.0
    for entry in evidence_list:
        if entry.score is None:
            continue
        type_weight = EVIDENCE_WEIGHTS.get(entry.evidence_type, 0.10)
        effective_weight = _recency_weight(entry.observed_at, current_time) * type_weight
        weighted_scores.append(entry.score * effective_weight)
        total_weight += effective_weight

    mastery = round(sum(weighted_scores) / total_weight, 2) if total_weight > 0 else None
    # Preserve the Phase 1 state contract: confidence tracks evidence volume and
    # coverage tracks the six documented evidence sources.
    confidence = round(min(0.95, len(evidence_list) / 5), 2)
    coverage = min(1.0, distinct_types / 6)

    if mastery is None:
        status = "UNASSESSED"
    elif _has_conflicting_evidence(evidence_list):
        status = "CONFLICTING_EVIDENCE"
    else:
        status = "verified" if mastery >= 0.70 and confidence >= 0.60 else "developing"

    return CompetencyCalculation(
        mastery=mastery,
        confidence=confidence,
        coverage=coverage,
        evidence_count=len(evidence_list),
        evidence_diversity=distinct_types,
        status=status,
        gaps=(),
    )


def _has_conflicting_evidence(evidence: Iterable[Evidence]) -> bool:
    by_type: dict[EvidenceType, list[float]] = {}
    for entry in evidence:
        if entry.score is not None:
            by_type.setdefault(entry.evidence_type, []).append(entry.score)
    knowledge = by_type.get(EvidenceType.KNOWLEDGE_ASSESSMENT, [])
    application_scores = by_type.get(EvidenceType.APPLICATION_SCENARIO, []) + by_type.get(EvidenceType.PRACTICAL_TASK, [])
    return bool(knowledge and application_scores and max(knowledge) >= 0.95 and min(application_scores) < 0.70)


def identify_gaps(
    evidence: Iterable[Evidence],
    subskills: Iterable[object],
    calculation: CompetencyCalculation,
) -> tuple[dict[str, object], ...]:
    evidence_list = list(evidence)
    subskill_list = list(subskills)
    if not evidence_list:
        return ()

    gaps: list[dict[str, object]] = []
    for subskill in subskill_list:
        subskill_id = getattr(subskill, "id", None)
        subskill_evidence = [entry for entry in evidence_list if entry.subskill_id == subskill_id]
        scored = [entry.score for entry in subskill_evidence if entry.score is not None]
        if not scored:
            gaps.append({"subskill_id": subskill_id, "subskill_name": getattr(subskill, "name", None), "reason": "insufficient_evidence", "severity": 1.0})
            continue
        subskill_mastery = sum(scored) / len(scored)
        if subskill_mastery < 0.70:
            gaps.append({"subskill_id": subskill_id, "subskill_name": getattr(subskill, "name", None), "reason": "low_mastery", "severity": round(1.0 - subskill_mastery, 2)})

    if not subskill_list and calculation.mastery is not None and calculation.mastery < 0.70:
        gaps.append({"subskill_id": None, "subskill_name": None, "reason": "low_mastery", "severity": round(1.0 - calculation.mastery, 2)})
    return tuple(sorted(gaps, key=lambda gap: float(gap["severity"]), reverse=True))
