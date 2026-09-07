from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.competency import Competency, Role
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.services.longitudinal_analytics_service import LongitudinalAnalyticsService
from app.utils.security import create_access_token


@pytest.fixture
def db_session():
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db_session: Session):
    admin_role = db_session.execute(
        select(Role).where(Role.name.in_(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "admin_t73@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t73@mospi.gov.in",
            full_name="Admin T73",
            role_id=admin_role.id if admin_role else 2,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def learner_user(db_session: Session):
    role = db_session.execute(
        select(Role).where(Role.name.not_in(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "learner_t73@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_t73@mospi.gov.in",
            full_name="Learner T73",
            role_id=role.id if role else 1,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_session: Session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_competency(db_session: Session):
    comp = Competency(
        name=f"Clean Competency {uuid.uuid4().hex[:6]}",
        code=f"CLEAN_{uuid.uuid4().hex[:4]}",
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)
    return comp


@pytest.fixture
def seeded_competency(db_session: Session, learner_user: User):
    comp = Competency(
        name=f"Seeded Longitudinal {uuid.uuid4().hex[:6]}",
        code=f"LONG_{uuid.uuid4().hex[:4]}",
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)

    now = datetime.now(timezone.utc)
    h1 = CompetencyHistory(
        user_id=learner_user.id,
        competency_id=comp.id,
        previous_mastery=0.0,
        new_mastery=0.30,
        new_confidence=0.40,
        new_status="EMERGING",
        state_version=1,
        timestamp=now - timedelta(days=20),
    )
    h2 = CompetencyHistory(
        user_id=learner_user.id,
        competency_id=comp.id,
        previous_mastery=0.30,
        new_mastery=0.55,
        new_confidence=0.65,
        new_status="DEVELOPING",
        state_version=2,
        timestamp=now - timedelta(days=10),
    )
    h3 = CompetencyHistory(
        user_id=learner_user.id,
        competency_id=comp.id,
        previous_mastery=0.55,
        new_mastery=0.75,
        new_confidence=0.85,
        new_status="PROFICIENT",
        state_version=3,
        timestamp=now - timedelta(days=2),
    )
    db_session.add_all([h1, h2, h3])

    state = CompetencyState(
        user_id=learner_user.id,
        competency_id=comp.id,
        mastery=0.75,
        confidence=0.85,
        uncertainty=0.15,
        status="PROFICIENT",
        last_assessed_at=now - timedelta(days=2),
    )
    db_session.add(state)
    db_session.commit()
    db_session.refresh(comp)
    return comp


# 1. Competency history when empty
def test_01_competency_history_empty(db_session: Session, sample_competency: Competency, learner_user: User):
    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=sample_competency.id
    )
    assert res["competency_id"] == sample_competency.id
    assert res["current_status"] == "UNASSESSED"
    assert res["current_uncertainty"] == 1.0
    assert len(res["trajectory_timeline"]) == 0


# 2. Competency trajectory progression & gain
def test_02_competency_history_trajectory(db_session: Session, seeded_competency: Competency, learner_user: User):
    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    assert res["total_state_transitions"] == 3
    assert res["initial_mastery"] == 0.30
    assert res["current_mastery"] == 0.75
    assert res["observed_competency_gain"] == 0.45


# 3. Uncertainty tracking (U = 1 - C)
def test_03_uncertainty_tracking(db_session: Session, seeded_competency: Competency, learner_user: User):
    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    assert res["current_uncertainty"] == round(1.0 - 0.85, 4)
    for point in res["trajectory_timeline"]:
        assert point["uncertainty"] == round(1.0 - point["confidence"], 4)


# 4. Evidence accumulation breakdown
def test_04_evidence_breakdown(db_session: Session, seeded_competency: Competency, learner_user: User):
    e1 = Evidence(
        user_id=learner_user.id,
        competency_id=seeded_competency.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Diagnostic Assessment E1",
        source="ASSESSMENT",
        score=0.8,
        weight=1.0,
    )
    e2 = Evidence(
        user_id=learner_user.id,
        competency_id=seeded_competency.id,
        evidence_type=EvidenceType.TRAINING_HISTORY,
        title="Intervention Completion E2",
        source="INTERVENTION",
        score=0.9,
        weight=1.0,
    )
    db_session.add_all([e1, e2])
    db_session.commit()

    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    assert res["total_evidence_count"] >= 2
    assert "ASSESSMENT" in res["evidence_count_by_source"]
    assert "INTERVENTION" in res["evidence_count_by_source"]


# 5. Retention window fresh (< 90 days)
def test_05_retention_window_fresh(db_session: Session, seeded_competency: Competency, learner_user: User):
    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    assert res["retention_refresher_recommended"] is False
    assert res["days_since_last_assessment"] is not None
    assert res["days_since_last_assessment"] <= 5


# 6. Retention window expired (> 90 days)
def test_06_retention_window_expired(db_session: Session, seeded_competency: Competency, learner_user: User):
    state = db_session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == learner_user.id,
            CompetencyState.competency_id == seeded_competency.id,
        )
    ).scalar_one()
    state.last_assessed_at = datetime.now(timezone.utc) - timedelta(days=95)
    db_session.commit()

    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    assert res["retention_refresher_recommended"] is True
    assert res["days_since_last_assessment"] >= 95


# 7. Non-causal language validation
def test_07_non_causal_language(db_session: Session, seeded_competency: Competency, learner_user: User):
    res = LongitudinalAnalyticsService.get_competency_history(
        db_session, user_id=learner_user.id, competency_id=seeded_competency.id
    )
    interp = res["interpretation"]
    assert "Observed" in interp
    assert "causal" not in interp.lower()
    assert "proved" not in interp.lower()


# 8. Learner multi-competency overview
def test_08_learner_timeline_overview(db_session: Session, seeded_competency: Competency, learner_user: User):
    timeline = LongitudinalAnalyticsService.get_learner_timeline(db_session, user_id=learner_user.id)
    assert timeline["user_id"] == learner_user.id
    assert timeline["total_tracked_competencies"] >= 1
    assert len(timeline["competencies"]) >= 1


# 9. API endpoint: GET /api/competency/timeline
def test_09_api_learner_timeline_endpoint(client: TestClient, learner_user: User, seeded_competency: Competency):
    resp = client.get("/api/competency/timeline", headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == learner_user.id
    assert "competencies" in data


# 10. API endpoint: GET /api/competency/timeline/{competency_id}
def test_10_api_learner_competency_history_endpoint(
    client: TestClient, learner_user: User, seeded_competency: Competency
):
    resp = client.get(f"/api/competency/timeline/{seeded_competency.id}", headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["competency_id"] == seeded_competency.id
    assert "trajectory_timeline" in data


# 11. Admin API endpoints: GET /api/admin/analytics/learners/{user_id}/longitudinal
def test_11_api_admin_learner_longitudinal(
    client: TestClient, admin_user: User, learner_user: User, seeded_competency: Competency
):
    resp1 = client.get(f"/api/admin/analytics/learners/{learner_user.id}/longitudinal", headers=auth_h(admin_user))
    assert resp1.status_code == 200
    assert resp1.json()["user_id"] == learner_user.id

    resp2 = client.get(
        f"/api/admin/analytics/learners/{learner_user.id}/longitudinal/{seeded_competency.id}",
        headers=auth_h(admin_user),
    )
    assert resp2.status_code == 200
    assert resp2.json()["competency_id"] == seeded_competency.id


# 12. Learner cannot access admin longitudinal endpoint (403)
def test_12_rbac_learner_cannot_access_admin_longitudinal(client: TestClient, learner_user: User):
    resp = client.get(f"/api/admin/analytics/learners/{learner_user.id}/longitudinal", headers=auth_h(learner_user))
    assert resp.status_code == 403
