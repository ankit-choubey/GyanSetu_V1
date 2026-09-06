from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentResponse
from app.models.evidence import Evidence
from app.models.misconception import Misconception

UNCLASSIFIED_TYPE = "UNCLASSIFIED_WRONG_ANSWER_PATTERN"
UNCLASSIFIED_DESCRIPTION = "Semantic classification unavailable; deterministic wrong-answer pattern only."


def build_pattern_key(assessment_item_id: int, selected_option: str) -> str:
    normalized_option = selected_option.strip().upper()
    if assessment_item_id <= 0 or not normalized_option:
        raise ValueError("Assessment item ID and selected option are required")
    return f"assessment_item:{assessment_item_id}|selected_option:{normalized_option}"


@dataclass(frozen=True)
class ClassifierResult:
    misconception_type: str
    description: str


class MisconceptionClassifier(Protocol):
    def classify(self, response: AssessmentResponse) -> ClassifierResult:
        """Future semantic classifier boundary; no implementation is provided here."""


@dataclass(frozen=True)
class MisconceptionTrackResult:
    misconception: Misconception | None
    classifier_status: str


def track_response(
    db: Session,
    response: AssessmentResponse,
    *,
    now: datetime | None = None,
    classifier: MisconceptionClassifier | None = None,
) -> MisconceptionTrackResult:
    if response.is_correct:
        return MisconceptionTrackResult(misconception=None, classifier_status="NOT_APPLICABLE")
    if response.attempt is None or response.attempt.user_id is None:
        raise ValueError("Assessment response must be linked to an attempt and learner")
    if response.competency_id is None or response.assessment_item_id is None:
        raise ValueError("Assessment response must identify competency and assessment item")

    pattern_key = build_pattern_key(response.assessment_item_id, response.selected_option)
    existing = db.execute(
        select(Misconception).where(
            Misconception.learner_id == response.attempt.user_id,
            Misconception.competency_id == response.competency_id,
            Misconception.subskill_id == response.subskill_id,
            Misconception.pattern_key == pattern_key,
        )
    ).scalar_one_or_none()
    observed_at = now or response.answered_at or datetime.now(timezone.utc)

    if existing is not None:
        existing.occurrences += 1
        existing.last_observed = observed_at
        db.flush()
        return MisconceptionTrackResult(existing, "AVAILABLE" if classifier else "UNAVAILABLE")

    classification = classifier.classify(response) if classifier is not None else None
    record = Misconception(
        learner_id=response.attempt.user_id,
        competency_id=response.competency_id,
        subskill_id=response.subskill_id,
        pattern_key=pattern_key,
        misconception_type=classification.misconception_type if classification else UNCLASSIFIED_TYPE,
        description=classification.description if classification else UNCLASSIFIED_DESCRIPTION,
        occurrences=1,
        first_observed=observed_at,
        last_observed=observed_at,
        resolved=False,
    )
    db.add(record)
    db.flush()
    return MisconceptionTrackResult(record, "AVAILABLE" if classifier else "UNAVAILABLE")


def resolve_misconception(
    db: Session,
    misconception_id: int,
    *,
    resolution_evidence_id: int | None = None,
    intervention_applied: bool | None = None,
) -> Misconception:
    record = db.get(Misconception, misconception_id)
    if record is None:
        raise ValueError("Misconception not found")
    if resolution_evidence_id is not None:
        evidence = db.get(Evidence, resolution_evidence_id)
        if evidence is None or evidence.user_id != record.learner_id:
            raise ValueError("Resolution evidence does not belong to the learner")
        record.resolution_evidence_id = resolution_evidence_id
    if intervention_applied is not None:
        record.intervention_applied = intervention_applied
    record.resolved = True
    db.flush()
    return record