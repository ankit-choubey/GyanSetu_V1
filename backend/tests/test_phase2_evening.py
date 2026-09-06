from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.routers import admin as admin_router
from app.routers import chatbot as chatbot_router
from app.routers import content as content_router
from app.seed import seed_data
from app.services.evening_interfaces import ChatAnswer, DocumentProcessResult


@dataclass
class RagDouble:
    def answer(self, request):
        return ChatAnswer(
            status="GROUNDED",
            answer="Use the verified training material.",
            sources=("sandbox/page-1",),
            source_mode="TEST_DOUBLE",
        )


@dataclass
class DocumentDouble:
    def process(self, filename, content_type, content):
        return DocumentProcessResult(
            status="PARTIAL_EXTRACTION",
            trusted=False,
            coverage=0.5,
            successful_pages=(1,),
            failed_pages=(2,),
            warning="Incomplete content; trusted assessment generation is blocked.",
        )


def test_chatbot_requires_authentication():
    client = TestClient(app)
    response = client.post("/api/chatbot/ask", json={"question": "What is sampling?"})
    assert response.status_code == 401


def test_chatbot_uses_rag_boundary_and_preserves_sources():
    app.dependency_overrides[chatbot_router.get_current_user] = lambda: User(id=1, email="user@example.com", full_name="User", password_hash="hashed")
    app.dependency_overrides[chatbot_router.get_rag_provider] = lambda: RagDouble()
    try:
        response = TestClient(app).post("/api/chatbot/ask", json={"question": "What is sampling?"})
    finally:
        app.dependency_overrides.pop(chatbot_router.get_current_user, None)
        app.dependency_overrides.pop(chatbot_router.get_rag_provider, None)
    assert response.status_code == 200
    assert response.json() == {
        "status": "GROUNDED",
        "answer": "Use the verified training material.",
        "sources": ["sandbox/page-1"],
        "source_mode": "TEST_DOUBLE",
    }


def test_chatbot_default_is_explicit_abstention():
    app.dependency_overrides[chatbot_router.get_current_user] = lambda: User(id=1, email="user@example.com", full_name="User", password_hash="hashed")
    try:
        response = TestClient(app).post("/api/chatbot/ask", json={"question": "What is sampling?"})
    finally:
        app.dependency_overrides.pop(chatbot_router.get_current_user, None)
    assert response.status_code == 200
    assert response.json()["status"] == "ABSTAINED"
    assert response.json()["source_mode"] == "UNAVAILABLE"
    assert "don't have enough verified information" in response.json()["answer"]


def test_document_upload_validates_format_and_preserves_partial_extraction():
    app.dependency_overrides[content_router.get_current_admin] = lambda: User(id=1, email="admin@example.com", full_name="Admin", password_hash="hashed")
    app.dependency_overrides[content_router.get_document_processor] = lambda: DocumentDouble()
    try:
        client = TestClient(app)
        response = client.post(
            "/api/content/upload",
            files={"file": ("training.pdf", b"pdf bytes", "application/pdf")},
        )
        unsupported = client.post(
            "/api/content/upload",
            files={"file": ("notes.txt", b"text", "text/plain")},
        )
    finally:
        app.dependency_overrides.pop(content_router.get_current_admin, None)
        app.dependency_overrides.pop(content_router.get_document_processor, None)
    assert response.status_code == 200
    assert response.json()["status"] == "PARTIAL_EXTRACTION"
    assert response.json()["trusted"] is False
    assert response.json()["failed_pages"] == [2]
    assert unsupported.status_code == 400
    assert unsupported.json()["detail"] == "UNSUPPORTED_FORMAT"


def test_admin_analytics_is_aggregate_and_authorized():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = factory()
    admin_role = Role(name="Analytics Admin")
    learner_role = Role(name="Analytics Learner")
    session.add_all([admin_role, learner_role])
    session.flush()
    competency = Competency(role_id=learner_role.id, name="Data Quality")
    learner = User(email="analytics-learner@example.com", full_name="Learner", password_hash="hashed", role_id=learner_role.id)
    session.add_all([competency, learner])
    session.flush()
    session.add(RoleCompetency(role_id=learner_role.id, competency_id=competency.id))
    session.add(CompetencyState(user_id=learner.id, competency_id=competency.id, mastery=0.8, confidence=0.4, coverage=0.2, evidence_count=2, status="ASSESSED"))
    session.commit()
    app.dependency_overrides[admin_router.get_current_admin] = lambda: User(id=99, email="admin@example.com", full_name="Admin", password_hash="hashed", role_id=admin_role.id)
    app.dependency_overrides[admin_router.get_db] = lambda: session
    try:
        response = TestClient(app).get("/api/admin/analytics/competencies")
    finally:
        app.dependency_overrides.pop(admin_router.get_current_admin, None)
        app.dependency_overrides.pop(admin_router.get_db, None)
        session.close()
        engine.dispose()
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_competencies"] == 1
    assert payload["competencies"][0]["learner_count"] == 1
    assert payload["competencies"][0]["average_mastery"] == 0.8
    assert "email" not in payload["competencies"][0]


def test_seed_evening_data_is_transactional_and_idempotent(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("app.seed_data.runner.SessionLocal", factory)
    SQLModel.metadata.create_all(engine)
    seed_data("evening-test-password")
    seed_data("evening-test-password")
    with factory() as session:
        assert session.query(Role).filter(Role.name == "Administrator").count() == 1
        assert session.query(User).filter(User.email == "sandbox.analyst@example.com").count() == 1
        assert session.query(CompetencyState).count() >= 3
    engine.dispose()
