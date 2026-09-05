import os
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

os.environ["DATABASE_URL"] = f"sqlite:///{Path.cwd() / f'test_phase1_{uuid4().hex}.db'}"
os.environ["JWT_SECRET"] = "phase1-test-secret-that-is-at-least-32-chars"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import SQLModel

from app.database import SessionLocal, engine
from app.main import app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.user import User
from app.routers import assessment as assessment_router
from app.seed import seed_data
from app.utils.security import create_access_token, hash_password


@pytest.fixture(scope="module", autouse=True)
def database():
    SQLModel.metadata.create_all(engine)
    seed_data("test-seed-password")
    yield
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def login(client: TestClient, email: str = "learner@example.com", password: str = "test-seed-password") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def bank_question_id() -> int:
    with SessionLocal() as db:
        return db.execute(
            select(AssessmentItem.id).where(
                AssessmentItem.source_reference == "sample-data-quality",
                AssessmentItem.user_id.is_(None),
            )
        ).scalar_one()


def test_successful_submission_scores_on_server_and_updates_state(client):
    token = login(client)
    response = client.post(
        "/api/assessment/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"competency_id": 2, "answers": [{"question_id": bank_question_id(), "selected": "B"}]},
    )
    assert response.status_code == 200
    assert response.json()["score"] == 1.0

    with SessionLocal() as db:
        state = db.execute(
            select(CompetencyState).where(CompetencyState.user_id == 1, CompetencyState.competency_id == 2)
        ).scalar_one()
        assert state.mastery == 1.0
        assert state.confidence == 0.2
        assert state.coverage == pytest.approx(1 / 6)
        assert state.evidence_count == 1
        assert state.status == "ASSESSED"


def test_invalid_answer_is_rejected_without_writes(client):
    token = login(client)
    before = counts_for_competency(2)
    response = client.post(
        "/api/assessment/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"competency_id": 2, "answers": [{"question_id": bank_question_id(), "selected": "Z"}]},
    )
    assert response.status_code == 400
    assert counts_for_competency(2) == before


def test_wrong_answer_is_scored_by_server(client):
    token = login(client)
    response = client.post(
        "/api/assessment/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"competency_id": 2, "answers": [{"question_id": bank_question_id(), "selected": "A"}]},
    )
    assert response.status_code == 200
    assert response.json()["score"] == 0.0


def test_transaction_rolls_back_when_commit_fails(client):
    token = login(client)
    failing_session = SessionLocal()
    failing_session.flush = Mock(side_effect=SQLAlchemyError("forced write failure"))

    def override_db():
        try:
            yield failing_session
        finally:
            failing_session.close()

    app.dependency_overrides[assessment_router.get_db] = override_db
    try:
        before = counts_for_competency(2)
        response = client.post(
            "/api/assessment/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={"competency_id": 2, "answers": [{"question_id": bank_question_id(), "selected": "B"}]},
        )
        assert response.status_code == 500
        assert counts_for_competency(2) == before
    finally:
        app.dependency_overrides.pop(assessment_router.get_db, None)


def test_no_evidence_competency_remains_unassessed(client):
    token = login(client)
    dashboard = client.get("/api/dashboard/learner", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    state = next(item for item in dashboard.json()["competencies"] if item["competency_id"] == 3)
    assert state == {
        "competency_id": 3,
        "competency_name": "Python for Analytics",
        "mastery": None,
        "confidence": 0.0,
        "coverage": 0.0,
        "evidence_count": 0,
        "status": "UNASSESSED",
    }


def test_duplicate_competency_state_is_prevented():
    with SessionLocal() as db:
        duplicate = CompetencyState(user_id=1, competency_id=3)
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_unauthorized_role_and_competency_are_rejected(client):
    with SessionLocal() as db:
        role = Role(name="Other Role", description="Unauthorized test role")
        db.add(role)
        db.flush()
        user = User(
            email="other@example.com",
            full_name="Other User",
            password_hash=hash_password("other-password"),
            role_id=role.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
    token = login(client, "other@example.com", "other-password")
    role_response = client.get("/api/competencies/1", headers={"Authorization": f"Bearer {token}"})
    competency_response = client.post(
        "/api/assessment/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"competency_id": 2, "answers": [{"question_id": bank_question_id(), "selected": "B"}]},
    )
    assert role_response.status_code == 403
    assert competency_response.status_code == 403


def test_inactive_user_cannot_login_or_use_token(client):
    with SessionLocal() as db:
        user = User(
            email="inactive@example.com",
            full_name="Inactive User",
            password_hash=hash_password("inactive-password"),
            role_id=1,
            is_active=False,
        )
        db.add(user)
        db.commit()
        user_id = user.id
    login_response = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "inactive-password"})
    token_response = client.get(
        "/api/users/profile", headers={"Authorization": f"Bearer {create_access_token(user_id)}"}
    )
    assert login_response.status_code == 401
    assert token_response.status_code == 401


def test_seed_is_idempotent():
    seed_data("test-seed-password")
    seed_data("test-seed-password")
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Role).where(Role.name == "Statistical Officer")) == 1
        assert db.scalar(select(func.count()).select_from(User).where(User.email == "learner@example.com")) == 1
        assert db.scalar(select(func.count()).select_from(Evidence).where(Evidence.title == "Sample training history")) == 1
        assert db.scalar(
            select(func.count()).select_from(AssessmentItem).where(
                AssessmentItem.source_reference == "sample-data-quality",
                AssessmentItem.user_id.is_(None),
            )
        ) == 1
        assert db.scalar(select(func.count()).select_from(CompetencyState).where(CompetencyState.user_id == 1)) == 3


def counts_for_competency(competency_id: int) -> tuple[int, int, int]:
    with SessionLocal() as db:
        return (
            db.scalar(select(func.count()).select_from(AssessmentItem).where(AssessmentItem.competency_id == competency_id)),
            db.scalar(select(func.count()).select_from(Evidence).where(Evidence.competency_id == competency_id)),
            db.scalar(select(func.count()).select_from(CompetencyState).where(CompetencyState.competency_id == competency_id)),
        )
