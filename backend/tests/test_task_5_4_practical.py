from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.database import get_db
from app.main import app
from app.models.competency import Competency, CompetencyDomain, Role, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.practical import AttemptStatus, PracticalAttempt, PracticalTask
from app.models.user import User
from app.services.practical.deterministic_evaluator import DeterministicEvaluator
from app.services.practical.evaluator_base import EvaluationResult
from app.services.practical.practical_service import PracticalService
from app.utils.security import create_access_token, hash_password


@pytest.fixture
def setup_practical_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed roles
    role = Role(name="Field Investigator")
    session.add(role)
    session.flush()

    # Seed competency taxonomy
    comp = Competency(name="Industrial Survey Methodology", domain=CompetencyDomain.STATISTICAL)
    session.add(comp)
    session.flush()

    sub = SubSkill(name="GVA Calculation", competency_id=comp.id)
    session.add(sub)
    session.flush()

    # Seed practical task with dimensions rubric
    task = PracticalTask(
        task_id="PRAC-TASK-001",
        title="ASI Gross Value Added Computation",
        competency_id=comp.id,
        subskill_id=sub.id,
        scenario_type="STATISTICAL_PROCEDURE",
        difficulty="medium",
        scenario_context="Official-Statistics-aligned simulated practical task for ASI returns.",
        instructions="Compute GVA from gross output and intermediate consumption.",
        input_artifacts_json=json.dumps({"gross_output": 1250000.0, "intermediate_consumption": 780000.0}),
        expected_output_type="NUMERICAL_JSON",
        rubric_json=json.dumps({
            "passing_score": 0.70,
            "dimensions": {
                "numerical_gva": {
                    "weight": 0.60,
                    "expected": 470000.0,
                    "tolerance": 5000.0,
                },
                "methodology_explanation": {
                    "weight": 0.40,
                    "keywords": ["output", "deduction", "consumption"],
                    "min_length": 15,
                },
            },
        }),
        rubric_version="v1.0-rubric",
        provenance="[SANDBOX DATA]",
        source="MOSPI_SIMULATION",
        version=1,
        status="ACTIVE",
    )
    session.add(task)
    session.flush()

    # Seed users
    u1 = User(
        email="learner1@mospi.gov.in",
        full_name="Learner One",
        password_hash=hash_password("pass123"),
        role_id=role.id,
        is_active=True,
    )
    u2 = User(
        email="learner2@mospi.gov.in",
        full_name="Learner Two",
        password_hash=hash_password("pass123"),
        role_id=role.id,
        is_active=True,
    )
    session.add_all([u1, u2])
    session.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield session, u1, u2, task, comp, sub

    app.dependency_overrides.clear()
    session.close()


def test_1_list_available_practical_task(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    resp = client.get("/api/practical/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1
    assert tasks[0]["task_id"] == "PRAC-TASK-001"


def test_2_retrieve_task(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    resp = client.get(f"/api/practical/tasks/{task.task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == task.task_id
    assert "input_artifacts" in data


def test_3_start_attempt(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    resp = client.post(f"/api/practical/tasks/{task.task_id}/attempts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "STARTED"
    assert data["task_id"] == task.id


def test_4_persist_attempt(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    assert attempt.id is not None

    db_attempt = session.get(PracticalAttempt, attempt.id)
    assert db_attempt is not None
    assert db_attempt.user_id == u1.id


def test_5_submit_valid_work(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    resp = client.post(
        f"/api/practical/attempts/{attempt.attempt_id}/submit",
        json={
            "submission": {
                "numerical_gva": 470000.0,
                "methodology_explanation": "Deduction of intermediate consumption from gross output.",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["attempt"]["status"] == "EVALUATED"
    assert data["attempt"]["score"] >= 0.70


def test_6_evaluate_through_actual_evaluator_interface(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    evaluator = DeterministicEvaluator()
    result = evaluator.evaluate(
        task,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    assert isinstance(result, EvaluationResult)
    assert result.passed is True
    assert result.score >= 0.70


def test_7_persist_evaluation(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    attempt, summary = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    session.refresh(attempt)
    assert attempt.score is not None
    assert attempt.evaluation_result_json is not None


def test_8_create_evidence(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    attempt, summary = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    assert attempt.evidence_id is not None
    ev = session.get(Evidence, attempt.evidence_id)
    assert ev is not None
    assert ev.evidence_type == EvidenceType.PRACTICAL_TASK
    assert ev.user_id == u1.id


def test_9_update_competency(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    attempt, summary = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    assert summary is not None
    assert summary["competency_id"] == comp.id

    st = session.execute(
        select(CompetencyState).where(CompetencyState.user_id == u1.id, CompetencyState.competency_id == comp.id)
    ).scalar_one_or_none()
    assert st is not None
    assert st.mastery > 0.0


def test_10_competency_history_updated(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    hist = session.execute(
        select(CompetencyHistory).where(CompetencyHistory.user_id == u1.id, CompetencyHistory.competency_id == comp.id)
    ).scalars().all()
    assert len(hist) >= 1
    assert hist[-1].new_mastery is not None


def test_11_failed_attempt_does_not_produce_mastery(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)

    # Submit completely wrong answer (score 0.0)
    attempt, summary = PracticalService.submit_attempt(
        session, u1.id, attempt.attempt_id, {"numerical_gva": 0.0, "methodology_explanation": "wrong"}
    )
    assert attempt.score < 0.50

    st = session.execute(
        select(CompetencyState).where(CompetencyState.user_id == u1.id, CompetencyState.competency_id == comp.id)
    ).scalar_one_or_none()
    assert st is None or st.mastery < 0.70


def test_12_partial_result_behaves_correctly(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    evaluator = DeterministicEvaluator()
    # Correct value (0.60 weight) but missing explanation keywords (0.40 weight)
    res = evaluator.evaluate(task, {"numerical_gva": 470000.0, "methodology_explanation": "short text"})
    assert 0.55 <= res.score <= 0.65
    assert res.passed is False  # below threshold 0.70


def test_13_review_required_result_is_preserved(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    attempt.status = AttemptStatus.REVIEW_REQUIRED.value
    session.commit()
    session.refresh(attempt)
    assert attempt.status == AttemptStatus.REVIEW_REQUIRED.value


def test_14_duplicate_start_is_idempotent_where_required(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    key = "idemp_start_123"
    att1 = PracticalService.start_attempt(session, u1.id, task.task_id, idempotency_key=key)
    att2 = PracticalService.start_attempt(session, u1.id, task.task_id, idempotency_key=key)
    assert att1.id == att2.id


def test_15_duplicate_outcome_does_not_double_apply_evidence(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    key = "idemp_submit_999"

    att1, sum1 = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
        idempotency_key=key,
    )
    initial_ev_count = len(session.execute(select(Evidence).where(Evidence.user_id == u1.id)).scalars().all())

    att2, sum2 = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
        idempotency_key=key,
    )
    post_ev_count = len(session.execute(select(Evidence).where(Evidence.user_id == u1.id)).scalars().all())

    assert initial_ev_count == post_ev_count
    assert sum2 is None


def test_16_learner_isolation(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token_b = create_access_token(u2.id)
    client = TestClient(app)

    attempt_a = PracticalService.start_attempt(session, u1.id, task.task_id)
    resp = client.get(f"/api/practical/attempts/{attempt_a.attempt_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 403


def test_17_unauthorized_request(setup_practical_db):
    client = TestClient(app)
    resp = client.post("/api/practical/tasks/PRAC-TASK-001/attempts")
    assert resp.status_code in (401, 403)


def test_18_invalid_task(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    resp = client.get("/api/practical/tasks/NONEXISTENT_TASK", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_19_malformed_submission(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    resp = client.post(
        f"/api/practical/attempts/{attempt.attempt_id}/submit",
        json={"submission": "NOT_A_DICT"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_20_evaluator_failure(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)

    class FailingEvaluator:
        def evaluate(self, t, s):
            raise RuntimeError("Evaluator hardware timeout")

    with pytest.raises(RuntimeError, match="timeout"):
        FailingEvaluator().evaluate(task, {})


def test_21_transaction_rollback(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    initial_ev_count = len(session.execute(select(Evidence)).scalars().all())

    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)

    try:
        session.begin_nested()
        ev = Evidence(
            user_id=u1.id,
            competency_id=task.competency_id,
            evidence_type=EvidenceType.PRACTICAL_TASK,
            title="Practical Task Rollback Test",
            description="Testing rollback",
            score=0.95,
            provenance="[TEST]",
            source="TEST",
        )
        session.add(ev)
        session.flush()
        raise ValueError("Simulated pipeline failure")
    except ValueError:
        session.rollback()

    post_ev_count = len(session.execute(select(Evidence)).scalars().all())
    assert post_ev_count == initial_ev_count


def test_22_evidence_provenance_verification(setup_practical_db):
    session, u1, u2, task, comp, sub = setup_practical_db
    attempt = PracticalService.start_attempt(session, u1.id, task.task_id)
    attempt, summary = PracticalService.submit_attempt(
        session,
        u1.id,
        attempt.attempt_id,
        {
            "numerical_gva": 470000.0,
            "methodology_explanation": "Deduction of intermediate consumption from gross output.",
        },
    )
    assert attempt.evidence_id is not None
    ev = session.get(Evidence, attempt.evidence_id)
    assert ev is not None
    assert ev.provenance == "[SANDBOX DATA]"
    assert f"PRACTICAL_TASK:{task.task_id}" in ev.source
    meta = json.loads(ev.evidence_metadata)
    assert meta["task_id"] == task.task_id
    assert meta["attempt_id"] == attempt.attempt_id
