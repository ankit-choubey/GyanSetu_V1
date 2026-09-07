from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.models.competency import Competency, CompetencyDomain, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.adapters.provider_adapters import (
    IGOTAdapter,
    InternalAdapter,
    NSSTAAdapter,
    VirtualLabAdapter,
    get_adapter_for_provider,
)
from app.services.eligibility_engine import EligibilityEngine
from app.services.intervention_lifecycle_service import InterventionLifecycleService
from app.services.next_best_action_service import NextBestActionService
from app.services.recommendation_ranker import RecommendationRanker


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()

    # Seed baseline role, competency, subskills
    role = Role(name="Statistical Officer", description="Role")
    db.add(role)
    db.flush()

    comp = Competency(
        role_id=role.id,
        name="Sampling Design",
        domain=CompetencyDomain.STATISTICAL,
        description="Sampling competency",
    )
    db.add(comp)
    db.flush()

    sub1 = SubSkill(competency_id=comp.id, name="Stratified sampling")
    sub2 = SubSkill(competency_id=comp.id, name="Probability sampling")
    db.add_all([sub1, sub2])
    db.flush()

    user = User(
        email="test.learner@mospi.gov.in",
        full_name="Test Learner",
        password_hash="pw",
        role_id=role.id,
    )
    db.add(user)
    db.commit()

    yield db
    db.close()


def test_provider_adapters():
    igot = get_adapter_for_provider("iGOT")
    assert igot.get_provider_name() == "iGOT"
    assert igot.get_integration_mode() == "REPLAY"

    nssta = get_adapter_for_provider("NSSTA")
    assert nssta.get_provider_name() == "NSSTA"
    assert nssta.get_integration_mode() == "REPLAY"

    vlab = get_adapter_for_provider("VIRTUAL_LAB")
    assert vlab.get_provider_name() == "VIRTUAL_LAB"
    assert vlab.get_integration_mode() == "SANDBOX"

    internal = get_adapter_for_provider("INTERNAL")
    assert internal.get_provider_name() == "INTERNAL"
    assert internal.get_integration_mode() == "LIVE"


def test_eligibility_engine_filtering(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()
    sub = test_db.query(SubSkill).first()

    engine = EligibilityEngine()

    active_item = Intervention(
        title="Active Practice",
        competency_id=comp.id,
        subskill_id=sub.id,
        intervention_type="targeted_practice",
        provider="INTERNAL",
        status="ACTIVE",
    )
    test_db.add(active_item)

    inactive_item = Intervention(
        title="Inactive Course",
        competency_id=comp.id,
        subskill_id=sub.id,
        intervention_type="video_lesson",
        provider="INTERNAL",
        status="INACTIVE",
    )
    test_db.add(inactive_item)

    stale_item = Intervention(
        title="Stale Document",
        competency_id=comp.id,
        subskill_id=sub.id,
        intervention_type="targeted_practice",
        provider="INTERNAL",
        status="STALE",
    )
    test_db.add(stale_item)

    unavail_item = Intervention(
        title="Under Maintenance Lab",
        competency_id=comp.id,
        subskill_id=sub.id,
        intervention_type="virtual_lab",
        provider="VIRTUAL_LAB",
        status="UNAVAILABLE",
    )
    test_db.add(unavail_item)
    test_db.commit()

    candidates = [active_item, inactive_item, stale_item, unavail_item]
    eligible, decisions = engine.filter_candidates(test_db, user, candidates)

    assert len(eligible) == 1
    assert eligible[0].id == active_item.id

    dec_map = {d.intervention_id: d.status for d in decisions}
    assert dec_map[active_item.id] == "ELIGIBLE"
    assert dec_map[inactive_item.id] == "INELIGIBLE"
    assert dec_map[stale_item.id] == "STALE"
    assert dec_map[unavail_item.id] == "UNAVAILABLE"


def test_eligibility_engine_prerequisite_blocking(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()

    prereq_json = json.dumps({"required_subskills": ["Sample size determination"], "min_mastery": 0.80})
    advanced_item = Intervention(
        title="Advanced Optimal Sample Allocation",
        competency_id=comp.id,
        intervention_type="scenario_practice",
        provider="INTERNAL",
        status="ACTIVE",
        prerequisites_json=prereq_json,
    )
    test_db.add(advanced_item)
    test_db.commit()

    engine = EligibilityEngine()
    decision = engine.evaluate_candidate(test_db, user, advanced_item)

    assert not decision.is_eligible
    assert decision.status == "INELIGIBLE"
    assert "Prerequisite not met" in str(decision.reason)


def test_recommendation_ranker_explanation():
    ranker = RecommendationRanker()

    item1 = Intervention(
        id=1,
        title="Item 1 Subskill Match",
        competency_id=1,
        subskill_id=10,
        intervention_type="scenario_practice",
        provider="INTERNAL",
        modality="PRACTICE_SCENARIO",
        status="ACTIVE",
        priority=1,
    )
    item2 = Intervention(
        id=2,
        title="Item 2 General",
        competency_id=1,
        subskill_id=11,
        intervention_type="video_lesson",
        provider="iGOT",
        modality="ONLINE_SELF_PACED",
        status="ACTIVE",
        priority=2,
    )

    result = ranker.rank(
        eligible_candidates=[item1, item2],
        ineligible_decisions=[],
        target_competency_id=1,
        target_subskill_id=10,
        target_subskill_name="Stratified sampling",
        active_misconceptions=None,
        competency_state=None,
    )

    assert result.selected is not None
    assert result.selected.intervention.id == 1
    assert len(result.selected.positive_factors) > 0
    assert any("subskill" in f.lower() for f in result.selected.positive_factors)
    assert len(result.rejected_candidates) > 0
    assert result.rejected_candidates[0]["status"] == "LOWER_RANKED"


def test_next_best_action_cold_start(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()

    # User has 0 evidence records -> unassessed state
    service = NextBestActionService()
    rec = service.get_next_best_action(test_db, learner=user, competency_id=comp.id)

    assert rec.action_type == "DIAGNOSTIC"
    assert rec.status == "RECOMMENDED"
    assert "diagnostic" in rec.objective.lower()
    explanation = json.loads(rec.explanation_json)
    assert "UNASSESSED" in explanation["why"]


def test_intervention_lifecycle_feedback_and_start(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()

    rec = RecommendationRecord(
        recommendation_id="rec_test_001",
        user_id=user.id,
        competency_id=comp.id,
        action_type="INTERVENTION",
        status="RECOMMENDED",
        confidence=0.8,
    )
    test_db.add(rec)
    test_db.commit()

    lifecycle = InterventionLifecycleService()

    # Accept recommendation
    accepted = lifecycle.record_feedback(test_db, user=user, recommendation_id="rec_test_001", action="ACCEPTED")
    assert accepted.status == "ACCEPTED"

    # Start recommendation
    started = lifecycle.start_intervention(test_db, user=user, recommendation_id="rec_test_001")
    assert started.status == "STARTED"


def test_completion_without_evidence_preserves_mastery(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()

    # Initial state with mastery 0.40
    st = CompetencyState(
        user_id=user.id,
        competency_id=comp.id,
        mastery=0.40,
        confidence=0.50,
        status="ASSESSED",
    )
    test_db.add(st)

    item = Intervention(
        title="Passive Video Watching",
        competency_id=comp.id,
        intervention_type="video_lesson",
        provider="iGOT",
        status="ACTIVE",
    )
    test_db.add(item)
    test_db.commit()

    lifecycle = InterventionLifecycleService()

    # Complete WITHOUT post-assessment evidence
    outcome = lifecycle.record_outcome(
        test_db,
        user=user,
        intervention_id=item.id,
        status="COMPLETED",
        completion_score=None,
        has_post_assessment_evidence=False,
    )

    assert outcome.status == "COMPLETED"
    assert outcome.evidence_id is None
    # Crucial rule: mastery remains unchanged!
    assert outcome.post_competency_mastery == 0.40
    assert "competency unchanged" in outcome.notes


def test_outcome_idempotency(test_db: Session):
    user = test_db.query(User).first()
    comp = test_db.query(Competency).first()

    item = Intervention(
        title="Practice Drill",
        competency_id=comp.id,
        intervention_type="targeted_practice",
        provider="INTERNAL",
        status="ACTIVE",
    )
    test_db.add(item)
    test_db.commit()

    lifecycle = InterventionLifecycleService()
    key = "unique-idempotency-key-12345"

    # First submission
    out1 = lifecycle.record_outcome(
        test_db,
        user=user,
        intervention_id=item.id,
        status="COMPLETED",
        idempotency_key=key,
    )

    # Second duplicate submission with same key
    out2 = lifecycle.record_outcome(
        test_db,
        user=user,
        intervention_id=item.id,
        status="COMPLETED",
        idempotency_key=key,
    )

    assert out1.id == out2.id
    total_outcomes = test_db.query(InterventionOutcome).filter_by(idempotency_key=key).count()
    assert total_outcomes == 1
