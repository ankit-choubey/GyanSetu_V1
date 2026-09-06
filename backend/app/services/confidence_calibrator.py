from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentResponse

MINIMUM_HISTORY = 3
SYSTEMATIC_CALIBRATION_THRESHOLD = 0.20
GOOD_CALIBRATION_THRESHOLD = 0.10


@dataclass(frozen=True)
class AttemptCalibration:
    attempt_id: int
    self_confidence: float
    actual_performance: float
    calibration_error: float


@dataclass(frozen=True)
class CalibrationSummary:
    attempt_count: int
    mean_calibration_error: float | None
    status: str
    reflection_needed: bool
    insufficient_data: bool


def validate_self_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("self_confidence must be numeric")
    confidence = float(value)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("self_confidence must be between 0.0 and 1.0")
    return confidence


def actual_performance(db: Session, attempt: AssessmentAttempt) -> float | None:
    """Use stored score, or derive performance from persisted response correctness."""
    if attempt.score is not None:
        if not 0.0 <= attempt.score <= 1.0:
            raise ValueError("Assessment score must be between 0.0 and 1.0")
        return float(attempt.score)

    responses = db.execute(
        select(AssessmentResponse.is_correct).where(AssessmentResponse.attempt_id == attempt.id)
    ).scalars().all()
    if not responses:
        return None
    return sum(bool(correct) for correct in responses) / len(responses)


def calibrate_attempt(db: Session, attempt: AssessmentAttempt) -> AttemptCalibration | None:
    if attempt.self_confidence is None:
        return None
    confidence = validate_self_confidence(attempt.self_confidence)
    performance = actual_performance(db, attempt)
    if performance is None:
        return None
    return AttemptCalibration(
        attempt_id=attempt.id,
        self_confidence=confidence,
        actual_performance=performance,
        calibration_error=round(confidence - performance, 4),
    )


def calibration_history(
    db: Session,
    user_id: int,
    competency_id: int | None = None,
    *,
    limit: int | None = None,
) -> tuple[AttemptCalibration, ...]:
    if limit is not None and limit <= 0:
        raise ValueError("Calibration history limit must be positive")
    statement = select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.self_confidence.is_not(None),
    )
    if competency_id is not None:
        statement = statement.where(AssessmentAttempt.competency_id == competency_id)
    ordered = statement.order_by(AssessmentAttempt.created_at.desc())
    if limit is not None:
        ordered = ordered.limit(limit)
    attempts = list(reversed(db.execute(ordered).scalars().all()))
    return tuple(
        calibration
        for attempt in attempts
        if (calibration := calibrate_attempt(db, attempt)) is not None
    )


def summarize_calibration(
    history: tuple[AttemptCalibration, ...],
    *,
    minimum_history: int = MINIMUM_HISTORY,
) -> CalibrationSummary:
    if len(history) < minimum_history:
        return CalibrationSummary(
            attempt_count=len(history),
            mean_calibration_error=None,
            status="INSUFFICIENT_DATA",
            reflection_needed=False,
            insufficient_data=True,
        )

    mean_error = round(sum(item.calibration_error for item in history) / len(history), 4)
    if mean_error >= SYSTEMATIC_CALIBRATION_THRESHOLD:
        status = "SYSTEMATIC_OVERCONFIDENCE"
        reflection_needed = True
    elif mean_error <= -SYSTEMATIC_CALIBRATION_THRESHOLD:
        status = "SYSTEMATIC_UNDERCONFIDENCE"
        reflection_needed = True
    elif abs(mean_error) <= GOOD_CALIBRATION_THRESHOLD:
        status = "WELL_CALIBRATED"
        reflection_needed = False
    else:
        status = "MILD_MISCALIBRATION"
        reflection_needed = False

    return CalibrationSummary(
        attempt_count=len(history),
        mean_calibration_error=mean_error,
        status=status,
        reflection_needed=reflection_needed,
        insufficient_data=False,
    )


def summarize_user_calibration(
    db: Session,
    user_id: int,
    competency_id: int | None = None,
    *,
    minimum_history: int = MINIMUM_HISTORY,
    history_limit: int | None = None,
) -> CalibrationSummary:
    return summarize_calibration(
        calibration_history(db, user_id, competency_id, limit=history_limit),
        minimum_history=minimum_history,
    )