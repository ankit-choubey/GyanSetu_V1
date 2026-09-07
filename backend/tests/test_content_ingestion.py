from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

os.environ.setdefault("JWT_SECRET", "content-ingestion-test-secret-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from app.main import app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.user import User
from app.routers import content as content_router
from app.services.content_ingestion import ContentIngestionError, ContentIngestionService
from app.services.evening_interfaces import DocumentProcessResult


@pytest.fixture
def database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as db:
        role = Role(name="Content Admin")
        db.add(role)
        db.flush()
        competency = Competency(name="Data Quality", role_id=role.id)
        admin = User(
            email="content-admin@example.com",
            full_name="Content Admin",
            password_hash="hashed",
            role_id=role.id,
        )
        db.add_all([competency, admin])
        db.flush()
        subskill = SubSkill(name="Validation", competency_id=competency.id)
        db.add(subskill)
        db.flush()
        db.add(RoleCompetency(role_id=role.id, competency_id=competency.id))
        db.commit()
        yield db, admin, competency, subskill
    engine.dispose()


def _pages(text="Stratified sampling validates data quality."):
    return [{"page": 1, "content_type": "text", "text": text, "tables": [], "ocr_used": False}]


def _mapping(subskills=("Validation",)):
    return [{
        "concept": "Validation",
        "competency": "Data Quality",
        "subskills": list(subskills),
        "confidence": 0.9,
        "rationale": "The content supports validation.",
    }]


def _mcq(question="Which validation step is required?", difficulty="medium"):
    return {
        "question": question,
        "options": [
            "Check documented field ranges",
            "Ignore invalid values",
            "Delete all metadata",
            "Publish without review",
        ],
        "correct_answer": "A",
        "explanation": "The source supports checking documented ranges.",
        "competency": "Data Quality",
        "difficulty": difficulty,
    }


def _run(service, db, filename="training.pdf"):
    db.rollback()
    with db.begin():
        return service.process(filename, "application/pdf", b"document bytes")


def _patch_valid_pipeline(monkeypatch, generated=None, mappings=None, pages=None, score=0.8):
    import app.services.content_ingestion as ingestion

    monkeypatch.setattr(ingestion, "process_document_structured", lambda path: pages or _pages())
    monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [{"concept": "Validation"}])
    monkeypatch.setattr(ingestion, "map_competencies", lambda concepts: mappings or _mapping())
    monkeypatch.setattr(ingestion, "generate_mcqs", lambda content, competency, num_questions, difficulty: generated or [_mcq()])
    monkeypatch.setattr(ingestion, "validate_mcqs", lambda mcqs, content: [
        {"valid": True, "issues": [], "checks": {}} for _ in mcqs
    ])
    monkeypatch.setattr(ingestion, "score_mcq_quality", lambda mcq, content: {**mcq, "quality_score": score})


def test_successful_upload_persists_trusted_shared_item(database, monkeypatch):
    db, _, competency, subskill = database
    _patch_valid_pipeline(monkeypatch)

    result = _run(ContentIngestionService(db), db)
    item = db.execute(select(AssessmentItem)).scalar_one()

    assert result.trusted is True
    assert result.successful_pages == (1,)
    assert item.user_id is None
    assert item.competency_id == competency.id
    assert item.subskill_id == subskill.id
    assert json.loads(item.options_json) == [
        "A. Check documented field ranges",
        "B. Ignore invalid values",
        "C. Delete all metadata",
        "D. Publish without review",
    ]
    assert item.correct_option == "A"
    assert item.difficulty == "medium"
    assert item.source_reference.startswith("gyansetu-qb:")


def test_single_subskill_mapping_generates_once(database, monkeypatch):
    db, _, _, subskill = database
    calls = []
    _patch_valid_pipeline(monkeypatch)
    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(
        ingestion,
        "generate_mcqs",
        lambda content, competency, num_questions, difficulty: (
            calls.append((competency, num_questions, difficulty)) or [_mcq()]
        ),
    )

    _run(ContentIngestionService(db), db)

    assert calls == [("Data Quality", 5, "medium")]
    assert db.execute(select(AssessmentItem)).scalar_one().subskill_id == subskill.id


def test_temporary_file_is_cleaned_after_processing(database, monkeypatch):
    db, _, _, _ = database
    paths = []

    def process(path):
        paths.append(path)
        assert Path(path).suffix == ".pdf"
        assert Path(path).exists()
        return _pages()

    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(ingestion, "process_document_structured", process)
    monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [{"concept": "Validation"}])
    monkeypatch.setattr(ingestion, "map_competencies", lambda concepts: _mapping())
    monkeypatch.setattr(ingestion, "generate_mcqs", lambda *args: [_mcq()])
    monkeypatch.setattr(ingestion, "validate_mcqs", lambda mcqs, content: [{"valid": True}])
    monkeypatch.setattr(ingestion, "score_mcq_quality", lambda mcq, content: {**mcq, "quality_score": 0.8})

    _run(ContentIngestionService(db), db)
    assert paths and not Path(paths[0]).exists()


def test_invalid_mcq_is_not_persisted(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch)
    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(ingestion, "validate_mcqs", lambda mcqs, content: [{"valid": False}])

    with pytest.raises(ContentIngestionError, match="NO_VALID_MCQ"):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_quality_threshold_rejects_low_quality_mcq(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch, score=0.54)

    with pytest.raises(ContentIngestionError, match="NO_VALID_MCQ"):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_mixed_batch_persists_only_accepted_item(database, monkeypatch):
    db, _, _, _ = database
    generated = [_mcq("Accepted question"), _mcq("Rejected question")]
    _patch_valid_pipeline(monkeypatch, generated=generated)
    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(ingestion, "validate_mcqs", lambda mcqs, content: [
        {"valid": True}, {"valid": False}
    ])

    _run(ContentIngestionService(db), db)
    items = db.execute(select(AssessmentItem)).scalars().all()
    assert [item.question_text for item in items] == ["Accepted question"]


def test_taxonomy_mismatch_rolls_back_entire_upload(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch, mappings=_mapping(("Unknown subskill",)))

    with pytest.raises(ContentIngestionError, match="Invalid subskill reference"):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_multi_subskill_mapping_fails_before_generation_and_rolls_back(database, monkeypatch):
    db, _, _, _ = database
    paths = []
    import app.services.content_ingestion as ingestion

    def process(path):
        paths.append(path)
        return _pages()

    monkeypatch.setattr(ingestion, "process_document_structured", process)
    monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [{"concept": "Validation"}])
    monkeypatch.setattr(ingestion, "map_competencies", lambda concepts: _mapping(("Validation", "Other")))
    monkeypatch.setattr(
        ingestion,
        "generate_mcqs",
        lambda *args: pytest.fail("ambiguous mapping reached MCQ generation"),
    )

    with pytest.raises(ContentIngestionError, match="AMBIGUOUS_SUBSKILL_MAPPING"):
        _run(ContentIngestionService(db), db)

    assert db.execute(select(AssessmentItem)).all() == []
    assert paths and not Path(paths[0]).exists()


def test_zero_subskill_mapping_fails_without_inventing_taxonomy(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch, mappings=_mapping(()))
    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(
        ingestion,
        "generate_mcqs",
        lambda *args: pytest.fail("zero-subskill mapping reached MCQ generation"),
    )

    with pytest.raises(ContentIngestionError, match="MISSING_SUBSKILL_MAPPING"):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_duplicate_upload_is_idempotent(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch)
    service = ContentIngestionService(db)

    _run(service, db)
    _run(service, db)

    assert len(db.execute(select(AssessmentItem)).scalars().all()) == 1


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("no_concepts", "NO_CONCEPTS"),
        ("no_mappings", "NO_COMPETENCY_MAPPINGS"),
        ("no_valid", "NO_VALID_MCQ"),
        ("extraction_failure", "CONTENT_PROCESSING_FAILED"),
    ],
)
def test_processing_failures_persist_nothing(database, monkeypatch, case, expected):
    db, _, _, _ = database
    import app.services.content_ingestion as ingestion
    monkeypatch.setattr(ingestion, "process_document_structured", lambda path: _pages())
    if case == "no_concepts":
        monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [])
    elif case == "no_mappings":
        monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [{"concept": "Validation"}])
        monkeypatch.setattr(ingestion, "map_competencies", lambda concepts: [])
    elif case == "no_valid":
        _patch_valid_pipeline(monkeypatch)
        monkeypatch.setattr(ingestion, "validate_mcqs", lambda mcqs, content: [{"valid": False}])
    else:
        monkeypatch.setattr(ingestion, "process_document_structured", lambda path: (_ for _ in ()).throw(RuntimeError("ML failed")))

    with pytest.raises(ContentIngestionError, match=expected):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_ml_exception_cleans_temporary_file(database, monkeypatch):
    db, _, _, _ = database
    paths = []
    import app.services.content_ingestion as ingestion

    def process(path):
        paths.append(path)
        return _pages()

    monkeypatch.setattr(ingestion, "process_document_structured", process)
    monkeypatch.setattr(ingestion, "extract_concepts", lambda content: (_ for _ in ()).throw(RuntimeError("ML failed")))

    with pytest.raises(ContentIngestionError, match="CONTENT_PROCESSING_FAILED"):
        _run(ContentIngestionService(db), db)
    assert paths and not Path(paths[0]).exists()
    assert db.execute(select(AssessmentItem)).all() == []


def test_taxonomy_exception_cleans_temporary_file(database, monkeypatch):
    db, _, _, _ = database
    paths = []
    import app.services.content_ingestion as ingestion

    def process(path):
        paths.append(path)
        return _pages()

    monkeypatch.setattr(ingestion, "process_document_structured", process)
    monkeypatch.setattr(ingestion, "extract_concepts", lambda content: [{"concept": "Validation"}])
    monkeypatch.setattr(ingestion, "map_competencies", lambda concepts: _mapping(("Unknown subskill",)))

    with pytest.raises(ContentIngestionError, match="Invalid subskill reference"):
        _run(ContentIngestionService(db), db)
    assert paths and not Path(paths[0]).exists()
    assert db.execute(select(AssessmentItem)).all() == []


def test_partial_extraction_is_not_trusted(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch, pages=[
        _pages()[0],
        {"page": 2, "content_type": "ocr_failed", "text": "", "tables": [], "ocr_used": False},
    ])

    with pytest.raises(ContentIngestionError, match="DOCUMENT_EXTRACTION_INCOMPLETE"):
        _run(ContentIngestionService(db), db)
    assert db.execute(select(AssessmentItem)).all() == []


def test_ppt_is_rejected_before_ml(database, monkeypatch):
    db, _, _, _ = database
    import app.services.content_ingestion as ingestion
    called = False

    def process(path):
        nonlocal called
        called = True
        return _pages()

    monkeypatch.setattr(ingestion, "process_document_structured", process)
    with pytest.raises(ContentIngestionError, match="UNSUPPORTED_FORMAT"):
        _run(ContentIngestionService(db), db, "training.ppt")
    assert called is False


def test_pptx_is_supported(database, monkeypatch):
    db, _, _, _ = database
    _patch_valid_pipeline(monkeypatch)
    result = _run(ContentIngestionService(db), db, "training.pptx")
    assert result.trusted is True


def test_empty_content_is_rejected(database):
    db, _, _, _ = database
    with pytest.raises(ContentIngestionError, match="EMPTY_CONTENT"):
        db.rollback()
        with db.begin():
            ContentIngestionService(db).process("training.pdf", "application/pdf", b"")


def test_upload_route_preserves_admin_boundary_and_answer_key_safety(database):
    db, admin, _, _ = database
    app.dependency_overrides[content_router.get_current_admin] = lambda: admin
    app.dependency_overrides[content_router.get_db] = lambda: db
    app.dependency_overrides[content_router.get_document_processor] = lambda: _ResponseOnlyProcessor()
    try:
        response = TestClient(app).post(
            "/api/content/upload",
            files={"file": ("training.pdf", b"pdf bytes", "application/pdf")},
        )
    finally:
        app.dependency_overrides.pop(content_router.get_current_admin, None)
        app.dependency_overrides.pop(content_router.get_db, None)
        app.dependency_overrides.pop(content_router.get_document_processor, None)

    assert response.status_code == 200
    assert "correct_option" not in response.text
    assert "question_text" not in response.text


def test_upload_route_rejects_non_admin(database):
    db, _, _, _ = database

    def reject_admin():
        raise HTTPException(status_code=403, detail="Administrator access required")

    app.dependency_overrides[content_router.get_current_admin] = reject_admin
    app.dependency_overrides[content_router.get_db] = lambda: db
    try:
        response = TestClient(app).post(
            "/api/content/upload",
            files={"file": ("training.pdf", b"pdf bytes", "application/pdf")},
        )
    finally:
        app.dependency_overrides.pop(content_router.get_current_admin, None)
        app.dependency_overrides.pop(content_router.get_db, None)

    assert response.status_code == 403


def test_upload_route_rejects_ppt_before_provider(database):
    db, admin, _, _ = database

    class FailingProcessor:
        def process(self, filename, content_type, content):
            raise AssertionError("unsupported .ppt reached the provider")

    app.dependency_overrides[content_router.get_current_admin] = lambda: admin
    app.dependency_overrides[content_router.get_db] = lambda: db
    app.dependency_overrides[content_router.get_document_processor] = lambda: FailingProcessor()
    try:
        response = TestClient(app).post(
            "/api/content/upload",
            files={"file": ("training.ppt", b"ppt bytes", "application/vnd.ms-powerpoint")},
        )
    finally:
        app.dependency_overrides.pop(content_router.get_current_admin, None)
        app.dependency_overrides.pop(content_router.get_db, None)
        app.dependency_overrides.pop(content_router.get_document_processor, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "UNSUPPORTED_FORMAT"


class _ResponseOnlyProcessor:
    def process(self, filename, content_type, content):
        return DocumentProcessResult(
            status="success",
            trusted=True,
            coverage=1.0,
            successful_pages=(1,),
        )
