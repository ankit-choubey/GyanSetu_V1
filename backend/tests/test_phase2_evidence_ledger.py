from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.dependencies import get_current_user, get_db
from app.main import app
from app.models.competency import Competency, Role, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User


@pytest.fixture
def env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    role = Role(name="Officer")
    session.add(role)
    session.flush()

    user1 = User(id=101, email="user1@example.com", full_name="User One", password_hash="hash", role_id=role.id)
    user2 = User(id=102, email="user2@example.com", full_name="User Two", password_hash="hash", role_id=role.id)
    session.add_all([user1, user2])
    session.flush()

    comp1 = Competency(id=1, role_id=role.id, name="Data Verification")
    comp2 = Competency(id=2, role_id=role.id, name="Statistical Analysis")
    session.add_all([comp1, comp2])
    session.flush()

    # User 1 evidence
    ev1 = Evidence(
        user_id=user1.id,
        competency_id=comp1.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Quiz A",
        score=0.9,
        source="TEST_SYSTEM",
        provenance="[CURATED]",
    )
    ev2 = Evidence(
        user_id=user1.id,
        competency_id=comp2.id,
        evidence_type=EvidenceType.APPLICATION_SCENARIO,
        title="Scenario B",
        score=0.8,
        source="TEST_SYSTEM",
        provenance="[LIVE INTEGRATION]",
    )
    # User 2 evidence
    ev3 = Evidence(
        user_id=user2.id,
        competency_id=comp1.id,
        evidence_type=EvidenceType.PRACTICAL_TASK,
        title="Secret Task User 2",
        score=0.7,
        source="TEST_SYSTEM",
    )
    session.add_all([ev1, ev2, ev3])
    session.commit()

    yield session, user1, user2, comp1, comp2

    session.close()
    engine.dispose()


def test_evidence_ledger_requires_authentication():
    client = TestClient(app)
    resp = client.get("/api/evidence")
    assert resp.status_code == 401


def test_evidence_ledger_returns_records_with_provenance_and_filters(env):
    session, user1, _, comp1, comp2 = env

    app.dependency_overrides[get_current_user] = lambda: user1
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    try:
        # All evidence for user1
        resp = client.get("/api/evidence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["learner_id"] == user1.id
        assert data["total_records"] == 2
        titles = [r["title"] for r in data["evidence"]]
        assert "Quiz A" in titles
        assert "Scenario B" in titles

        # Provenance and source metadata verified
        item_a = next(r for r in data["evidence"] if r["title"] == "Quiz A")
        assert item_a["provenance"] == "[CURATED]"
        assert item_a["source"] == "TEST_SYSTEM"
        assert item_a["reliability_status"] == "VERIFIED"

        # Filter by competency_id
        resp_filtered = client.get(f"/api/evidence?competency_id={comp1.id}")
        assert resp_filtered.status_code == 200
        filtered_data = resp_filtered.json()
        assert filtered_data["total_records"] == 1
        assert filtered_data["evidence"][0]["competency_id"] == comp1.id

        # Filter by evidence_type
        resp_type = client.get("/api/evidence?evidence_type=APPLICATION_SCENARIO")
        assert resp_type.status_code == 200
        type_data = resp_type.json()
        assert type_data["total_records"] == 1
        assert type_data["evidence"][0]["evidence_type"] == "APPLICATION_SCENARIO"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_evidence_ledger_enforces_strict_user_isolation(env):
    session, user1, user2, _, _ = env

    # Logged in as User 1
    app.dependency_overrides[get_current_user] = lambda: user1
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    try:
        resp = client.get("/api/evidence")
        assert resp.status_code == 200
        data = resp.json()
        # Verify user 2's evidence is NEVER exposed to user 1
        titles = [r["title"] for r in data["evidence"]]
        assert "Secret Task User 2" not in titles
        for record in data["evidence"]:
            assert record["user_id"] == user1.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
