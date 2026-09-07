"""
Unit tests for backend/app/services/ml_providers.py and their integration
with monitoring_agent and signal_collector.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.monitoring_event import MonitoringEvent
from app.models.user import User
from app.schemas.monitoring import MonitoringEventRequest, MonitoringEventType
from app.services.ml_providers import (
    IRTProvider,
    InterventionProvider,
    LearningStateProvider,
    RetentionProvider,
)
from app.services.monitoring_agent import MonitoringAgent
from app.services.signal_collector import (
    collect_question_signal,
    persist_attempt_aggregate,
)
from app.models.assessment import AssessmentAttempt, AssessmentItem


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        role = Role(name="Statistical Officer", code="SO")
        session.add(role)
        session.commit()
        session.refresh(role)

        learner = User(email="test@example.com", full_name="Test User", password_hash="hash", role_id=role.id)
        session.add(learner)
        session.commit()
        session.refresh(learner)

        comp = Competency(name="Sampling Design", role_id=role.id)
        session.add(comp)
        session.commit()
        session.refresh(comp)

        role_comp = RoleCompetency(role_id=role.id, competency_id=comp.id)
        session.add(role_comp)
        session.commit()

        subskill = SubSkill(competency_id=comp.id, name="Stratification", code="SD-01")
        session.add(subskill)
        session.commit()
        session.refresh(subskill)

        evidence = Evidence(
            user_id=learner.id,
            competency_id=comp.id,
            subskill_id=subskill.id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Test Assessment",
            score=0.75,
            observed_at=datetime.now(timezone.utc) - timedelta(days=45),
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)

        yield session, learner, comp, subskill, evidence


def test_retention_provider_prediction():
    provider = RetentionProvider()
    score = provider.predict_retention({
        "days_since_learning": 30.0,
        "mastery_before_decay": 0.85,
        "decay_amount": 0.05,
        "intervention_count": 0.0,
        "intervention_boost": 0.0,
        "mastery": 0.80,
    })
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_retention_provider_evaluate_stale_evidence():
    provider = RetentionProvider()
    observed = datetime.now(timezone.utc) - timedelta(days=90)
    retention, reassess = provider.evaluate_stale_evidence(observed, current_mastery=0.75)
    assert isinstance(retention, float)
    assert isinstance(reassess, bool)
    assert 0.0 <= retention <= 1.0


def test_learning_state_provider_classification():
    provider = LearningStateProvider()
    result = provider.classify_state({
        "accuracy": 0.95,
        "average_response_time_seconds": 15.0,
        "hints_used": 0.0,
        "completion_rate": 1.0,
        "engagement_score": 0.9,
        "mastery_change": 0.15,
        "session_quality_score": 0.95,
    })
    assert "predicted_state" in result
    assert result["predicted_state"] in {"mastered", "improving", "needs_practice", "struggling"}
    assert "confidence" in result
    assert 0.0 <= result["confidence"] <= 1.0


def test_irt_provider_parameter_lookup_and_probability():
    provider = IRTProvider()
    item = provider.get_item_params("item_0001")
    assert item is not None
    assert "calibrated_difficulty_b" in item
    assert "calibrated_discrimination_a" in item

    # Higher ability theta should yield higher probability of correct response
    p_low = provider.predict_probability(theta=-2.0, item_id="item_0001")
    p_high = provider.predict_probability(theta=2.0, item_id="item_0001")
    assert 0.0 <= p_low <= 1.0
    assert 0.0 <= p_high <= 1.0
    assert p_high > p_low


def test_intervention_provider_recommendations():
    provider = InterventionProvider()
    recs_low = provider.recommend_interventions("low", top_k=2)
    assert len(recs_low) == 2
    assert all(r.get("mastery_band") == "low" for r in recs_low)

    recs_high = provider.recommend_interventions("high", top_k=3)
    assert len(recs_high) == 3
    assert all(r.get("mastery_band") == "high" for r in recs_high)


def test_monitoring_agent_wires_retention_provider(db_session):
    session, learner, comp, subskill, evidence = db_session
    retention_provider = RetentionProvider()

    req = MonitoringEventRequest(
        event_type=MonitoringEventType.EVIDENCE_STALE,
        learner_id=learner.id,
        competency_id=comp.id,
        subskill_id=subskill.id,
        source_entity_type="evidence",
        source_entity_id=evidence.id,
    )

    agent = MonitoringAgent()
    result = agent.handle_event(
        session,
        req,
        retention_provider=retention_provider,
    )

    assert result.status == "PROCESSED"
    assert result.action == "RETENTION_EVALUATED"
    assert "predicted_retention" in result.result
    assert "reassessment_needed" in result.result
    assert 0.0 <= result.result["predicted_retention"] <= 1.0


def test_signal_collector_wires_learning_state_provider(db_session):
    session, learner, comp, subskill, _ = db_session

    attempt = AssessmentAttempt(
        user_id=learner.id,
        competency_id=comp.id,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    collect_question_signal(session, attempt.id, {"response_time": 25.0, "retries": 1, "hints_requested": 0})

    learning_provider = LearningStateProvider()
    aggregate = persist_attempt_aggregate(session, attempt.id, session_duration=25.0, learning_state_provider=learning_provider)

    assert aggregate is not None
    assert aggregate.is_session_aggregate is True
