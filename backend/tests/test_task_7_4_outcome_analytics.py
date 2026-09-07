from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.competency import Competency, Role
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.outcome_analytics_service import OutcomeAnalyticsService
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
    user = db_session.execute(select(User).where(User.email == "admin_t74@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t74@mospi.gov.in",
            full_name="Admin T74",
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
    user = db_session.execute(select(User).where(User.email == "learner_t74@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_t74@mospi.gov.in",
            full_name="Learner T74",
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
        name=f"Outcome Comp {uuid.uuid4().hex[:6]}",
        code=f"OUT_{uuid.uuid4().hex[:4]}",
    )
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)
    return comp


@pytest.fixture
def sample_intervention(db_session: Session, sample_competency: Competency):
    it = Intervention(
        competency_id=sample_competency.id,
        title=f"Sample Module {uuid.uuid4().hex[:6]}",
        intervention_type="LEARNING_RESOURCE",
        provider="DIKSHA",
        source_id=f"diksha_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(it)
    db_session.commit()
    db_session.refresh(it)
    return it


# 1. Recommendation funnel empty state
def test_01_recommendation_funnel_empty(db_session: Session):
    res = OutcomeAnalyticsService.get_recommendation_funnel_analytics(db_session)
    assert "total_recommendations_generated" in res
    assert "funnel" in res
    assert "acceptance_rate" in res
    assert res["data_mode"] == "OBSERVATIONAL"


# 2. Recommendation funnel with populated status records
def test_02_recommendation_funnel_full(db_session: Session, learner_user: User, sample_competency: Competency):
    statuses = ["RECOMMENDED", "ACCEPTED", "STARTED", "COMPLETED", "REJECTED", "SKIPPED"]
    for st in statuses:
        rec = RecommendationRecord(
            recommendation_id=f"rec_{uuid.uuid4().hex[:12]}",
            user_id=learner_user.id,
            competency_id=sample_competency.id,
            status=st,
        )
        db_session.add(rec)
    db_session.commit()

    funnel = OutcomeAnalyticsService.get_recommendation_funnel_analytics(db_session)
    assert funnel["total_recommendations_generated"] >= 6
    assert funnel["funnel"]["rejected"] >= 1
    assert funnel["funnel"]["skipped"] >= 1
    assert funnel["funnel"]["completed"] >= 1


# 3. Intervention outcomes empty query
def test_03_intervention_outcomes_empty(db_session: Session):
    res = OutcomeAnalyticsService.get_intervention_outcome_analytics(db_session, provider="NON_EXISTENT_PROV")
    assert res["total_outcomes_recorded"] == 0
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["completion_rate"] == 0.0


# 4. Intervention outcomes with observed gains
def test_04_intervention_outcomes_completed_gains(
    db_session: Session, learner_user: User, sample_intervention: Intervention
):
    # 2 completed outcomes with pre and post mastery
    o1 = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=sample_intervention.id,
        status="COMPLETED",
        completion_score=0.85,
        pre_competency_mastery=0.40,
        post_competency_mastery=0.70,
        provider="DIKSHA",
    )
    o2 = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=sample_intervention.id,
        status="COMPLETED",
        completion_score=0.90,
        pre_competency_mastery=0.50,
        post_competency_mastery=0.80,
        provider="DIKSHA",
    )
    db_session.add_all([o1, o2])
    db_session.commit()

    res = OutcomeAnalyticsService.get_intervention_outcome_analytics(db_session, provider="DIKSHA")
    assert res["total_outcomes_recorded"] >= 2
    assert res["completed_count"] >= 2
    gains = res["observed_gains"]
    assert gains["sample_size"] >= 2
    assert gains["mean_gain"] is not None
    assert gains["positive_outcome_rate"] > 0


# 5. Causal disclaimer presence and rigor
def test_05_causal_disclaimer_present(db_session: Session):
    res = OutcomeAnalyticsService.get_intervention_outcome_analytics(db_session)
    assert "causal_disclaimer" in res["observed_gains"]
    assert "observational" in res["observed_gains"]["causal_disclaimer"].lower()
    assert "no causal claim" in res["observed_gains"]["causal_disclaimer"].lower()


# 6. Provider breakdown
def test_06_provider_breakdown(db_session: Session, learner_user: User, sample_competency: Competency):
    it_swayam = Intervention(
        competency_id=sample_competency.id,
        title=f"SWAYAM Module {uuid.uuid4().hex[:6]}",
        intervention_type="LEARNING_RESOURCE",
        provider="SWAYAM",
        source_id=f"swayam_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(it_swayam)
    db_session.commit()

    o_swayam = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=it_swayam.id,
        status="COMPLETED",
        completion_score=0.95,
        provider="SWAYAM",
    )
    db_session.add(o_swayam)
    db_session.commit()

    res = OutcomeAnalyticsService.get_intervention_outcome_analytics(db_session)
    pb = res["provider_breakdown"]
    assert "SWAYAM" in pb
    assert pb["SWAYAM"]["completed"] >= 1
    assert pb["SWAYAM"]["avg_score"] == 0.95


# 7. Provider filter
def test_07_filter_by_provider(db_session: Session):
    res_swayam = OutcomeAnalyticsService.get_intervention_outcome_analytics(db_session, provider="SWAYAM")
    assert res_swayam["total_outcomes_recorded"] >= 1
    for prov in res_swayam["provider_breakdown"].keys():
        assert prov == "SWAYAM"


# 8. Competency filter
def test_08_filter_by_competency(db_session: Session, sample_intervention: Intervention, learner_user: User):
    o = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=sample_intervention.id,
        status="COMPLETED",
        completion_score=0.92,
    )
    db_session.add(o)
    db_session.commit()

    res = OutcomeAnalyticsService.get_intervention_outcome_analytics(
        db_session, competency_id=sample_intervention.competency_id
    )
    assert res["total_outcomes_recorded"] >= 1



# 9. Admin REST endpoint: GET /api/admin/analytics/recommendations
def test_09_api_admin_recommendations_endpoint(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/analytics/recommendations", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "funnel" in data
    assert "acceptance_rate" in data


# 10. Admin REST endpoint: GET /api/admin/analytics/interventions/outcomes
def test_10_api_admin_interventions_outcomes_endpoint(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/analytics/interventions/outcomes", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "observed_gains" in data
    assert "provider_breakdown" in data


# 11. Learner access forbidden on recommendation analytics (403)
def test_11_learner_cannot_access_recommendation_analytics(client: TestClient, learner_user: User):
    resp = client.get("/api/admin/analytics/recommendations", headers=auth_h(learner_user))
    assert resp.status_code == 403


# 12. Learner access forbidden on intervention outcomes analytics (403)
def test_12_learner_cannot_access_intervention_analytics(client: TestClient, learner_user: User):
    resp = client.get("/api/admin/analytics/interventions/outcomes", headers=auth_h(learner_user))
    assert resp.status_code == 403
