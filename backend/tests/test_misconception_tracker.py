from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.misconception import Misconception
from app.models.user import User
from app.services.misconception_tracker import (
    ClassifierResult,
    UNCLASSIFIED_TYPE,
    build_pattern_key,
    resolve_misconception,
    track_response,
)


class FakeClassifier:
    def classify(self, response):
        return ClassifierResult(
            misconception_type="TEST_SEMANTIC_LABEL",
            description="Test classifier description",
        )


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    role = Role(name="Misconception Role")
    session.add(role)
    session.flush()
    user_one = User(email="mis-one@example.com", full_name="One", password_hash="hashed", role_id=role.id)
    user_two = User(email="mis-two@example.com", full_name="Two", password_hash="hashed", role_id=role.id)
    competency_one = Competency(name="Misconception Competency One", role_id=role.id)
    competency_two = Competency(name="Misconception Competency Two", role_id=role.id)
    session.add_all([user_one, user_two, competency_one, competency_two])
    session.flush()
    subskill_one = SubSkill(name="Subskill One", competency_id=competency_one.id)
    subskill_two = SubSkill(name="Subskill Two", competency_id=competency_one.id)
    session.add_all([subskill_one, subskill_two])
    session.flush()
    item_one = AssessmentItem(
        competency_id=competency_one.id,
        subskill_id=subskill_one.id,
        question_text="Question one",
        options_json='["A. One", "B. Two", "C. Three", "D. Four"]',
        correct_option="A",
    )
    item_two = AssessmentItem(
        competency_id=competency_one.id,
        subskill_id=subskill_one.id,
        question_text="Question two",
        options_json='["A. One", "B. Two", "C. Three", "D. Four"]',
        correct_option="A",
    )
    item_three = AssessmentItem(
        competency_id=competency_one.id,
        subskill_id=subskill_two.id,
        question_text="Question three",
        options_json='["A. One", "B. Two", "C. Three", "D. Four"]',
        correct_option="A",
    )
    item_four = AssessmentItem(
        competency_id=competency_two.id,
        question_text="Question four",
        options_json='["A. One", "B. Two", "C. Three", "D. Four"]',
        correct_option="A",
    )
    session.add_all([item_one, item_two, item_three, item_four])
    session.flush()
    attempt = AssessmentAttempt(user_id=user_one.id, competency_id=competency_one.id)
    session.add(attempt)
    session.flush()
    yield session, user_one, user_two, competency_one, competency_two, subskill_one, subskill_two, item_one, item_two, item_three, item_four, attempt
    session.close()
    engine.dispose()


def response(attempt, item, *, selected="B", competency_id=None, subskill_id=None, correct=False):
    return AssessmentResponse(
        attempt_id=attempt.id,
        assessment_item_id=item.id,
        competency_id=competency_id or item.competency_id,
        subskill_id=subskill_id if subskill_id is not None else item.subskill_id,
        selected_option=selected,
        is_correct=correct,
    )


def test_pattern_key_is_canonical():
    assert build_pattern_key(7, " b ") == "assessment_item:7|selected_option:B"


def test_first_wrong_pattern_is_unresolved_and_unclassified(db):
    session, _, _, _, _, _, _, item_one, _, _, _, attempt = db
    item_response = response(attempt, item_one)
    session.add(item_response)
    session.flush()
    tracked = track_response(session, item_response, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert tracked.classifier_status == "UNAVAILABLE"
    assert tracked.misconception.pattern_key == "assessment_item:%s|selected_option:B" % item_one.id
    assert tracked.misconception.occurrences == 1
    assert tracked.misconception.resolved is False
    assert tracked.misconception.misconception_type == UNCLASSIFIED_TYPE


def test_matching_pattern_increments_and_preserves_first_timestamp(db):
    session, user_one, _, competency_one, _, _, _, item_one, _, _, _, attempt = db
    first = response(attempt, item_one)
    second_attempt = AssessmentAttempt(user_id=user_one.id, competency_id=competency_one.id)
    session.add(second_attempt)
    session.flush()
    second = response(second_attempt, item_one)
    session.add_all([first, second])
    session.flush()
    first_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second_time = datetime(2026, 1, 2, tzinfo=timezone.utc)
    track_response(session, first, now=first_time)
    tracked = track_response(session, second, now=second_time)
    assert tracked.misconception.occurrences == 2
    assert tracked.misconception.first_observed.replace(tzinfo=timezone.utc) == first_time
    assert tracked.misconception.last_observed.replace(tzinfo=timezone.utc) == second_time


@pytest.mark.parametrize("variation", ["different_option", "different_item", "different_learner", "different_competency", "different_subskill"])
def test_scope_or_pattern_variations_create_separate_records(db, variation):
    session, user_one, user_two, competency_one, competency_two, subskill_one, subskill_two, item_one, item_two, item_three, item_four, attempt = db
    first = response(attempt, item_one)
    session.add(first)
    session.flush()
    track_response(session, first)
    if variation == "different_option":
        other_attempt = AssessmentAttempt(user_id=user_one.id, competency_id=competency_one.id)
        session.add(other_attempt)
        session.flush()
        second = response(other_attempt, item_one, selected="C")
    elif variation == "different_item":
        second = response(attempt, item_two)
    elif variation == "different_learner":
        other_attempt = AssessmentAttempt(user_id=user_two.id, competency_id=competency_one.id)
        session.add(other_attempt)
        session.flush()
        second = response(other_attempt, item_one)
    elif variation == "different_competency":
        other_attempt = AssessmentAttempt(user_id=user_one.id, competency_id=competency_two.id)
        session.add(other_attempt)
        session.flush()
        second = response(other_attempt, item_four, competency_id=competency_two.id)
    else:
        second = response(attempt, item_three, subskill_id=subskill_two.id)
    session.add(second)
    session.flush()
    track_response(session, second)
    assert session.scalar(select(func.count()).select_from(Misconception)) == 2


def test_correct_answer_creates_no_record(db):
    session, _, _, _, _, _, _, item_one, _, _, _, attempt = db
    correct = response(attempt, item_one, selected="A", correct=True)
    session.add(correct)
    session.flush()
    tracked = track_response(session, correct)
    assert tracked.misconception is None
    assert session.scalar(select(func.count()).select_from(Misconception)) == 0


def test_explicit_resolution_supports_evidence_and_intervention(db):
    session, user_one, _, competency_one, _, _, _, item_one, _, _, _, attempt = db
    wrong = response(attempt, item_one)
    session.add(wrong)
    session.flush()
    tracked = track_response(session, wrong)
    evidence = Evidence(
        user_id=user_one.id,
        competency_id=competency_one.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Resolution evidence",
        score=1.0,
    )
    session.add(evidence)
    session.flush()
    resolved = resolve_misconception(
        session,
        tracked.misconception.id,
        resolution_evidence_id=evidence.id,
        intervention_applied=True,
    )
    assert resolved.resolved is True
    assert resolved.resolution_evidence_id == evidence.id
    assert resolved.intervention_applied is True


def test_classifier_boundary_enriches_semantics_without_changing_pattern_key(db):
    session, _, _, _, _, _, _, item_one, _, _, _, attempt = db
    wrong = response(attempt, item_one, selected="C")
    session.add(wrong)
    session.flush()
    tracked = track_response(session, wrong, classifier=FakeClassifier())
    assert tracked.classifier_status == "AVAILABLE"
    assert tracked.misconception.misconception_type == "TEST_SEMANTIC_LABEL"
    assert tracked.misconception.description == "Test classifier description"
    assert tracked.misconception.pattern_key == f"assessment_item:{item_one.id}|selected_option:C"