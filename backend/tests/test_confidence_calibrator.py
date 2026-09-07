from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.services.confidence_calibrator import (
    actual_performance,
    calibrate_attempt,
    calibration_history,
    summarize_calibration,
    summarize_user_calibration,
    validate_self_confidence,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    role = Role(name="Calibration Role")
    session.add(role)
    session.flush()
    user = User(email="calibration@example.com", full_name="Calibration Learner", password_hash="hashed", role_id=role.id)
    competency = Competency(name="Calibration Competency", role_id=role.id)
    session.add_all([user, competency])
    session.flush()
    yield session, user, competency
    session.close()
    engine.dispose()


def add_attempt(session, user, competency, confidence, score=None, correct_values=()):
    attempt = AssessmentAttempt(
        user_id=user.id,
        competency_id=competency.id,
        self_confidence=confidence,
        score=score,
    )
    session.add(attempt)
    session.flush()
    for correct in correct_values:
        item = AssessmentItem(
            competency_id=competency.id,
            question_text="Calibration question",
            options_json='["A. One", "B. Two"]',
            correct_option="A",
        )
        session.add(item)
        session.flush()
        session.add(
            AssessmentResponse(
                attempt_id=attempt.id,
                assessment_item_id=item.id,
                competency_id=competency.id,
                selected_option="A",
                is_correct=correct,
            )
        )
    session.flush()
    return attempt


def test_confidence_boundaries_and_middle_value_are_valid():
    assert validate_self_confidence(0.0) == 0.0
    assert validate_self_confidence(1.0) == 1.0
    assert validate_self_confidence(0.65) == 0.65


@pytest.mark.parametrize("value", [-0.01, 1.01, "high", True])
def test_invalid_confidence_is_rejected(value):
    with pytest.raises(ValueError):
        validate_self_confidence(value)


def test_actual_performance_and_calibration_error_use_stored_score(db):
    session, user, competency = db
    attempt = add_attempt(session, user, competency, 0.8, score=0.5)
    calibration = calibrate_attempt(session, attempt)
    assert actual_performance(session, attempt) == 0.5
    assert calibration.actual_performance == 0.5
    assert calibration.calibration_error == 0.3


def test_actual_performance_can_derive_from_response_correctness(db):
    session, user, competency = db
    attempt = add_attempt(session, user, competency, 0.5, correct_values=(True, False, True))
    assert actual_performance(session, attempt) == pytest.approx(2 / 3)


def test_overconfidence_underconfidence_and_good_calibration():
    over = summarize_calibration(tuple(type("C", (), {"calibration_error": 0.3})() for _ in range(3)))
    under = summarize_calibration(tuple(type("C", (), {"calibration_error": -0.3})() for _ in range(3)))
    good = summarize_calibration(tuple(type("C", (), {"calibration_error": 0.05})() for _ in range(3)))
    assert over.status == "SYSTEMATIC_OVERCONFIDENCE"
    assert over.reflection_needed is True
    assert under.status == "SYSTEMATIC_UNDERCONFIDENCE"
    assert under.reflection_needed is True
    assert good.status == "WELL_CALIBRATED"
    assert good.reflection_needed is False


def test_insufficient_history_does_not_trigger_reflection():
    summary = summarize_calibration(tuple(type("C", (), {"calibration_error": 0.9})() for _ in range(2)))
    assert summary.insufficient_data is True
    assert summary.status == "INSUFFICIENT_DATA"
    assert summary.reflection_needed is False


def test_history_summary_and_self_confidence_are_separate_from_system_confidence(db):
    session, user, competency = db
    for _ in range(3):
        add_attempt(session, user, competency, 0.9, score=0.5)
    session.add(CompetencyState(user_id=user.id, competency_id=competency.id, confidence=0.2))
    session.commit()
    history = calibration_history(session, user.id, competency.id)
    summary = summarize_user_calibration(session, user.id, competency.id)
    state = session.query(CompetencyState).one()
    assert len(history) == 3
    assert summary.reflection_needed is True
    assert history[0].self_confidence == 0.9
    assert state.confidence == 0.2


def test_history_supports_latest_n_rolling_window(db):
    session, user, competency = db
    for confidence, score in ((0.5, 0.5), (0.9, 0.5), (0.8, 0.5), (0.7, 0.5)):
        add_attempt(session, user, competency, confidence, score=score)
    history = calibration_history(session, user.id, competency.id, limit=2)
    assert len(history) == 2
    assert [item.self_confidence for item in history] == [0.8, 0.7]


def test_database_rejects_out_of_range_self_confidence(db):
    session, user, competency = db
    session.add(AssessmentAttempt(user_id=user.id, competency_id=competency.id, self_confidence=1.5))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()