from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role
from app.models.user import User
from app.services.assessment_analytics_service import AssessmentAnalyticsService
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
    user = db_session.execute(select(User).where(User.email == "admin_t72@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t72@mospi.gov.in",
            full_name="Admin T72",
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
    user = db_session.execute(select(User).where(User.email == "learner_t72@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_t72@mospi.gov.in",
            full_name="Learner T72",
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
    comp = db_session.execute(select(Competency)).scalars().first()
    if not comp:
        comp = Competency(name="Sampling Statistics T72", code=f"STAT_{uuid.uuid4().hex[:4]}")
        db_session.add(comp)
        db_session.commit()
        db_session.refresh(comp)
    return comp


# 1. Cold start item
def test_01_item_statistics_cold_start(db_session: Session, sample_competency: Competency):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Cold start question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"}),
        correct_option="A",
        difficulty="EASY",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert stats["item_id"] == item.id
    assert stats["sample_size"] == 0
    assert stats["status"] == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT_DATA" in stats["quality_flags"]
    assert "NEVER_ATTEMPTED" in stats["quality_flags"]
    assert stats["lifecycle_recommendation"] == "REVIEW"


# 2. Insufficient sample size (< 5 responses)
def test_02_item_statistics_insufficient_sample(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Insufficient sample question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Option A", "B": "Option B"}),
        correct_option="A",
        difficulty="MEDIUM",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 3 attempts
    for i in range(3):
        attempt = AssessmentAttempt(
            user_id=learner_user.id,
            competency_id=sample_competency.id,
            score=0.7,
        )
        db_session.add(attempt)
        db_session.commit()
        db_session.refresh(attempt)

        resp = AssessmentResponse(
            attempt_id=attempt.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option="A",
            is_correct=True,
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert stats["sample_size"] == 3
    assert stats["status"] == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT_DATA" in stats["quality_flags"]


# 3. Extremely easy item (> 0.95 difficulty p-value)
def test_03_item_statistics_extremely_easy(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Extremely easy question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Correct", "B": "Wrong"}),
        correct_option="A",
        difficulty="EASY",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 10 correct attempts
    for _ in range(10):
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=sample_competency.id, score=1.0)
        db_session.add(att)
        db_session.commit()
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option="A",
            is_correct=True,
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert stats["sample_size"] == 10
    assert stats["difficulty_index"] == 1.0
    assert "EXTREMELY_EASY" in stats["quality_flags"]


# 4. Extremely hard item (< 0.20 difficulty p-value)
def test_04_item_statistics_extremely_hard(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Extremely hard question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Correct", "B": "Wrong"}),
        correct_option="A",
        difficulty="HARD",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 10 attempts: 1 correct, 9 wrong
    for i in range(10):
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=sample_competency.id, score=0.2)
        db_session.add(att)
        db_session.commit()
        is_c = (i == 0)
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option="A" if is_c else "B",
            is_correct=is_c,
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert stats["sample_size"] == 10
    assert stats["difficulty_index"] == 0.1
    assert "EXTREMELY_HARD" in stats["quality_flags"]
    assert stats["lifecycle_recommendation"] == "REVIEW"


# 5. Distractor distribution analysis
def test_05_distractor_analysis(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Distractor analysis question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"}),
        correct_option="A",
        difficulty="MEDIUM",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 6 on A, 2 on B, 2 on C, 0 on D
    responses_to_make = ["A"] * 6 + ["B"] * 2 + ["C"] * 2
    for opt in responses_to_make:
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=sample_competency.id, score=0.5)
        db_session.add(att)
        db_session.commit()
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option=opt,
            is_correct=(opt == "A"),
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    dist = stats["option_distribution"]
    assert dist["A"]["count"] == 6
    assert dist["A"]["is_correct"] is True
    assert dist["B"]["count"] == 2
    assert dist["B"]["is_correct"] is False
    assert dist["D"]["count"] == 0
    assert "DISTRACTOR_UNUSED" in stats["quality_flags"]


# 6. Distractor dominant anomaly
def test_06_distractor_dominant_flag(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Dominant distractor question {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Correct", "B": "Misleading Distractor"}),
        correct_option="A",
        difficulty="HARD",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # 2 on A, 8 on B
    for opt in ["A"] * 2 + ["B"] * 8:
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=sample_competency.id, score=0.3)
        db_session.add(att)
        db_session.commit()
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option=opt,
            is_correct=(opt == "A"),
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert "DISTRACTOR_DOMINANT" in stats["quality_flags"]
    assert stats["lifecycle_recommendation"] == "REVIEW"


# 7. Discrimination index (Point-Biserial Correlation)
def test_07_point_biserial_discrimination(db_session: Session, sample_competency: Competency, learner_user: User):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"Discrimination test item {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Correct", "B": "Wrong"}),
        correct_option="A",
        difficulty="MEDIUM",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    # High scorers (score=0.9) get it right, low scorers (score=0.2) get it wrong
    for i in range(10):
        is_high = (i < 5)
        score = 0.9 if is_high else 0.2
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=sample_competency.id, score=score)
        db_session.add(att)
        db_session.commit()
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=sample_competency.id,
            selected_option="A" if is_high else "B",
            is_correct=is_high,
        )
        db_session.add(resp)
    db_session.commit()

    stats = AssessmentAnalyticsService.get_item_statistics(db_session, item.id)
    assert stats["discrimination_index"] is not None
    assert stats["discrimination_index"] > 0.4  # Strong positive discrimination


# 8. Question bank aggregate analytics
def test_08_question_bank_analytics_catalog(db_session: Session):
    catalog = AssessmentAnalyticsService.get_question_bank_analytics(db_session, limit=10)
    assert "total_items_in_catalog" in catalog
    assert "evaluated_count" in catalog
    assert "items" in catalog
    assert catalog["total_items_in_catalog"] >= 1


# 9. Question bank filter by quality flag
def test_09_question_bank_filter_flag(db_session: Session):
    catalog = AssessmentAnalyticsService.get_question_bank_analytics(
        db_session, quality_flag="INSUFFICIENT_DATA", limit=20
    )
    assert "items" in catalog
    for it in catalog["items"]:
        assert "INSUFFICIENT_DATA" in it.get("quality_flags", [])


# 10. Admin REST endpoint: GET /api/admin/assessment/items/analytics
def test_10_api_admin_items_analytics_endpoint(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/assessment/items/analytics", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_items_in_catalog" in data
    assert "items" in data


# 11. Admin REST endpoints: GET /api/admin/assessment/items/{id}/analytics and quality
def test_11_api_admin_single_item_analytics_and_quality(
    client: TestClient, admin_user: User, db_session: Session, sample_competency: Competency
):
    item = AssessmentItem(
        competency_id=sample_competency.id,
        question_text=f"API item {uuid.uuid4().hex[:6]}",
        options_json=json.dumps({"A": "Yes", "B": "No"}),
        correct_option="A",
        difficulty="MEDIUM",
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    resp1 = client.get(f"/api/admin/assessment/items/{item.id}/analytics", headers=auth_h(admin_user))
    assert resp1.status_code == 200
    assert resp1.json()["item_id"] == item.id

    resp2 = client.get(f"/api/admin/assessment/items/{item.id}/quality", headers=auth_h(admin_user))
    assert resp2.status_code == 200
    assert "quality_flags" in resp2.json()


# 12. Learner access forbidden (403) on admin item analytics endpoints
def test_12_learner_access_forbidden(client: TestClient, learner_user: User):
    resp1 = client.get("/api/admin/assessment/items/analytics", headers=auth_h(learner_user))
    assert resp1.status_code == 403

    resp2 = client.get("/api/admin/assessment/items/1/analytics", headers=auth_h(learner_user))
    assert resp2.status_code == 403

    resp3 = client.get("/api/admin/assessment/items/1/quality", headers=auth_h(learner_user))
    assert resp3.status_code == 403
