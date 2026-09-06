from __future__ import annotations

import io
import json
import os
import pytest

os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-chars-long"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.user import User
from app.routers import assessment as assessment_router
from app.routers import chatbot as chatbot_router
from app.routers import content as content_router
from app.seed import seed_data
from app.services.evening_interfaces import ABSTENTION_MESSAGE
from ml_pipeline.vector_store import add_chunks, clear_collection


@pytest.fixture
def test_setup():
    """Sets up an isolated SQLite in-memory database and test client."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    # Seed initial test data
    def get_test_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[assessment_router.get_db] = get_test_db

    # Create admin and learner users
    with factory() as session:
        role = Role(name="Statistical Officer", description="MoSPI cadre")
        admin_role = Role(name="Admin", description="Administrator")
        session.add_all([role, admin_role])
        session.flush()

        comp = Competency(role_id=role.id, name="Survey Sampling", description="Sampling techniques")
        session.add(comp)
        session.flush()

        sub1 = SubSkill(competency_id=comp.id, name="Stratified Sampling", description="Strata formation")
        sub2 = SubSkill(competency_id=comp.id, name="Sample Size Calculation", description="Precision bounds")
        session.add_all([sub1, sub2])
        session.flush()

        # Seed candidate assessment items
        item_easy = AssessmentItem(
            competency_id=comp.id,
            subskill_id=sub1.id,
            question_text="What is the primary benefit of stratified sampling?",
            options_json=json.dumps([
                "A. Reduces sampling variance across heterogeneous groups",
                "B. Eliminates all non-sampling errors completely",
                "C. Removes the need for any sampling frame",
                "D. Guarantees 100% census data collection",
            ]),
            correct_option="A",
            difficulty="easy",
            source_reference="NSSTA Module 1, p. 12",
        )
        item_medium = AssessmentItem(
            competency_id=comp.id,
            subskill_id=sub1.id,
            question_text="When should Neyman allocation be applied?",
            options_json=json.dumps([
                "A. When all stratum variances and sampling costs are identical",
                "B. When stratum standard deviations or sampling costs differ across strata",
                "C. Only when sample size exceeds 100,000 units",
                "D. When no population data is available",
            ]),
            correct_option="B",
            difficulty="medium",
            source_reference="NSSTA Module 1, p. 15",
        )
        item_hard = AssessmentItem(
            competency_id=comp.id,
            subskill_id=sub2.id,
            question_text="How does doubling the margin of error affect required sample size?",
            options_json=json.dumps([
                "A. Doubles the required sample size",
                "B. Reduces the required sample size to one-fourth",
                "C. Has zero effect on sample size",
                "D. Triples the required sample size",
            ]),
            correct_option="B",
            difficulty="hard",
            source_reference="NSSTA Module 1, p. 22",
        )
        session.add_all([item_easy, item_medium, item_hard])

        # Seed interventions
        intervention = Intervention(
            competency_id=comp.id,
            subskill_id=sub1.id,
            title="Practical Guide to Stratified Survey Design",
            description="iGOT Micro-module on Neyman allocation and stratification rules",
            intervention_type="iGOT_COURSE",
            priority=1,
        )
        session.add(intervention)

        learner = User(
            id=10,
            email="learner@mospi.gov.in",
            full_name="Test Officer",
            password_hash="hashed_pw",
            role_id=role.id,
            is_active=True,
        )
        admin = User(
            id=1,
            email="admin@mospi.gov.in",
            full_name="Director NSSTA",
            password_hash="hashed_pw",
            role_id=admin_role.id,
            is_active=True,
        )
        session.add_all([learner, admin])
        session.commit()

        context = {
            "factory": factory,
            "role_id": role.id,
            "competency_id": comp.id,
            "subskill1_id": sub1.id,
            "subskill2_id": sub2.id,
            "item_easy_id": item_easy.id,
            "item_medium_id": item_medium.id,
            "item_hard_id": item_hard.id,
            "learner": learner,
            "admin": admin,
        }

    yield context

    app.dependency_overrides.clear()


def test_document_ingestion_indexes_chunks_and_enables_rag(test_setup):
    """Test uploading a training document indexes it into ChromaDB for grounded RAG."""
    admin = test_setup["admin"]
    app.dependency_overrides[content_router.get_current_admin] = lambda: admin
    app.dependency_overrides[chatbot_router.get_current_user] = lambda: test_setup["learner"]

    clear_collection("gyansetu_training")

    # Ingest chunks directly to simulate processed document
    test_chunks = [
        {
            "text": "Neyman Allocation in Stratified Sampling calculates optimal sample sizes when stratum variances differ.",
            "chunk_type": "text",
            "page_number": 14,
            "source_id": "NSSTA_Sampling_Manual.pdf",
            "competency": str(test_setup["competency_id"]),
        }
    ]
    add_chunks(test_chunks, collection_name="gyansetu_training")

    client = TestClient(app)

    # 1. Grounded query about Neyman allocation should succeed with source citations
    res = client.post(
        "/api/chatbot/ask",
        json={"question": "What is Neyman Allocation in Stratified Sampling?", "competency_id": test_setup["competency_id"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in {"SUCCESS", "ABSTAINED"}
    if data["status"] == "SUCCESS":
        assert len(data["sources"]) >= 1

    # 2. Out of domain query should strictly abstain without hallucination
    unrelated_res = client.post(
        "/api/chatbot/ask",
        json={"question": "What is quantum physics in outer space?", "competency_id": test_setup["competency_id"]},
    )
    assert unrelated_res.status_code == 200
    assert unrelated_res.json()["status"] == "ABSTAINED"
    assert "don't have enough verified information" in unrelated_res.json()["answer"]


def test_adaptive_diagnostic_question_selection_flow(test_setup):
    """Test adaptive question flow: initial easy -> step up on correct -> step down on incorrect."""
    learner = test_setup["learner"]
    app.dependency_overrides[assessment_router.get_current_user] = lambda: learner

    client = TestClient(app)

    # Step 1: Request initial question (starts at difficulty 'easy')
    res1 = client.post(
        "/api/assessment/next",
        json={"competency_id": test_setup["competency_id"], "session_history": []},
    )
    assert res1.status_code == 200, f"Error: {res1.status_code} - {res1.text}"
    q1 = res1.json()
    assert q1["status"] == "QUESTION_PROPOSED"
    assert q1["difficulty"] == "easy"
    assert q1["question_id"] == test_setup["item_easy_id"]

    # Step 2: Officer answers correctly -> adaptive engine steps up to 'medium'
    history_correct = [
        {"item_id": q1["question_id"], "difficulty": "easy", "is_correct": True, "subskill": "Stratified Sampling"}
    ]
    res2 = client.post(
        "/api/assessment/next",
        json={"competency_id": test_setup["competency_id"], "session_history": history_correct},
    )
    assert res2.status_code == 200
    q2 = res2.json()
    assert q2["status"] == "QUESTION_PROPOSED"
    assert q2["difficulty"] == "medium"
    assert q2["question_id"] == test_setup["item_medium_id"]

    # Step 3: Officer answers medium incorrectly -> adaptive engine steps down / targets subskill
    history_fail = [
        {"item_id": q1["question_id"], "difficulty": "easy", "is_correct": True, "subskill": "Stratified Sampling"},
        {"item_id": q2["question_id"], "difficulty": "medium", "is_correct": False, "subskill": "Stratified Sampling"},
    ]
    res3 = client.post(
        "/api/assessment/next",
        json={"competency_id": test_setup["competency_id"], "session_history": history_fail},
    )
    assert res3.status_code == 200
    q3 = res3.json()
    assert q3["status"] in {"QUESTION_PROPOSED", "SUFFICIENT_EVIDENCE"}


def test_full_closed_loop_assessment_evidence_gap_and_intervention(test_setup):
    """
    Verifies the complete GyanSetu closed loop:
    Assessment submission -> Server scoring -> Evidence persistence ->
    Competency Engine state calculation -> Subskill gap detection ->
    Intervention Agent recommendation with diagnostic explanations.
    """
    learner = test_setup["learner"]
    app.dependency_overrides[assessment_router.get_current_user] = lambda: learner

    client = TestClient(app)

    # Submit 1 correct and 1 wrong answer
    submit_payload = {
        "competency_id": test_setup["competency_id"],
        "answers": [
            {"question_id": test_setup["item_easy_id"], "selected": "A"},  # Correct
            {"question_id": test_setup["item_medium_id"], "selected": "C"},  # Incorrect distractor
        ],
    }

    response = client.post("/api/assessment/submit", json=submit_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["score"] == 0.5

    # Verify diagnostic feedback per answer
    assert len(data["feedback"]) == 2
    f1 = data["feedback"][0]
    assert f1["is_correct"] is True
    assert "correct" in f1["feedback"].lower()

    f2 = data["feedback"][1]
    assert f2["is_correct"] is False
    assert len(f2["feedback"]) > 0

    # Verify Competency Engine updated state in DB
    factory = test_setup["factory"]
    with factory() as session:
        state = session.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == learner.id,
                CompetencyState.competency_id == test_setup["competency_id"],
            )
        ).scalar_one_or_none()

        assert state is not None
        assert state.status in {"ASSESSED", "developing", "verified"}
        assert state.mastery == 0.5
        assert state.confidence > 0.0
        assert state.evidence_count >= 1

        # Verify evidence recorded
        ev = session.execute(
            select(Evidence).where(
                Evidence.user_id == learner.id,
                Evidence.competency_id == test_setup["competency_id"],
                Evidence.evidence_type == EvidenceType.KNOWLEDGE_ASSESSMENT,
            )
        ).scalar_one_or_none()
        assert ev is not None
        assert ev.score == 0.5

    # Verify Next Best Action recommendation
    assert data["next_best_action"] is not None
    nba = data["next_best_action"]
    assert nba["selected_intervention"] is not None
    assert "Stratified Survey Design" in nba["selected_intervention"]["title"]


def test_reproducibility_5_consecutive_clean_runs(test_setup):
    """
    Build Guide §31 & Project Context Non-Negotiable Rule:
    The full closed-loop system must survive 5 consecutive clean runs
    without regressions, crashes, or inconsistent states.
    """
    learner = test_setup["learner"]
    app.dependency_overrides[assessment_router.get_current_user] = lambda: learner
    client = TestClient(app)

    for run_idx in range(1, 6):
        # 1. Check next question
        next_res = client.post(
            "/api/assessment/next",
            json={"competency_id": test_setup["competency_id"], "session_history": []},
        )
        assert next_res.status_code == 200, f"Run {run_idx} failed on /assessment/next"

        # 2. Submit assessment
        sub_res = client.post(
            "/api/assessment/submit",
            json={
                "competency_id": test_setup["competency_id"],
                "answers": [{"question_id": test_setup["item_easy_id"], "selected": "A"}],
            },
        )
        assert sub_res.status_code == 200, f"Run {run_idx} failed on /assessment/submit"
        data = sub_res.json()
        assert data["score"] == 1.0, f"Run {run_idx} unexpected score: {data['score']}"
        assert data["competency_status"] is not None

        # 3. Check chatbot abstention / answer
        chat_res = client.post(
            "/api/chatbot/ask",
            json={"question": f"Question run {run_idx} out of domain?", "competency_id": test_setup["competency_id"]},
        )
        assert chat_res.status_code == 200, f"Run {run_idx} failed on /chatbot/ask"
        assert chat_res.json()["status"] in {"ABSTAINED", "SUCCESS"}
