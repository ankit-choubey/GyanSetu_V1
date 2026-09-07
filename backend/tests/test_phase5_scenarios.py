from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.practical import AttemptStatus, PracticalAttempt, PracticalTask
from app.models.user import User
from app.seed_data.practical_scenario_loader import PRACTICAL_TASKS_DATA, seed_practical_tasks
from app.services.next_best_action_service import NextBestActionService
from app.services.orchestrator import recalculate_competency_state
from app.services.practical.deterministic_evaluator import DeterministicEvaluator
from app.services.practical.llm_evaluator import LLMEvaluator
from app.utils.security import create_access_token, hash_password


@pytest.fixture(scope="module", autouse=True)
def setup_module_data():
    from sqlmodel import SQLModel
    from app.database import engine, SessionLocal
    from app.models.competency import Role
    from app.seed_data.runner import seed_full_taxonomy
    from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
    
    SQLModel.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.execute(select(Role)).scalars().first():
            seed_full_taxonomy("test-pass")
        seed_intervention_catalog(db)
        seed_practical_tasks(db)
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_learner(db_session: Session) -> User:
    email = f"phase5.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("test-password-phase5"),
        full_name="Phase 5 Test Officer",
        is_active=True,
    )
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    if role:
        user.role_id = role.id
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_learner(db_session: Session) -> User:
    email = f"phase5.other.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("test-password-phase5"),
        full_name="Other Test Officer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# SCENARIO A: Practical Task Seeding & Schema Integrity
# ==============================================================================
def test_scenario_a_seeding_and_schema_integrity(db_session: Session, client: TestClient):
    tasks = db_session.execute(select(PracticalTask)).scalars().all()
    assert len(tasks) >= 5, "All 5 authentic MoSPI practical scenarios must be seeded."

    task_ids = {t.task_id for t in tasks}
    expected_ids = {
        "TASK-MOSPI-SAMP-01",
        "TASK-MOSPI-SAMP-02",
        "TASK-MOSPI-CPI-01",
        "TASK-MOSPI-QUAL-01",
        "TASK-MOSPI-MISC-01",
    }
    assert expected_ids.issubset(task_ids)

    for task in tasks:
        assert task.provenance == "[CURATED:SIMULATION]"
        assert task.source == "MOSPI_SIMULATION"
        assert task.competency_id is not None
        assert task.rubric_version.startswith("v1.0")
        assert "Official-Statistics-aligned simulated practical scenario." in task.scenario_context
        rubric = task.get_rubric()
        assert "dimensions" in rubric
        assert "passing_score" in rubric

    response = client.get("/api/practical/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


# ==============================================================================
# SCENARIO B: Task Filtering by Competency, Difficulty, and Scenario Type
# ==============================================================================
def test_scenario_b_task_filtering(client: TestClient, db_session: Session):
    cpi_task = db_session.execute(
        select(PracticalTask).where(PracticalTask.task_id == "TASK-MOSPI-CPI-01")
    ).scalar_one()

    # Filter by competency_id
    resp = client.get(f"/api/practical/tasks?competency_id={cpi_task.competency_id}")
    assert resp.status_code == 200
    for t in resp.json():
        assert t["competency_id"] == cpi_task.competency_id

    # Filter by difficulty
    resp = client.get("/api/practical/tasks?difficulty=hard")
    assert resp.status_code == 200
    for t in resp.json():
        assert t["difficulty"] == "hard"

    # Filter by scenario_type
    resp = client.get("/api/practical/tasks?scenario_type=DATA_VALIDATION")
    assert resp.status_code == 200
    for t in resp.json():
        assert t["scenario_type"] == "DATA_VALIDATION"


# ==============================================================================
# SCENARIO C: Task Lifecycle - Start Attempt
# ==============================================================================
def test_scenario_c_start_attempt(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=headers)
    assert resp.status_code == 200
    attempt = resp.json()

    assert attempt["attempt_id"].startswith("pr_att_")
    assert attempt["status"] == "STARTED"
    assert attempt["user_id"] == test_learner.id
    assert attempt["score"] is None
    assert attempt["evidence_id"] is None


# ==============================================================================
# SCENARIO D: Learner Isolation & Unauthorized Attempt Access
# ==============================================================================
def test_scenario_d_learner_isolation(client: TestClient, test_learner: User, other_learner: User):
    # test_learner starts attempt
    resp1 = client.post(
        "/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=auth_headers(test_learner)
    )
    attempt_id = resp1.json()["attempt_id"]

    # other_learner tries to get it -> 403 Forbidden
    resp2 = client.get(f"/api/practical/attempts/{attempt_id}", headers=auth_headers(other_learner))
    assert resp2.status_code == 403

    # other_learner tries to submit it -> 403 Forbidden
    payload = {"submission": {"adjusted_weights": {}}}
    resp3 = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json=payload,
        headers=auth_headers(other_learner),
    )
    assert resp3.status_code == 403


# ==============================================================================
# SCENARIO E: Perfect Submission Evaluation
# ==============================================================================
def test_scenario_e_perfect_submission_evaluation(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Accurate answers for TASK-MOSPI-SAMP-01
    submission = {
        "response_rates": {
            "STRATUM-RURAL-01": 0.80,
            "STRATUM-URBAN-01": 0.80,
            "STRATUM-PERIURBAN-01": 0.80,
        },
        "adjusted_weights": {
            "STRATUM-RURAL-01": 31.25,
            "STRATUM-URBAN-01": 18.75,
            "STRATUM-PERIURBAN-01": 50.0,
        },
        "estimated_total": 35750000.0,
        "methodology_note": "Calibrated non-response adjustment factors to ensure unbiased weight totals.",
    }

    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()

    attempt = res["attempt"]
    assert attempt["status"] == "EVALUATED"
    assert attempt["score"] >= 0.95
    assert attempt["evaluator_type"] == "DETERMINISTIC"
    assert attempt["evidence_id"] is not None

    evaluation = res["evaluation"]
    assert evaluation["passed"] is True
    assert evaluation["dimension_scores"]["response_rates"] == 1.0
    assert evaluation["dimension_scores"]["adjusted_weights"] == 1.0
    assert evaluation["dimension_scores"]["estimated_total"] == 1.0


# ==============================================================================
# SCENARIO F: Tolerance Checking & Numerical Precision
# ==============================================================================
def test_scenario_f_tolerance_checking(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-CPI-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Submit values slightly shifted but within tolerance (+0.02 where tolerance is 0.05)
    submission = {
        "price_relatives": {
            "Food and Beverages": 125.02,
            "Housing": 110.03,
            "Fuel and Light": 119.98,
            "Miscellaneous": 110.01,
        },
        "laspeyres_index": 117.58,  # Expected 117.56, diff 0.02 <= 0.05 tolerance
        "inflation_rate": 17.58,   # Expected 17.56, diff 0.02 <= 0.05 tolerance
        "analysis_summary": "Calculated Laspeyres aggregate index from food price relatives and inflation.",
    }

    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["attempt"]["status"] == "EVALUATED"
    assert res["evaluation"]["passed"] is True
    assert res["attempt"]["score"] >= 0.90


# ==============================================================================
# SCENARIO G: Sub-Threshold / Failing Submission
# ==============================================================================
def test_scenario_g_failing_submission(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-02/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Incorrect calculations
    submission = {
        "stratum_products": {
            "ASI-SMALL": 50000.0,
            "ASI-MEDIUM": 80000.0,
            "ASI-LARGE": 120000.0,
        },
        "allocations": {
            "ASI-SMALL": 200,
            "ASI-MEDIUM": 200,
            "ASI-LARGE": 200,
        },
        "methodology_note": "Equal sample allocation without considering variance.",
    }

    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["attempt"]["status"] == "EVALUATED"
    assert res["evaluation"]["passed"] is False
    assert res["attempt"]["score"] < 0.50


# ==============================================================================
# SCENARIO H: Set-Equality Evaluation for Data Validation
# ==============================================================================
def test_scenario_h_set_equality_evaluation(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-QUAL-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Data validation correct responses with order reversed
    submission = {
        "invalid_record_ids": ["HH-104", "HH-103"],  # Reversed order set match
        "outlier_record_ids": ["HH-110"],
        "iqr": 1350.0,
        "upper_fence": 7025.0,
        "clean_mean": 4171.43,
        "audit_remarks": "Applied Tukey IQR bounds to exclude outlier and validation rule check.",
    }

    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["attempt"]["status"] == "EVALUATED"
    assert res["evaluation"]["passed"] is True
    assert res["evaluation"]["dimension_scores"]["invalid_record_ids"] == 1.0
    assert res["evaluation"]["dimension_scores"]["outlier_record_ids"] == 1.0


# ==============================================================================
# SCENARIO I: Missing Dimension Handling (Partial Credit)
# ==============================================================================
def test_scenario_i_missing_dimension_partial_credit(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-MISC-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Provide only stratum_means, omit other fields
    submission = {
        "stratum_means": {
            "TEXTILE": 140.0,
            "FOOD_PROC": 300.0,
        },
    }

    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["attempt"]["status"] == "EVALUATED"
    assert res["evaluation"]["dimension_scores"]["stratum_means"] == 1.0
    assert res["evaluation"]["dimension_scores"]["imputed_values"] == 0.0
    # Overall score should reflect only the weight of stratum_means (0.30)
    assert 0.25 <= res["attempt"]["score"] <= 0.35


# ==============================================================================
# SCENARIO J: Idempotent Submission Handling
# ==============================================================================
def test_scenario_j_idempotency_handling(client: TestClient, test_learner: User, db_session: Session):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    idempotency_key = f"idem_{uuid.uuid4().hex}"
    payload = {
        "submission": {
            "response_rates": {"STRATUM-RURAL-01": 0.8, "STRATUM-URBAN-01": 0.8, "STRATUM-PERIURBAN-01": 0.8},
            "adjusted_weights": {"STRATUM-RURAL-01": 31.25, "STRATUM-URBAN-01": 18.75, "STRATUM-PERIURBAN-01": 50.0},
            "estimated_total": 35750000.0,
            "methodology_note": "Calibrated non-response adjustment factors to ensure unbiased weight totals.",
        },
        "idempotency_key": idempotency_key,
    }

    # First submission
    resp1 = client.post(f"/api/practical/attempts/{attempt_id}/submit", json=payload, headers=headers)
    assert resp1.status_code == 200
    score1 = resp1.json()["attempt"]["score"]
    evidence_id1 = resp1.json()["attempt"]["evidence_id"]

    # Count evidences before second submission
    ev_count_before = len(db_session.execute(select(Evidence).where(Evidence.user_id == test_learner.id)).scalars().all())

    # Second submission with same idempotency key
    resp2 = client.post(f"/api/practical/attempts/{attempt_id}/submit", json=payload, headers=headers)
    assert resp2.status_code == 200
    score2 = resp2.json()["attempt"]["score"]
    evidence_id2 = resp2.json()["attempt"]["evidence_id"]

    assert score1 == score2
    assert evidence_id1 == evidence_id2

    # Verify no duplicate evidence was emitted
    ev_count_after = len(db_session.execute(select(Evidence).where(Evidence.user_id == test_learner.id)).scalars().all())
    assert ev_count_before == ev_count_after


# ==============================================================================
# SCENARIO K: Evidence Ledger Integration
# ==============================================================================
def test_scenario_k_evidence_ledger_integration(client: TestClient, test_learner: User, db_session: Session):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    submission = {
        "response_rates": {"STRATUM-RURAL-01": 0.8, "STRATUM-URBAN-01": 0.8, "STRATUM-PERIURBAN-01": 0.8},
        "adjusted_weights": {"STRATUM-RURAL-01": 31.25, "STRATUM-URBAN-01": 18.75, "STRATUM-PERIURBAN-01": 50.0},
        "estimated_total": 35750000.0,
        "methodology_note": "Calibrated non-response adjustment factors to ensure unbiased weight totals.",
    }

    submit_resp = client.post(f"/api/practical/attempts/{attempt_id}/submit", json={"submission": submission}, headers=headers)
    assert submit_resp.status_code == 200
    evidence_id = submit_resp.json()["attempt"]["evidence_id"]
    assert evidence_id is not None

    evidence = db_session.get(Evidence, evidence_id)
    assert evidence is not None
    assert evidence.evidence_type == EvidenceType.PRACTICAL_TASK
    assert evidence.provenance == "[SANDBOX DATA]"
    assert evidence.reliability_status == "VERIFIED"
    assert evidence.source == "PRACTICAL_TASK:TASK-MOSPI-SAMP-01"

    meta = json.loads(evidence.evidence_metadata)
    assert meta["task_id"] == "TASK-MOSPI-SAMP-01"
    assert meta["attempt_id"] == attempt_id


# ==============================================================================
# SCENARIO L: Competency State Recalculation
# ==============================================================================
def test_scenario_l_competency_state_recalculation(client: TestClient, test_learner: User, db_session: Session):
    task = db_session.execute(select(PracticalTask).where(PracticalTask.task_id == "TASK-MOSPI-CPI-01")).scalar_one()
    headers = auth_headers(test_learner)

    # Initial state should be unassessed or non-existent
    state_before = db_session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == test_learner.id,
            CompetencyState.competency_id == task.competency_id,
        )
    ).scalar_one_or_none()

    start_resp = client.post(f"/api/practical/tasks/{task.task_id}/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    submission = {
        "price_relatives": {"Food and Beverages": 125.0, "Housing": 110.0, "Fuel and Light": 120.0, "Miscellaneous": 110.0},
        "laspeyres_index": 117.56,
        "inflation_rate": 17.56,
        "analysis_summary": "Calculated Laspeyres aggregate index from food price relatives and inflation.",
    }

    submit_resp = client.post(f"/api/practical/attempts/{attempt_id}/submit", json={"submission": submission}, headers=headers)
    assert submit_resp.status_code == 200

    # Verify competency state updated
    state_after = db_session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == test_learner.id,
            CompetencyState.competency_id == task.competency_id,
        )
    ).scalar_one()

    assert state_after.mastery is not None
    assert state_after.mastery >= 0.70
    assert state_after.confidence > 0.0


# ==============================================================================
# SCENARIO M: Conflicting Evidence Detection
# ==============================================================================
def test_scenario_m_conflicting_evidence_detection(db_session: Session, test_learner: User):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one()
    
    # 1. High knowledge assessment evidence: 1.0 (>= 0.95)
    ev_knowledge = Evidence(
        user_id=test_learner.id,
        competency_id=comp.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="MCQ High Knowledge",
        score=1.0,
        reliability_status="VERIFIED",
    )
    # 2. Low practical task evidence: 0.35 (< 0.70)
    ev_practical = Evidence(
        user_id=test_learner.id,
        competency_id=comp.id,
        evidence_type=EvidenceType.PRACTICAL_TASK,
        title="Practical Failed Scenario",
        score=0.35,
        reliability_status="VERIFIED",
    )
    db_session.add(ev_knowledge)
    db_session.add(ev_practical)
    db_session.commit()

    orch = recalculate_competency_state(db_session, test_learner.id, comp.id)
    db_session.commit()

    # Conflicting evidence rule: Knowledge >= 0.95 but practical/application < 0.70 -> CONFLICTING_EVIDENCE
    assert orch.state.status == "CONFLICTING_EVIDENCE"


# ==============================================================================
# SCENARIO N: LLM Evaluator Safe Degradation / Fallback
# ==============================================================================
def test_scenario_n_llm_evaluator_safe_degradation(client: TestClient, test_learner: User):
    headers = auth_headers(test_learner)
    start_resp = client.post("/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    submission = {
        "response_rates": {"STRATUM-RURAL-01": 0.8, "STRATUM-URBAN-01": 0.8, "STRATUM-PERIURBAN-01": 0.8},
        "adjusted_weights": {"STRATUM-RURAL-01": 31.25, "STRATUM-URBAN-01": 18.75, "STRATUM-PERIURBAN-01": 50.0},
        "estimated_total": 35750000.0,
        "methodology_note": "Calibrated non-response adjustment factors to ensure unbiased weight totals.",
    }

    # Request LLM_ASSISTED evaluator when no API key is present in environment
    submit_resp = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": submission, "evaluator_type": "LLM_ASSISTED"},
        headers=headers,
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    attempt = res["attempt"]

    # Either evaluated via deterministic fallback or safe degradation
    assert attempt["status"] in ("EVALUATED", "REVIEW_REQUIRED")
    assert attempt["evaluator_type"] in ("LLM_ASSISTED", "LLM_ASSISTED_FALLBACK")


# ==============================================================================
# SCENARIO O: Closed-Loop Integration with Next Best Action
# ==============================================================================
def test_scenario_o_closed_loop_with_next_best_action(client: TestClient, other_learner: User, db_session: Session):
    headers = auth_headers(other_learner)
    task = db_session.execute(select(PracticalTask).where(PracticalTask.task_id == "TASK-MOSPI-SAMP-02")).scalar_one()

    # Learner fails the Neyman allocation practical task
    start_resp = client.post(f"/api/practical/tasks/{task.task_id}/attempts", headers=headers)
    attempt_id = start_resp.json()["attempt_id"]

    bad_submission = {
        "stratum_products": {"ASI-SMALL": 100.0, "ASI-MEDIUM": 100.0, "ASI-LARGE": 100.0},
        "allocations": {"ASI-SMALL": 50, "ASI-MEDIUM": 50, "ASI-LARGE": 50},
        "methodology_note": "Flawed approach.",
    }

    submit_resp = client.post(f"/api/practical/attempts/{attempt_id}/submit", json={"submission": bad_submission}, headers=headers)
    assert submit_resp.status_code == 200

    # Request Next Best Action recommendations for this competency
    rec_resp = client.post(
        "/api/recommendations/next-best-action",
        json={"competency_id": task.competency_id},
        headers=headers,
    )
    assert rec_resp.status_code == 200
    rec = rec_resp.json()

    assert rec["selected_intervention"] is not None
    assert rec["competency_id"] == task.competency_id
    assert rec["status"] == "RECOMMENDED"
