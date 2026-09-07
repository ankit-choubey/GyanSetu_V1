from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, SubSkill
from app.models.user import User
from app.services.adaptive_question_selector import (
    DatabaseAdaptiveQuestionSelector,
    NoEligibleDiagnosticQuestionError,
)
from app.services.ml_interfaces import QuestionSelectionRequest
from ml_pipeline import adaptive_selector


@pytest.fixture
def db_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as db:
        competency = Competency(name="Data Quality")
        other_competency = Competency(name="Sampling Design")
        db.add_all([competency, other_competency])
        db.flush()
        validation = SubSkill(competency_id=competency.id, name="Validation")
        other_subskill = SubSkill(competency_id=other_competency.id, name="Sampling frames")
        user = User(email="selector@example.com", full_name="Selector User", password_hash="hashed")
        other_user = User(email="other@example.com", full_name="Other User", password_hash="hashed")
        db.add_all([validation, other_subskill, user, other_user])
        db.flush()
        db.add_all(
            [
                _item(competency.id, validation.id, "Easy validation", "easy", "q-easy"),
                _item(competency.id, validation.id, "Medium validation", "medium", "q-medium"),
                _item(competency.id, validation.id, "Hard validation", "hard", "q-hard"),
                _item(other_competency.id, other_subskill.id, "Other competency", "easy", "q-other"),
            ]
        )
        db.commit()
        yield db, competency, validation, user, other_user
    engine.dispose()


def _item(competency_id, subskill_id, text, difficulty, source_reference):
    return AssessmentItem(
        user_id=None,
        competency_id=competency_id,
        subskill_id=subskill_id,
        question_text=text,
        options_json=json.dumps(["A. One", "B. Two", "C. Three", "D. Four"]),
        correct_option="A. One",
        difficulty=difficulty,
        source_reference=source_reference,
    )


def _request(competency_id, subskill_id=None, subskill_name=None):
    return QuestionSelectionRequest(
        competency_id=competency_id,
        subskill_id=subskill_id,
        subskill_name=subskill_name,
        evidence_count=1,
        evidence_diversity=1,
        competency_status="developing",
        gap_reason="low_mastery",
        constraints=("use validated items",),
    )


def test_maps_database_items_and_converts_selected_item(db_context, monkeypatch):
    db, competency, validation, user, _ = db_context
    selector_result = Mock(
        return_value={
            "next_question": {"question_id": 2},
            "target_difficulty": "medium",
            "target_subskill": None,
            "is_complete": False,
        }
    )
    monkeypatch.setattr(adaptive_selector, "select_next_question", selector_result)

    result = DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(
        _request(competency.id, validation.id, validation.name)
    )

    assert result.question_id == 2
    assert result.competency_id == competency.id
    assert result.subskill_id == validation.id
    assert result.question_text == "Medium validation"
    assert result.options == ("A. One", "B. Two", "C. Three", "D. Four")
    assert result.correct_option == "A. One"
    selector_result.assert_called_once()
    item_bank, history = selector_result.call_args.kwargs["item_bank"], selector_result.call_args.kwargs["session_history"]
    assert {item["question_id"] for item in item_bank} == {1, 2, 3}
    assert all(item["competency"] == "Data Quality" for item in item_bank)
    mapped = next(item for item in item_bank if item["question_id"] == 2)
    assert mapped == {
        "question_id": 2,
        "question": "Medium validation",
        "options": ["A. One", "B. Two", "C. Three", "D. Four"],
        "correct_option": "A. One",
        "difficulty": "medium",
        "competency": "Data Quality",
        "subskill": "Validation",
        "source_reference": "q-medium",
    }
    assert history == []


def test_competency_filtering_excludes_other_competencies(db_context, monkeypatch):
    db, competency, validation, user, _ = db_context
    selector_result = Mock(return_value={"next_question": {"question_id": 1}, "is_complete": False})
    monkeypatch.setattr(adaptive_selector, "select_next_question", selector_result)

    DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(
        _request(competency.id, validation.id, None)
    )

    bank = selector_result.call_args.kwargs["item_bank"]
    assert {item["question_id"] for item in bank} == {1, 2, 3}


def test_session_history_is_scoped_and_converted(db_context, monkeypatch):
    db, competency, validation, user, other_user = db_context
    items = db.query(AssessmentItem).filter(AssessmentItem.competency_id == competency.id).all()
    own_attempt = AssessmentAttempt(user_id=user.id, competency_id=competency.id)
    other_attempt = AssessmentAttempt(user_id=other_user.id, competency_id=competency.id)
    db.add_all([own_attempt, other_attempt])
    db.flush()
    db.add_all(
        [
            AssessmentResponse(
                attempt_id=own_attempt.id,
                assessment_item_id=items[0].id,
                competency_id=competency.id,
                subskill_id=validation.id,
                selected_option="A. One",
                is_correct=True,
                answered_at=datetime.now(timezone.utc),
            ),
            AssessmentResponse(
                attempt_id=other_attempt.id,
                assessment_item_id=items[1].id,
                competency_id=competency.id,
                subskill_id=validation.id,
                selected_option="B. Two",
                is_correct=False,
                answered_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db.commit()
    selector_result = Mock(return_value={"next_question": {"question_id": 3}, "is_complete": False})
    monkeypatch.setattr(adaptive_selector, "select_next_question", selector_result)

    DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(_request(competency.id))

    history = selector_result.call_args.kwargs["session_history"]
    assert len(history) == 1
    assert history[0]["question_id"] == items[0].id
    assert history[0]["is_correct"] is True


def test_anti_repetition_and_correct_answer_escalation_are_delegated(db_context):
    db, competency, validation, user, _ = db_context
    items = db.query(AssessmentItem).filter(AssessmentItem.competency_id == competency.id).order_by(AssessmentItem.id).all()
    attempt = AssessmentAttempt(user_id=user.id, competency_id=competency.id)
    db.add(attempt)
    db.flush()
    db.add(
        AssessmentResponse(
            attempt_id=attempt.id,
            assessment_item_id=items[0].id,
            competency_id=competency.id,
            subskill_id=validation.id,
            selected_option="A. One",
            is_correct=True,
        )
    )
    db.commit()
    selector = DatabaseAdaptiveQuestionSelector(db, user.id)
    result = selector.select_next_question(_request(competency.id))
    assert result.question_id == items[1].id


def test_incorrect_answer_targets_weak_subskill(db_context):
    db, competency, validation, user, _ = db_context
    items = db.query(AssessmentItem).filter(AssessmentItem.competency_id == competency.id).order_by(AssessmentItem.id).all()
    attempt = AssessmentAttempt(user_id=user.id, competency_id=competency.id)
    db.add(attempt)
    db.flush()
    db.add(
        AssessmentResponse(
            attempt_id=attempt.id,
            assessment_item_id=items[1].id,
            competency_id=competency.id,
            subskill_id=validation.id,
            selected_option="B. Two",
            is_correct=False,
        )
    )
    db.commit()
    result = DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(
        _request(competency.id)
    )
    assert result.question_id == items[0].id


def test_malformed_options_json_is_rejected(db_context):
    db, competency, validation, user, _ = db_context
    item = db.query(AssessmentItem).filter(AssessmentItem.id == 1).one()
    item.options_json = "not-json"
    db.add(item)
    db.commit()
    with pytest.raises(ValueError, match="options are malformed"):
        DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(_request(competency.id))


@pytest.mark.parametrize(
    "result, message",
    [
        ({"next_question": {"question_id": 999}, "is_complete": False}, "unknown question"),
        ({"next_question": {"question_id": "not-an-id"}, "is_complete": False}, "unknown question"),
        ([], "response must be an object"),
    ],
)
def test_malformed_or_unsupported_ml_output_is_rejected(db_context, monkeypatch, result, message):
    db, competency, validation, user, _ = db_context
    monkeypatch.setattr(adaptive_selector, "select_next_question", Mock(return_value=result))
    with pytest.raises(ValueError, match=message):
        DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(
            _request(competency.id, validation.id, validation.name)
        )


def test_empty_question_bank_raises_controlled_completion_error(db_context, monkeypatch):
    db, competency, _, user, _ = db_context
    db.query(AssessmentItem).delete()
    db.commit()
    monkeypatch.setattr(
        adaptive_selector,
        "select_next_question",
        Mock(return_value={"next_question": None, "is_complete": True}),
    )
    with pytest.raises(NoEligibleDiagnosticQuestionError, match="No eligible diagnostic question"):
        DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(_request(competency.id))


def test_exhausted_question_bank_raises_controlled_completion_error(db_context, monkeypatch):
    db, competency, _, user, _ = db_context
    monkeypatch.setattr(
        adaptive_selector,
        "select_next_question",
        Mock(return_value={"next_question": None, "is_complete": True}),
    )
    with pytest.raises(NoEligibleDiagnosticQuestionError, match="No eligible diagnostic question"):
        DatabaseAdaptiveQuestionSelector(db, user.id).select_next_question(_request(competency.id))