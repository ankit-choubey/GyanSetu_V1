from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.database import get_db
from app.main import app
from app.models.competency import Competency, CompetencyDomain, Role, SubSkill
from app.models.content import (
    ContentAsset,
    ContentChunk,
    ContentStatus,
    ContentVersion,
    JobStatus,
    ProcessingJob,
)
from app.models.user import User
from app.services.content.content_interfaces import (
    CandidateAssessment,
    CandidateAssessmentValidationError,
    ChunkedBlock,
    ContentExtractionError,
    ContentMappingError,
    DeterministicAssessmentGenerator,
    DeterministicContentChunker,
    DeterministicContentExtractor,
    DeterministicContentMapper,
    ExtractedDocument,
    ExtractedSection,
    MappedConcept,
    validate_assessment_candidate,
)
from app.services.content.content_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    ContentService,
    ContentValidationError,
    InvalidStateTransitionError,
)
from app.utils.security import create_access_token, hash_password


@pytest.fixture
def setup_content_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed roles
    admin_role = Role(name="Admin")
    learner_role = Role(name="Field Investigator")
    session.add_all([admin_role, learner_role])
    session.flush()

    # Seed competency taxonomy
    comp = Competency(name="Consumer Expenditure Survey", domain=CompetencyDomain.STATISTICAL)
    session.add(comp)
    session.flush()

    sub = SubSkill(name="Item Classification", competency_id=comp.id)
    session.add(sub)
    session.flush()

    # Users
    admin_user = User(
        email="admin@mospi.gov.in",
        full_name="Admin Officer",
        password_hash=hash_password("adminpass"),
        role_id=admin_role.id,
        is_active=True,
    )
    learner_user = User(
        email="learner@mospi.gov.in",
        full_name="Junior Officer",
        password_hash=hash_password("learnerpass"),
        role_id=learner_role.id,
        is_active=True,
    )
    session.add_all([admin_user, learner_user])
    session.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield session, admin_user, learner_user, comp, sub

    app.dependency_overrides.clear()
    session.close()


def test_1_valid_pdf_upload(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    pdf_bytes = b"%PDF-1.4 sample valid content bytes for test"
    files = {"file": ("sampling_guide.pdf", pdf_bytes, "application/pdf")}
    resp = client.post("/api/content/upload", files=files, headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "sampling_guide.pdf"
    assert data["status"] == "UPLOADED"
    assert data["asset_id"] is not None


def test_2_invalid_file_rejected(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    # Empty file
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = client.post("/api/content/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_3_oversized_file_rejected(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    # File exceeding 15MB limit
    oversized = b"x" * (16 * 1024 * 1024)
    files = {"file": ("huge.pdf", oversized, "application/pdf")}
    resp = client.post("/api/content/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_4_unsupported_media_type_rejected(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    files = {"file": ("script.exe", b"binary content", "application/x-msdownload")}
    resp = client.post("/api/content/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_5_duplicate_checksum_handled(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    content = b"Exact identical content bytes for checksum test"
    files1 = {"file": ("manual_v1.pdf", content, "application/pdf")}
    files2 = {"file": ("manual_copy.pdf", content, "application/pdf")}

    resp1 = client.post("/api/content/upload", files=files1, headers={"Authorization": f"Bearer {token}"})
    resp2 = client.post("/api/content/upload", files=files2, headers={"Authorization": f"Bearer {token}"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["asset_id"] == resp2.json()["asset_id"]
    assert resp2.json()["is_duplicate"] is True


def test_6_content_metadata_persisted(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(learner_user.id)
    client = TestClient(app)

    asset, job, _ = ContentService.upload_content_asset(
        session, "metadata_test.pdf", "application/pdf", b"Content for metadata check"
    )

    resp = client.get(f"/api/content/{asset.asset_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["asset_id"] == asset.asset_id
    assert data["file_size"] == len(b"Content for metadata check")


def test_7_processing_job_created(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    asset, job, _ = ContentService.upload_content_asset(
        session, "job_test.pdf", "application/pdf", b"Job check content"
    )

    assert job is not None
    assert job.status == JobStatus.QUEUED.value
    assert job.current_stage == "UPLOADED"


def test_8_processing_status_changes(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    asset, job, _ = ContentService.upload_content_asset(
        session, "pipeline_test.pdf", "application/pdf", b"Official MoSPI procedure on Consumer Expenditure Survey sampling"
    )

    resp = client.post(f"/api/content/{asset.asset_id}/process", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["current_stage"] == "READY"


def test_9_extracted_content_persisted(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    content = b"MoSPI Guidelines\n\nChapter 1: Consumer Expenditure Survey\nField data verification rules."
    asset, job, _ = ContentService.upload_content_asset(session, "extract_test.pdf", "application/pdf", content)

    asset, job, chunks, candidates = ContentService.process_content_asset(
        session, asset.asset_id, content_bytes_override=content
    )
    assert len(chunks) >= 1
    assert "Consumer Expenditure" in chunks[0].content


def test_10_chunks_persisted(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(learner_user.id)
    client = TestClient(app)

    content = b"Section 1: Survey Sampling Standards.\n\nSection 2: Imputation Calculations."
    asset, job, _ = ContentService.upload_content_asset(session, "chunk_test.pdf", "application/pdf", content)
    ContentService.process_content_asset(session, asset.asset_id, content_bytes_override=content)

    resp = client.get(f"/api/content/{asset.asset_id}/chunks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    chunks = resp.json()
    assert len(chunks) >= 1
    assert chunks[0]["chunk_type"] == "TEXT"


def test_11_provenance_preserved(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(learner_user.id)
    client = TestClient(app)

    content = b"Consumer Expenditure Survey data verification and sampling frame."
    asset, job, _ = ContentService.upload_content_asset(session, "provenance_test.pdf", "application/pdf", content)
    ContentService.process_content_asset(session, asset.asset_id, content_bytes_override=content)

    resp = client.get(f"/api/content/{asset.asset_id}/candidates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) >= 1
    assert f"[INGESTED_CONTENT:{asset.asset_id}:chunk_" in candidates[0]["provenance"]


def test_12_failed_processing_produces_failed_state(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db

    class FailingExtractor:
        def extract(self, fn, mt, cb):
            raise ContentExtractionError("Corrupt document stream")

    asset, job, _ = ContentService.upload_content_asset(session, "fail_test.pdf", "application/pdf", b"corrupt bytes")
    with pytest.raises(ContentExtractionError):
        ContentService.process_content_asset(session, asset.asset_id, extractor=FailingExtractor())

    session.refresh(asset)
    session.refresh(job)
    assert asset.status == ContentStatus.FAILED.value
    assert job.status == JobStatus.FAILED.value
    assert "Corrupt document stream" in job.error_details


def test_13_retry_works(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    # Initial fail
    asset, job, _ = ContentService.upload_content_asset(session, "retry_test.pdf", "application/pdf", b"valid on retry")
    asset.status = ContentStatus.FAILED.value
    job.status = JobStatus.FAILED.value
    job.error_details = "Transient failure"
    session.commit()

    resp = client.post(f"/api/content/{asset.asset_id}/retry", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["retry_count"] == 1


def test_14_successful_retry_reaches_ready(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    asset, job, _ = ContentService.upload_content_asset(session, "ready_test.pdf", "application/pdf", b"retry to ready")
    asset.status = ContentStatus.FAILED.value
    job.status = JobStatus.FAILED.value
    session.commit()

    asset, job = ContentService.retry_processing_job(session, asset.asset_id)
    assert asset.status == ContentStatus.READY.value
    assert job.status == JobStatus.COMPLETED.value


def test_15_unauthorized_access_rejected(setup_content_db):
    client = TestClient(app)
    resp = client.get("/api/content")
    assert resp.status_code in (401, 403)


def test_16_learner_cannot_access_admin_only_controls(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(learner_user.id)
    client = TestClient(app)

    files = {"file": ("learner_upload.pdf", b"pdf", "application/pdf")}
    resp = client.post("/api/content/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403  # Learner rejected from admin upload


def test_17_content_versioning_works(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    asset, job, _ = ContentService.upload_content_asset(session, "versioned.pdf", "application/pdf", b"Version 1 bytes")
    versions = session.execute(
        select(ContentVersion).where(ContentVersion.asset_id == asset.id)
    ).scalars().all()
    assert len(versions) == 1
    assert versions[0].version_number == 1


def test_18_retired_content_cannot_be_used_where_prohibited(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    token = create_access_token(admin_user.id)
    client = TestClient(app)

    asset, job, _ = ContentService.upload_content_asset(session, "retire_me.pdf", "application/pdf", b"content")
    resp = client.post(f"/api/content/{asset.asset_id}/retire", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "RETIRED"

    session.expire_all()
    # Processing a retired asset must be rejected
    with pytest.raises(InvalidStateTransitionError):
        ContentService.process_content_asset(session, asset.asset_id)


def test_19_malformed_mapper_output_is_rejected(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db

    class MalformedMapper:
        def map_chunk(self, db, chunk):
            raise ContentMappingError("Invalid mapping schema")

    asset, job, _ = ContentService.upload_content_asset(session, "map_fail.pdf", "application/pdf", b"content")
    with pytest.raises(ContentMappingError):
        ContentService.process_content_asset(session, asset.asset_id, mapper=MalformedMapper())


def test_20_candidate_assessment_output_passes_through_backend_validation(setup_content_db):
    session, admin_user, learner_user, comp, sub = setup_content_db
    valid_cand = CandidateAssessment(
        prompt="What is the standard procedure for sample selection in the Consumer Expenditure Survey?",
        item_type="MULTIPLE_CHOICE",
        options=["Stratified random sampling", "Arbitrary convenience sampling"],
        correct_answer="Stratified random sampling",
        competency_id=comp.id,
        subskill_id=sub.id,
        difficulty="medium",
        provenance="[TEST]",
        rubric={"type": "EXACT_MATCH"},
    )
    # Must not raise
    validate_assessment_candidate(session, valid_cand)

    # Invalid: correct answer not in options
    bad_cand = CandidateAssessment(
        prompt="What is the standard procedure?",
        item_type="MULTIPLE_CHOICE",
        options=["Option A", "Option B"],
        correct_answer="Missing Option",
        competency_id=comp.id,
        subskill_id=sub.id,
        difficulty="medium",
        provenance="[TEST]",
        rubric={},
    )
    with pytest.raises(CandidateAssessmentValidationError):
        validate_assessment_candidate(session, bad_cand)
