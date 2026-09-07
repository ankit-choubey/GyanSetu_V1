from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentResponse
from app.models.assessment_signal import AssessmentSignal


@dataclass(frozen=True)
class QuestionSignalInput:
    response_time: float | None = None
    retries: int | None = None
    hints_requested: int | None = None
    skips: int | None = None
    repeated_errors: int | None = None

    def __post_init__(self) -> None:
        for name in ("response_time", "retries", "hints_requested", "skips", "repeated_errors"):
            value = getattr(self, name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"{name} must be numeric")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
            if name != "response_time" and int(value) != value:
                raise ValueError(f"{name} must be a whole number")

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "QuestionSignalInput":
        allowed = {"response_time", "retries", "hints_requested", "skips", "repeated_errors"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Unknown signal fields: {sorted(unknown)}")
        return cls(**{field: values.get(field) for field in allowed if field in values})


@dataclass(frozen=True)
class SignalAggregate:
    attempt_id: int
    signal_count: int
    available: bool
    response_time: float | None = None
    retries: int | None = None
    hints_requested: int | None = None
    skips: int | None = None
    repeated_errors: int | None = None
    session_duration: float | None = None


def _coerce_signal(signal: QuestionSignalInput | Mapping[str, object]) -> QuestionSignalInput:
    if isinstance(signal, QuestionSignalInput):
        return signal
    if isinstance(signal, Mapping):
        return QuestionSignalInput.from_mapping(signal)
    raise ValueError("Signal must be QuestionSignalInput or a mapping")


def collect_question_signal(
    db: Session,
    attempt_id: int,
    signal: QuestionSignalInput | Mapping[str, object],
    *,
    assessment_response_id: int | None = None,
) -> AssessmentSignal:
    """Persist one validated question-level signal without committing the session."""
    normalized = _coerce_signal(signal)
    attempt = db.get(AssessmentAttempt, attempt_id)
    if attempt is None:
        raise ValueError(f"Assessment attempt {attempt_id} does not exist")

    if assessment_response_id is not None:
        response = db.get(AssessmentResponse, assessment_response_id)
        if response is None or response.attempt_id != attempt_id:
            raise ValueError("Assessment response does not belong to the assessment attempt")

    record = AssessmentSignal(
        attempt_id=attempt_id,
        assessment_response_id=assessment_response_id,
        response_time=normalized.response_time,
        retries=normalized.retries,
        hints_requested=normalized.hints_requested,
        skips=normalized.skips,
        repeated_errors=normalized.repeated_errors,
    )
    db.add(record)
    db.flush()
    return record


def aggregate_attempt_signals(db: Session, attempt_id: int) -> SignalAggregate:
    """Return deterministic sums for available question-level signals."""
    records = db.execute(
        select(AssessmentSignal).where(
            AssessmentSignal.attempt_id == attempt_id,
            AssessmentSignal.is_session_aggregate.is_(False),
        )
    ).scalars().all()
    if not records:
        return SignalAggregate(attempt_id=attempt_id, signal_count=0, available=False)

    def total(field: str) -> float | int | None:
        values = [getattr(record, field) for record in records if getattr(record, field) is not None]
        return sum(values) if values else None

    return SignalAggregate(
        attempt_id=attempt_id,
        signal_count=len(records),
        available=True,
        response_time=total("response_time"),
        retries=total("retries"),
        hints_requested=total("hints_requested"),
        skips=total("skips"),
        repeated_errors=total("repeated_errors"),
    )


def persist_attempt_aggregate(
    db: Session,
    attempt_id: int,
    *,
    session_duration: float | None = None,
    learning_state_provider: Any | None = None,
) -> AssessmentSignal | None:
    """Persist the current aggregate, or leave storage unchanged when no signal exists."""
    if session_duration is not None:
        QuestionSignalInput(response_time=session_duration)
    aggregate = aggregate_attempt_signals(db, attempt_id)
    if not aggregate.available:
        return None

    if learning_state_provider is not None:
        # Pre-classify learning state for telemetry/downstream consumers
        learning_state_provider.classify_state({
            "response_time": aggregate.response_time or 20.0,
            "hints_requested": aggregate.hints_requested or 0,
        })

    existing = db.execute(
        select(AssessmentSignal).where(
            AssessmentSignal.attempt_id == attempt_id,
            AssessmentSignal.is_session_aggregate.is_(True),
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = AssessmentSignal(attempt_id=attempt_id, is_session_aggregate=True)
        db.add(existing)

    existing.response_time = aggregate.response_time
    existing.retries = aggregate.retries
    existing.hints_requested = aggregate.hints_requested
    existing.skips = aggregate.skips
    existing.repeated_errors = aggregate.repeated_errors
    existing.session_duration = session_duration
    db.flush()
    return existing