from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role, SubSkill
from app.models.user import User
from app.services.signal_collector import (
    aggregate_attempt_signals,
    collect_question_signal,
    persist_attempt_aggregate,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

    role = Role(name="Signal Role")
    session.add(role)
    session.flush()
    user = User(email="signals@example.com", full_name="Signal Learner", password_hash="hashed", role_id=role.id)
    competency = Competency(name="Signal Competency", role_id=role.id)
    session.add_all([user, competency])
    session.flush()
    subskill = SubSkill(name="Signal Subskill", competency_id=competency.id)
    session.add(subskill)
    session.flush()
    item = AssessmentItem(
        competency_id=competency.id,
        subskill_id=subskill.id,
        question_text="Question",
        options_json='["A. One", "B. Two"]',
        correct_option="A",
    )
    session.add(item)
    session.flush()
    attempt = AssessmentAttempt(user_id=user.id, competency_id=competency.id)
    session.add(attempt)
    session.flush()
    response = AssessmentResponse(
        attempt_id=attempt.id,
        assessment_item_id=item.id,
        competency_id=competency.id,
        subskill_id=subskill.id,
        selected_option="A",
        is_correct=True,
    )
    session.add(response)
    session.commit()
    yield session, attempt, response
    session.close()
    engine.dispose()


def test_valid_signal_persistence_and_relationship(db):
    session, attempt, response = db
    record = collect_question_signal(
        session,
        attempt.id,
        {"response_time": 4.5, "retries": 1, "hints_requested": 2, "skips": 0, "repeated_errors": 1},
        assessment_response_id=response.id,
    )
    session.commit()
    assert record.id is not None
    assert record.attempt_id == attempt.id
    assert record.assessment_response_id == response.id
    assert record.response_time == 4.5
    assert record.repeated_errors == 1


def test_aggregation_preserves_missing_values_and_sums_repeated_errors(db):
    session, attempt, _ = db
    collect_question_signal(session, attempt.id, {"response_time": 2.0, "retries": 1, "repeated_errors": 1})
    collect_question_signal(session, attempt.id, {"response_time": 3.5, "retries": 2, "hints_requested": 1, "repeated_errors": 2})
    aggregate = aggregate_attempt_signals(session, attempt.id)
    assert aggregate.available is True
    assert aggregate.signal_count == 2
    assert aggregate.response_time == 5.5
    assert aggregate.retries == 3
    assert aggregate.hints_requested == 1
    assert aggregate.skips is None
    assert aggregate.repeated_errors == 3


def test_zero_values_are_retained(db):
    session, attempt, _ = db
    collect_question_signal(session, attempt.id, {"response_time": 0, "retries": 0, "hints_requested": 0, "skips": 0, "repeated_errors": 0})
    aggregate = aggregate_attempt_signals(session, attempt.id)
    assert aggregate.response_time == 0
    assert aggregate.retries == 0
    assert aggregate.hints_requested == 0
    assert aggregate.skips == 0
    assert aggregate.repeated_errors == 0


def test_missing_signals_return_empty_result(db):
    session, attempt, _ = db
    aggregate = aggregate_attempt_signals(session, attempt.id)
    assert aggregate.available is False
    assert aggregate.signal_count == 0
    assert aggregate.response_time is None
    assert persist_attempt_aggregate(session, attempt.id) is None


def test_explicit_session_duration_is_persisted_without_inference(db):
    session, attempt, _ = db
    collect_question_signal(session, attempt.id, {"response_time": 2.0})
    aggregate = persist_attempt_aggregate(session, attempt.id, session_duration=30.0)
    assert aggregate is not None
    assert aggregate.session_duration == 30.0
    assert aggregate.response_time == 2.0


@pytest.mark.parametrize("field", ["response_time", "retries", "hints_requested", "skips", "repeated_errors"])
def test_negative_values_are_rejected(db, field):
    session, attempt, _ = db
    with pytest.raises(ValueError, match="non-negative"):
        collect_question_signal(session, attempt.id, {field: -1})


def test_malformed_values_are_rejected(db):
    session, attempt, _ = db
    with pytest.raises(ValueError, match="numeric"):
        collect_question_signal(session, attempt.id, {"retries": "twice"})
    with pytest.raises(ValueError, match="Unknown signal fields"):
        collect_question_signal(session, attempt.id, {"unknown": 1})


def test_duplicate_response_for_attempt_is_rejected(db):
    session, attempt, response = db
    session.add(
        AssessmentResponse(
            attempt_id=attempt.id,
            assessment_item_id=response.assessment_item_id,
            competency_id=response.competency_id,
            subskill_id=response.subskill_id,
            selected_option="B",
            is_correct=False,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()