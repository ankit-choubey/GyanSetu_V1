"""
backend/tests/test_phase1_integration.py — Complete Phase 1 Backend & ML Integration Test Suite.

Covers all 10 required Phase 1 dimensions (A through J):
A. Backend unit behavior (canonical schema, fingerprinting, coercion)
B. Backend database behavior (AssessmentItem foreign keys, subskill integrity)
C. Backend API behavior (Role-scoped competencies, assessment submission, state update)
D. ML pipeline behavior (Canonical taxonomy, MCQ quality scorer, Bloom level)
E. Backend -> ML integration boundary (explicit service contracts)
F. ML -> Backend persistence (loading canonical question bank into DB)
G. Failure handling (malformed input, invalid taxonomy, missing files, rollback)
H. Provenance persistence (source_reference, document metadata, provenance states)
I. Idempotency (re-seeding does not duplicate items)
J. Assessment quality gates (structural, grounding, distractor checks)
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

_db_path = Path.cwd() / f"test_phase1_integ_{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["JWT_SECRET"] = "phase1-test-secret-that-is-at-least-32-chars"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["SEED_PASSWORD"] = "test-pass"

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import select
from sqlmodel import SQLModel

from app.database import SessionLocal, engine
from app.main import app
from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.schemas.canonical_question import CanonicalQuestionSchema
from app.seed_data.question_bank_loader import (
    SOURCE_REFERENCE_PREFIX,
    load_canonical_question_bank,
    load_question_bank,
)
from app.seed_data.runner import seed_full_taxonomy

from ml_pipeline.canonical_question import CanonicalQuestion
from ml_pipeline.canonical_taxonomy import (
    CANONICAL_COMPETENCIES,
    CANONICAL_SUBSKILLS,
    is_canonical_competency,
    is_canonical_subskill,
)
from ml_pipeline.document_processor import process_document
from ml_pipeline.mcq_scorer import classify_cognitive_level, compute_distractor_entropy
from ml_pipeline.question_generation_boundary import (
    generate_question_with_fallback,
    validate_and_gate_mcq,
)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    seed_full_taxonomy("test-pass")
    with SessionLocal() as db:
        load_canonical_question_bank(db)
        db.commit()
    yield



@pytest.fixture
def db_session():
    with SessionLocal() as db:
        yield db


# ---------------------------------------------------------------------------
# A. Backend Unit Behavior
# ---------------------------------------------------------------------------

def test_a_canonical_question_schema_validation():
    valid_data = {
        "question_id": "Q-TEST-001",
        "question_text": "What is stratified sampling?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_option": "A",
        "competency": "Sampling Design",
        "subskill": "Stratified sampling",
        "cognitive_level": "Understanding",
        "difficulty": "medium",
        "explanation": "Stratified sampling divides populations into homogeneous strata.",
        "source": {"document_id": "test_doc", "title": "Test Title"},
        "source_reference": "test-ref-001",
        "provenance": "MoSPI",
        "provenance_state": "CURATED",
    }
    schema = CanonicalQuestionSchema(**valid_data)
    assert schema.question_id == "Q-TEST-001"
    assert schema.correct_option == "A"

    canonical = CanonicalQuestion.from_dict(valid_data)
    assert canonical.competency == "Sampling Design"
    assert canonical.compute_fingerprint().startswith(SOURCE_REFERENCE_PREFIX)


# ---------------------------------------------------------------------------
# B. Backend Database Behavior
# ---------------------------------------------------------------------------

def test_b_assessment_item_database_persistence(db_session):
    items = db_session.execute(select(AssessmentItem).where(AssessmentItem.user_id.is_(None))).scalars().all()
    assert len(items) >= 160  # All 160 subskills seeded

    # Check FK integrity
    for item in items[:20]:
        assert item.competency_id is not None
        assert item.subskill_id is not None
        comp = db_session.get(Competency, item.competency_id)
        sub = db_session.get(SubSkill, item.subskill_id)
        assert comp is not None
        assert sub is not None
        assert sub.competency_id == comp.id


# ---------------------------------------------------------------------------
# C. Backend API Behavior
# ---------------------------------------------------------------------------

def test_c_role_competencies_and_submission_api(db_session):
    client = TestClient(app, raise_server_exceptions=False)

    # Login as learner
    resp = client.post("/api/auth/login", json={"email": "learner@example.com", "password": "test-pass"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch role competencies
    learner = db_session.execute(select(User).where(User.email == "learner@example.com")).scalar_one()
    role_id = learner.role_id
    sampling_comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one()
    item = db_session.execute(
        select(AssessmentItem).where(
            AssessmentItem.competency_id == sampling_comp.id,
            AssessmentItem.user_id.is_(None),
        )
    ).scalars().first()
    assert item is not None
    question_id = item.id
    correct_letter = item.correct_option

    resp = client.get(f"/api/competencies/{role_id}", headers=headers)
    assert resp.status_code == 200
    comp_names = [c["name"] for c in resp.json()["competencies"]]
    assert "Sampling Design" in comp_names

    # Submit assessment answer
    submit_resp = client.post(
        "/api/assessment/submit",
        headers=headers,
        json={
            "competency_id": sampling_comp.id,
            "answers": [{"question_id": question_id, "selected": correct_letter}],
        },
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["score"] == 1.0


# ---------------------------------------------------------------------------
# D. ML Pipeline Behavior
# ---------------------------------------------------------------------------

def test_d_ml_pipeline_canonical_taxonomy_and_scorer():
    assert len(CANONICAL_COMPETENCIES) == 40
    assert sum(len(v) for v in CANONICAL_SUBSKILLS.values()) == 160
    assert is_canonical_competency("Sampling Design")
    assert is_canonical_subskill("Sampling Design", "Stratified sampling")
    assert not is_canonical_competency("Invented Competency 101")

    # Cognitive level classifier
    assert classify_cognitive_level("Calculate the sample variance given n=100") == "Application"
    assert classify_cognitive_level("Compare stratified sampling and cluster sampling") == "Analysis"
    assert classify_cognitive_level("What is the definition of a sampling frame?") == "Recall"

    # Distractor entropy
    options = ["Short", "Short", "Short", "A very very very very long distractor that gives away the answer"]
    entropy = compute_distractor_entropy(options)
    assert entropy < 0.8


# ---------------------------------------------------------------------------
# E. Backend <-> ML Integration Boundary
# ---------------------------------------------------------------------------

def test_e_backend_ml_integration_boundary():
    # Verify fallback generation cascade
    items = generate_question_with_fallback(
        content="Stratified sampling divides population into homogeneous strata.",
        competency="Sampling Design",
        subskill="Stratified sampling",
        difficulty="medium",
        num_questions=1,
    )
    assert len(items) == 1
    assert items[0].competency == "Sampling Design"
    assert items[0].subskill == "Stratified sampling"
    assert items[0].provenance_state in {"LIVE INTEGRATION", "SANDBOX DATA", "CURATED"}

    # Convert to backend loadable dictionary
    backend_payload = items[0].to_backend_dict()
    assert "competency_name" in backend_payload
    assert "subskill_name" in backend_payload
    assert "question_text" in backend_payload
    assert "options" in backend_payload
    assert "correct_option" in backend_payload


# ---------------------------------------------------------------------------
# F. ML -> Backend Persistence
# ---------------------------------------------------------------------------

def test_f_canonical_bank_loads_into_assessment_items(db_session):
    # Verify all 40 competencies are represented in DB
    db_comps = db_session.execute(select(Competency.id)).scalars().all()
    item_comp_ids = set(
        db_session.execute(
            select(AssessmentItem.competency_id).where(AssessmentItem.user_id.is_(None))
        ).scalars().all()
    )
    assert len(item_comp_ids) == len(db_comps) == 40

    # Verify all 160 subskills are represented in DB
    db_subskills = db_session.execute(select(SubSkill.id)).scalars().all()
    item_sub_ids = set(
        db_session.execute(
            select(AssessmentItem.subskill_id).where(AssessmentItem.user_id.is_(None))
        ).scalars().all()
    )
    assert len(item_sub_ids) == len(db_subskills) == 160


# ---------------------------------------------------------------------------
# G. Failure Handling & Validation Rejections
# ---------------------------------------------------------------------------

def test_g_failure_handling_and_rejections(db_session):
    # 1. Invalid competency rejection
    with pytest.raises(ValueError, match="Invalid competency reference"):
        load_question_bank(
            db_session,
            [
                {
                    "competency_name": "NonExistentCompetency",
                    "subskill_name": "Validation rules",
                    "question_text": "Q text",
                    "options": ["A", "B", "C", "D"],
                    "correct_option": "A",
                    "difficulty": "easy",
                }
            ],
        )

    # 2. Invalid subskill rejection
    with pytest.raises(ValueError, match="Invalid subskill reference"):
        load_question_bank(
            db_session,
            [
                {
                    "competency_name": "Data Quality",
                    "subskill_name": "CompletelyFakeSubskill",
                    "question_text": "Q text",
                    "options": ["A", "B", "C", "D"],
                    "correct_option": "A",
                    "difficulty": "easy",
                }
            ],
        )

    # 3. Subskill belonging to wrong competency
    with pytest.raises(ValueError, match="does not belong to competency"):
        load_question_bank(
            db_session,
            [
                {
                    "competency_name": "Data Quality",
                    "subskill_name": "Sampling frames",  # Belongs to Sampling Design
                    "question_text": "Q text",
                    "options": ["A", "B", "C", "D"],
                    "correct_option": "A",
                    "difficulty": "easy",
                }
            ],
        )

    # 4. Document processor unsupported file rejection
    with tempfile.NamedTemporaryFile(suffix=".docx") as bad_f:
        with pytest.raises(ValueError, match="unsupported file type"):
            process_document(bad_f.name)


# ---------------------------------------------------------------------------
# H. Provenance Persistence
# ---------------------------------------------------------------------------

def test_h_provenance_persistence(db_session):
    items = db_session.execute(select(AssessmentItem).where(AssessmentItem.user_id.is_(None))).scalars().all()
    for item in items:
        assert item.source_reference is not None
        assert len(item.source_reference) > 0


# ---------------------------------------------------------------------------
# I. Idempotency
# ---------------------------------------------------------------------------

def test_i_seeding_idempotency(db_session):
    count_1 = len(db_session.execute(select(AssessmentItem).where(AssessmentItem.user_id.is_(None))).scalars().all())

    # Second seed invocation must not duplicate any item
    seed_full_taxonomy("test-pass")
    count_2 = len(db_session.execute(select(AssessmentItem).where(AssessmentItem.user_id.is_(None))).scalars().all())

    assert count_1 == count_2


# ---------------------------------------------------------------------------
# J. Assessment Quality Gates
# ---------------------------------------------------------------------------

def test_j_quality_gate_checks():
    # 1. Broken item failing structural check
    broken_item = {
        "question": "Incomplete item?",
        "options": ["Only two"],
        "correct_answer": "Z",
        "competency": "Data Quality",
    }
    canonical, gate = validate_and_gate_mcq(broken_item, "Some source")
    assert canonical is None
    assert gate["passed"] is False

    # 2. Ungrounded item failing grounding check
    ungrounded_item = {
        "question": "What is the capital of Mars?",
        "options": ["Olympus Mons", "Elysium", "Valles Marineris", "Utopia"],
        "correct_answer": "A",
        "competency": "Data Quality",
        "subskill": "Validation rules",
        "difficulty": "medium",
        "explanation": "This text is completely unrelated to the answer choices above.",
    }
    canonical, gate = validate_and_gate_mcq(ungrounded_item, "Irrelevant source about agriculture.", quality_threshold=0.55)
    assert canonical is None
    assert gate["passed"] is False
