from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

os.environ.setdefault("JWT_SECRET", "monitoring-test-secret-that-is-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.competency_state import CompetencyState
from app.models.monitoring_event import MonitoringEvent
from app.models.user import User
from app.routers import monitoring as monitoring_router
from app.schemas.monitoring import MonitoringEventRequest, MonitoringEventType
from app.services.monitoring_agent import MonitoringAgent


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    role = Role(name="Monitoring Role")
    session.add(role)
    session.flush()
    learner = User(email="monitoring@example.com", full_name="Monitoring Learner", password_hash="hashed", role_id=role.id)
    other = User(email="other-monitoring@example.com", full_name="Other Learner", password_hash="hashed", role_id=role.id)
    competency = Competency(name="Monitoring Competency", role_id=role.id)
    session.add_all([learner, other, competency])
    session.flush()
    session.add(RoleCompetency(role_id=role.id, competency_id=competency.id))
    first_subskill = SubSkill(name="First subskill", competency_id=competency.id)
    second_subskill = SubSkill(name="Second subskill", competency_id=competency.id)
    session.add_all([first_subskill, second_subskill])
    session.flush()
    evidence = Evidence(
        user_id=learner.id,
        competency_id=competency.id,
        subskill_id=first_subskill.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Monitoring evidence",
        score=0.8,
        observed_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    session.add(evidence)
    session.commit()
    yield session, learner, other, competency, first_subskill, second_subskill, evidence
    session.close()
    engine.dispose()


def event(event_type, learner_id, competency_id=None, **kwargs):
    return MonitoringEventRequest(
        event_type=event_type,
        learner_id=learner_id,
        competency_id=competency_id,
        **kwargs,
    )


def test_assessment_completed_recalculates_competency_state(db):
    session, learner, _, competency, *_ = db
    result = MonitoringAgent().handle_event(session, event(MonitoringEventType.ASSESSMENT_COMPLETED, learner.id, competency.id))
    session.commit()
    assert result.status == "PROCESSED"
    assert result.action == "COMPETENCY_STATE_RECALCULATED"
    assert result.result["gap_count"] == 1
    assert session.scalar(select(func.count()).select_from(MonitoringEvent)) == 1


def test_repeated_failure_is_provider_unavailable_without_selector(db):
    session, learner, _, competency, *_ = db
    result = MonitoringAgent().handle_event(session, event(MonitoringEventType.REPEATED_FAILURE, learner.id, competency.id))
    session.commit()
    assert result.status == "PROVIDER_UNAVAILABLE"
    assert result.action == "DIAGNOSTIC_PENDING"
    assert "provider" in result.result["reason"]


def test_evidence_stale_schedules_retention_check_without_prediction(db):
    session, learner, _, competency, _, _, evidence = db
    result = MonitoringAgent().handle_event(
        session,
        event(
            MonitoringEventType.EVIDENCE_STALE,
            learner.id,
            competency.id,
            source_entity_type="evidence",
            source_entity_id=evidence.id,
            metadata={"stale_before": datetime.now(timezone.utc).isoformat()},
        ),
    )
    session.commit()
    assert result.status == "PROVIDER_UNAVAILABLE"
    assert result.action == "RETENTION_CHECK_PENDING"
    assert "interval" in result.result["reason"]
    assert "evidence_observed_at" in result.result


@pytest.mark.parametrize(
    ("event_type", "action", "status"),
    [
        (MonitoringEventType.DELAYED_CHECK_DUE, "REASSESSMENT_PENDING", "PENDING"),
        (MonitoringEventType.INTERVENTION_COMPLETED, "POST_ASSESSMENT_PENDING", "PENDING"),
    ],
)
def test_pending_workflows_are_explicit(event_type, action, status, db):
    session, learner, _, competency, *_ = db
    result = MonitoringAgent().handle_event(session, event(event_type, learner.id, competency.id))
    assert result.action == action
    assert result.status == status


def test_new_competency_requirement_identifies_existing_gaps(db):
    session, learner, _, competency, *_ = db
    newly_required = Competency(name="New required competency", role_id=learner.role_id)
    session.add(newly_required)
    session.flush()
    session.add(RoleCompetency(role_id=learner.role_id, competency_id=newly_required.id))
    session.flush()
    result = MonitoringAgent().handle_event(
        session,
        event(MonitoringEventType.COMPETENCY_REQUIREMENT_ADDED, learner.id, newly_required.id),
    )
    assert result.status == "PROCESSED"
    assert result.action == "REQUIREMENT_GAP_EVALUATED"
    assert result.result == {
        "required_competency_id": newly_required.id,
        "competency_state_id": None,
        "gap": True,
        "reason": "No assessed competency state exists.",
    }
    assert session.scalar(
        select(func.count()).select_from(CompetencyState).where(CompetencyState.competency_id == newly_required.id)
    ) == 0


def test_invalid_context_and_event_data_are_rejected_without_persistence(db):
    session, learner, _, competency, _, _, evidence = db
    before = session.scalar(select(func.count()).select_from(MonitoringEvent))
    with pytest.raises(ValueError, match="requires source_entity"):
        MonitoringAgent().handle_event(session, event(
            MonitoringEventType.EVIDENCE_STALE,
            learner.id,
            competency.id,
        ))
    assert session.scalar(select(func.count()).select_from(MonitoringEvent)) == before + 1
    session.rollback()
    with pytest.raises(ValueError, match="Learner not found"):
        MonitoringAgent().handle_event(session, event(MonitoringEventType.DELAYED_CHECK_DUE, 999, competency.id))


def test_api_enforces_learner_ownership_and_persists_event(db):
    session, learner, other, competency, *_ = db
    app.dependency_overrides[monitoring_router.get_current_user] = lambda: learner
    app.dependency_overrides[monitoring_router.get_db] = lambda: session
    try:
        client = TestClient(app)
        forbidden = client.post(
            "/api/monitoring/events",
            json={"event_type": "delayed_check_due", "learner_id": other.id, "competency_id": competency.id},
        )
        accepted = client.post(
            "/api/monitoring/events",
            json={"event_type": "delayed_check_due", "learner_id": learner.id, "competency_id": competency.id},
        )
    finally:
        app.dependency_overrides.pop(monitoring_router.get_current_user, None)
        app.dependency_overrides.pop(monitoring_router.get_db, None)
    assert forbidden.status_code == 403
    assert accepted.status_code == 200
    assert accepted.json()["action"] == "REASSESSMENT_PENDING"


def test_api_rejects_unsupported_event_type():
    app.dependency_overrides[monitoring_router.get_current_user] = lambda: User(
        id=1,
        email="monitoring@example.com",
        full_name="Monitoring Learner",
        password_hash="hashed",
    )
    try:
        response = TestClient(app).post(
            "/api/monitoring/events",
            json={"event_type": "unknown_event", "learner_id": 1},
        )
    finally:
        app.dependency_overrides.pop(monitoring_router.get_current_user, None)
    assert response.status_code == 422
    assert any(error["loc"][-1] == "event_type" for error in response.json()["detail"])


def test_api_rolls_back_when_event_persistence_fails(db):
    session, learner, _, competency, *_ = db
    original_flush = session.flush
    session.flush = lambda *args, **kwargs: (_ for _ in ()).throw(SQLAlchemyError("forced failure"))
    app.dependency_overrides[monitoring_router.get_current_user] = lambda: learner
    app.dependency_overrides[monitoring_router.get_db] = lambda: session
    try:
        response = TestClient(app).post(
            "/api/monitoring/events",
            json={"event_type": "delayed_check_due", "learner_id": learner.id, "competency_id": competency.id},
        )
    finally:
        app.dependency_overrides.pop(monitoring_router.get_current_user, None)
        app.dependency_overrides.pop(monitoring_router.get_db, None)
        session.flush = original_flush
    assert response.status_code == 500
    assert session.scalar(select(func.count()).select_from(MonitoringEvent)) == 0