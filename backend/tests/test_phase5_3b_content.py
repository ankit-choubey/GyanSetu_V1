from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.competency import Competency, Role, SubSkill
from app.models.content import ContentCompetencyMapping, ContentConcept, ContentItem
from app.models.user import User
from app.routers import content as content_router
from app.services.evening_interfaces import ContentConceptResult, ContentMappingResult, ContentProcessResult


@dataclass
class ProviderDouble:
    result: ContentProcessResult
    calls: list[dict]

    def process(self, filename, content_type, content, *, content_id=None, storage_reference=None):
        self.calls.append({"filename": filename, "content_type": content_type, "content": content, "content_id": content_id, "storage_reference": storage_reference})
        return self.result


@pytest.fixture
def content_context(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = factory()
    admin_role = Role(name="Administrator")
    learner_role = Role(name="Learner")
    session.add_all([admin_role, learner_role])
    session.flush()
    admin = User(email="content-admin@example.com", full_name="Admin", password_hash="hashed", role_id=admin_role.id)
    learner = User(email="content-learner@example.com", full_name="Learner", password_hash="hashed", role_id=learner_role.id)
    competency = Competency(name="Data Quality")
    unrelated = Competency(name="Security")
    session.add_all([admin, learner, competency, unrelated])
    session.flush()
    matching_subskill = SubSkill(competency_id=competency.id, name="Validation")
    unrelated_subskill = SubSkill(competency_id=unrelated.id, name="Validation")
    session.add_all([matching_subskill, unrelated_subskill])
    session.commit()
    monkeypatch.setattr(content_router.settings, "content_storage_dir", str(tmp_path))
    app.dependency_overrides[content_router.get_current_admin] = lambda: admin
    app.dependency_overrides[content_router.get_db] = lambda: session
    try:
        yield session, admin, learner, competency, matching_subskill, unrelated_subskill, tmp_path
    finally:
        app.dependency_overrides.pop(content_router.get_current_admin, None)
        app.dependency_overrides.pop(content_router.get_current_user, None)
        app.dependency_overrides.pop(content_router.get_db, None)
        session.close()
        engine.dispose()


def result(status="completed", *, mappings=(), warnings=(), errors=()):
    return ContentProcessResult(
        status=status,
        concepts=(ContentConceptResult(concept="Sampling", description="Sampling concept", subskills=("Validation",)),),
        competency_mappings=tuple(mappings),
        source_reference="Page 23, paragraph 2",
        metadata={"provider": "test"},
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def mapping(competency="Data Quality", subskills=("Validation",)):
    return ContentMappingResult(concept="Sampling", competency=competency, subskills=tuple(subskills), confidence=0.8, rationale="Directly covers the competency.")


def test_upload_requires_authentication():
    response = TestClient(app).post("/api/content/upload", files={"file": ("training.pdf", b"pdf", "application/pdf")})
    assert response.status_code == 401


def test_upload_rejects_non_admin(content_context):
    _, _, learner, *_ = content_context
    app.dependency_overrides[content_router.get_current_admin] = lambda: (_ for _ in ()).throw(HTTPException(status_code=403, detail="Administrator access required"))
    try:
        response = TestClient(app).post("/api/content/upload", files={"file": ("training.pdf", b"pdf", "application/pdf")})
    finally:
        app.dependency_overrides[content_router.get_current_admin] = lambda: content_context[1]
    assert response.status_code == 403


@pytest.mark.parametrize("filename", ["training.pdf", "slides.ppt", "slides.pptx"])
def test_upload_accepts_supported_formats_and_passes_backend_identity(content_context, filename):
    session, *_ = content_context
    provider = ProviderDouble(result("failed"), [])
    app.dependency_overrides[content_router.get_document_processor] = lambda: provider
    try:
        response = TestClient(app).post("/api/content/upload", files={"file": (filename, b"document", "application/octet-stream")})
    finally:
        app.dependency_overrides.pop(content_router.get_document_processor, None)
    assert response.status_code == 200
    payload = response.json()
    assert payload["content_id"]
    assert provider.calls[0]["content_id"] == payload["content_id"]
    assert provider.calls[0]["storage_reference"] == f"content/{payload['content_id']}{Path(filename).suffix}"
    record = session.execute(select(ContentItem).where(ContentItem.content_id == payload["content_id"])).scalar_one()
    assert record.checksum
    assert record.storage_reference.endswith(Path(filename).suffix)


def test_upload_persists_completed_concepts_mapping_and_metadata(content_context):
    session, _, _, competency, matching_subskill, _, tmp_path = content_context
    provider = ProviderDouble(result(mappings=(mapping(),)), [])
    app.dependency_overrides[content_router.get_document_processor] = lambda: provider
    try:
        response = TestClient(app).post("/api/content/upload", files={"file": ("..\\training.pdf", b"document", "application/pdf")})
    finally:
        app.dependency_overrides.pop(content_router.get_document_processor, None)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    record = session.execute(select(ContentItem).where(ContentItem.content_id == payload["content_id"])).scalar_one()
    assert record.original_filename == "training.pdf"
    assert (tmp_path / Path(record.storage_reference).name).exists()
    assert session.execute(select(ContentConcept).where(ContentConcept.content_item_id == record.id)).scalar_one().concept == "Sampling"
    persisted = session.execute(select(ContentCompetencyMapping).where(ContentCompetencyMapping.content_item_id == record.id)).scalar_one()
    assert persisted.competency_id == competency.id
    assert persisted.subskill_id == matching_subskill.id
    assert persisted.source_reference == "Page 23, paragraph 2"
    assert persisted.rationale == "Directly covers the competency."


def test_mapping_names_are_case_insensitive_and_unknown_ids_are_not_fabricated(content_context):
    session, *_ = content_context
    provider = ProviderDouble(result(mappings=(mapping(competency=" unknown ", subskills=("Validation",)),)), [])
    app.dependency_overrides[content_router.get_document_processor] = lambda: provider
    try:
        response = TestClient(app).post("/api/content/upload", files={"file": ("training.pdf", b"document", "application/pdf")})
    finally:
        app.dependency_overrides.pop(content_router.get_document_processor, None)
    assert response.status_code == 200
    assert response.json()["errors"][0]["code"] == "MAPPING_FAILURE"
    record = session.execute(select(ContentItem).where(ContentItem.content_id == response.json()["content_id"])).scalar_one()
    assert record.status == "PARTIAL"
    assert session.execute(select(ContentCompetencyMapping)).scalars().all() == []


def test_unavailable_provider_persists_failed_state_and_diagnostics(content_context):
    session, *_ = content_context
    response = TestClient(app).post("/api/content/upload", files={"file": ("training.pdf", b"document", "application/pdf")})
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert response.json()["errors"][0]["code"] == "PROVIDER_UNAVAILABLE"
    record = session.execute(select(ContentItem).where(ContentItem.content_id == response.json()["content_id"])).scalar_one()
    assert record.ml_status == "failed"


def test_empty_unsupported_and_oversized_files_are_rejected(content_context):
    _, *_rest, tmp_path = content_context
    client = TestClient(app)
    assert client.post("/api/content/upload", files={"file": ("empty.pdf", b"", "application/pdf")}).json()["detail"] == "EMPTY_CONTENT"
    assert client.post("/api/content/upload", files={"file": ("notes.txt", b"text", "text/plain")}).json()["detail"] == "UNSUPPORTED_FORMAT"
    original_limit = content_router.settings.content_max_upload_bytes
    content_router.settings.content_max_upload_bytes = 2
    try:
        response = client.post("/api/content/upload", files={"file": ("large.pdf", b"123", "application/pdf")})
    finally:
        content_router.settings.content_max_upload_bytes = original_limit
    assert response.status_code == 413
    assert list(tmp_path.iterdir()) == []