from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.database import get_db
from app.main import app
from app.models.competency import Competency, CompetencyDomain, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import Scenario, ScenarioAttempt, ScenarioAttemptStatus, ScenarioEvaluation
from app.models.user import User
from app.services.scenarios.scenario_interfaces import (
    CandidateValidationError,
    DeterministicScenarioEvaluator,
    DeterministicScenarioGenerator,
    EvaluationValidationError,
    LLMScenarioGenerator,
    ScenarioCandidate,
    ScenarioEvaluationResult,
    ScenarioGenerationContext,
    validate_evaluation_result,
    validate_scenario_candidate,
)
from app.services.scenarios.scenario_service import ScenarioService
from app.utils.security import create_access_token, hash_password


@pytest.fixture
def setup_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Taxonomy seed
    role = Role(name="Field Investigator")
    session.add(role)
    session.flush()

    comp1 = Competency(name="Sampling Frame Design", domain=CompetencyDomain.STATISTICAL)
    comp2 = Competency(name="Data Quality Verification", domain=CompetencyDomain.STATISTICAL)
    session.add_all([comp1, comp2])
    session.flush()

    sub1 = SubSkill(name="Stratified Selection", competency_id=comp1.id)
    sub2 = SubSkill(name="Non-response Imputation", competency_id=comp2.id)
    session.add_all([sub1, sub2])
    session.flush()

    rc = RoleCompetency(role_id=role.id, competency_id=comp1.id)
    session.add(rc)
    session.flush()

    # Users
    u1 = User(
        email="learner_a@example.com",
        full_name="Learner A",
        password_hash=hash_password("pass123"),
        role_id=role.id,
        is_active=True,
    )
    u2 = User(
        email="learner_b@example.com",
        full_name="Learner B",
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

    yield session, u1, u2, comp1, sub1, comp2, sub2

    app.dependency_overrides.clear()
    session.close()


def test_1_authenticated_learner_creates_or_requests_valid_scenario(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    payload = {
        "title": "NSS Stratified Sampling Scenario",
        "description": "Establish stratum boundaries for NSS consumer expenditure survey.",
        "scenario_type": "SURVEY_DESIGN",
        "competency_id": comp1.id,
        "subskill_id": sub1.id,
        "difficulty": "medium",
        "expected_outcomes": ["Stratify urban and rural blocks accurately."],
        "evaluation_rubric": {"passing_threshold": 0.70, "criteria": []},
        "metadata": {"source": "TEST"},
    }
    resp = client.post("/api/scenarios", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["competency_id"] == comp1.id


def test_2_scenario_is_actually_persisted(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    candidate = ScenarioCandidate(
        title="Field Validation Drill",
        description="Verify household roster consistency.",
        scenario_type="OPERATIONAL_PROCEDURE",
        competency_id=comp1.id,
        subskill_id=sub1.id,
        expected_outcomes=["Detect discrepancy."],
        evaluation_rubric={"passing_threshold": 0.70},
    )
    scen = ScenarioService.create_scenario(session, candidate)
    assert scen.id is not None

    db_scen = session.get(Scenario, scen.id)
    assert db_scen is not None
    assert db_scen.title == "Field Validation Drill"


def test_3_scenario_references_valid_competency_subskill(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    candidate = ScenarioCandidate(
        title="Check Taxonomy Link",
        description="Scenario testing FK relationships.",
        scenario_type="OPERATIONAL_PROCEDURE",
        competency_id=comp1.id,
        subskill_id=sub1.id,
        expected_outcomes=["Verify link."],
        evaluation_rubric={"passing_threshold": 0.70},
    )
    scen = ScenarioService.create_scenario(session, candidate)
    assert scen.competency_id == comp1.id
    assert scen.subskill_id == sub1.id


def test_4_learner_creates_an_attempt(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Attempt Creation Test Scenario",
            description="Operational scenario for attempt creation.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Complete task."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )

    resp = client.post(f"/api/scenarios/{scen.scenario_id}/attempts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "STARTED"
    assert data["user_id"] == u1.id


def test_5_learner_submits_response(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Response Submission Scenario",
            description="Scenario testing response persistence.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Analyze data."],
            evaluation_rubric={
                "passing_threshold": 0.70,
                "criteria": [{"name": "strat", "weight": 1.0, "required_keyword": "stratification"}],
            },
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)

    resp = client.post(
        f"/api/scenarios/attempts/{attempt.attempt_id}/submit",
        json={"response_payload": {"answer": "Apply proper stratification to the rural block."}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["attempt"]["status"] in ("EVALUATED", "REVIEW_REQUIRED")


def test_6_actual_backend_evaluation_path_executes(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Evaluation Path Test",
            description="Testing evaluator invocation.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Solve issue."],
            evaluation_rubric={
                "passing_threshold": 0.70,
                "criteria": [
                    {"name": "c1", "weight": 0.5, "required_keyword": "stratification"},
                    {"name": "c2", "weight": 0.5, "required_keyword": "resample"},
                ],
            },
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    attempt, eval_rec, update = ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "We need stratification and will resample the cluster."},
    )
    assert eval_rec is not None
    assert eval_rec.passed is True
    assert eval_rec.normalized_score == 1.0


def test_7_evaluation_result_is_persisted(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Persisted Eval Test",
            description="Testing evaluation persistence.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Solve."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    attempt, eval_rec, _ = ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "General detailed procedure answer for testing."},
    )
    assert eval_rec.id is not None
    db_eval = session.get(ScenarioEvaluation, eval_rec.id)
    assert db_eval is not None
    assert db_eval.attempt_id == attempt.id


def test_8_evidence_is_created(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Evidence Creation Test",
            description="Testing evidence creation.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            subskill_id=sub1.id,
            expected_outcomes=["Emit evidence."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "Thorough operational response with sufficient length."},
    )
    ev = session.execute(
        select(Evidence).where(
            Evidence.user_id == u1.id,
            Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO,
            Evidence.competency_id == comp1.id,
        )
    ).scalar_one_or_none()
    assert ev is not None
    assert "SCENARIO:" in ev.source
    assert ev.provenance == "[SANDBOX DATA]"


def test_9_competency_state_changes_through_real_competency_service(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Competency Change Test",
            description="Testing state calculation.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Update state."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    attempt, eval_rec, comp_update = ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "Sufficiently detailed technical answer."},
    )
    assert comp_update is not None
    assert comp_update["competency_id"] == comp1.id

    st = session.execute(
        select(CompetencyState).where(CompetencyState.user_id == u1.id, CompetencyState.competency_id == comp1.id)
    ).scalar_one_or_none()
    assert st is not None
    assert st.mastery > 0.0


def test_10_competency_history_records_the_transition(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="History Transition Test",
            description="Testing history record.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Record history."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "Thorough operational response."},
    )
    hist = session.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == u1.id,
            CompetencyHistory.competency_id == comp1.id,
        )
    ).scalars().all()
    assert len(hist) >= 1
    assert hist[-1].new_mastery is not None


def test_11_duplicate_submission_behaves_idempotently(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Idempotency Test Scenario",
            description="Testing idempotent submission.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Be idempotent."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)
    key = "idemp_key_12345"

    att1, eval1, up1 = ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "First submission."},
        idempotency_key=key,
    )
    att2, eval2, up2 = ScenarioService.submit_attempt(
        session,
        user_id=u1.id,
        attempt_id=attempt.attempt_id,
        response_payload={"answer": "Second repeated submission."},
        idempotency_key=key,
    )
    assert att1.id == att2.id
    assert eval1.id == eval2.id
    assert up2 is None  # Does not re-trigger double evidence or update


def test_12_invalid_scenario_is_rejected(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    token = create_access_token(u1.id)
    client = TestClient(app)

    # Missing expected outcomes and invalid difficulty
    payload = {
        "title": "AB",  # too short
        "description": "Short",
        "scenario_type": "INVALID_TYPE",
        "competency_id": comp1.id,
        "difficulty": "extreme_impossible",
    }
    resp = client.post("/api/scenarios", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (400, 422)


def test_13_invalid_competency_subskill_relationship_is_rejected(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    # sub2 belongs to comp2, pairing with comp1 must fail
    cand = ScenarioCandidate(
        title="Mismatched Subskill Scenario",
        description="Testing validation constraint on subskill.",
        scenario_type="OPERATIONAL_PROCEDURE",
        competency_id=comp1.id,
        subskill_id=sub2.id,
        expected_outcomes=["Fail validation."],
        evaluation_rubric={"passing_threshold": 0.70},
    )
    with pytest.raises(CandidateValidationError, match="belongs to competency"):
        validate_scenario_candidate(session, cand)


def test_14_learner_a_cannot_access_learner_b_attempt(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    token_b = create_access_token(u2.id)
    client = TestClient(app)

    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Learner Isolation Scenario",
            description="Testing isolation.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Isolate."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt_a = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)

    # Learner B attempts to read Learner A's attempt
    resp = client.get(f"/api/scenarios/attempts/{attempt_a.attempt_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 403


def test_15_unauthenticated_request_is_rejected(setup_db):
    client = TestClient(app)
    resp = client.get("/api/scenarios")
    assert resp.status_code in (401, 403)


def test_16_malformed_evaluator_output_is_rejected(setup_db):
    bad_result = ScenarioEvaluationResult(
        score=1.5,  # exceeds max_score
        max_score=1.0,
        normalized_score=1.5,  # out of bounds
        passed=True,
        competency_evidence={},
        subskill_evidence={},
        rubric_results={},
    )
    with pytest.raises(EvaluationValidationError):
        validate_evaluation_result(bad_result)


def test_17_scenario_provider_unavailable_path_degrades_safely(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    llm_gen = LLMScenarioGenerator(available=False)
    ctx = ScenarioGenerationContext(competency_id=comp1.id)

    with pytest.raises(RuntimeError, match="unavailable"):
        llm_gen.generate(ctx)


def test_18_database_transaction_rollback_works_on_failure(setup_db):
    session, u1, u2, comp1, sub1, comp2, sub2 = setup_db
    scen = ScenarioService.create_scenario(
        session,
        ScenarioCandidate(
            title="Rollback Verification Scenario",
            description="Testing transactional rollback.",
            scenario_type="OPERATIONAL_PROCEDURE",
            competency_id=comp1.id,
            expected_outcomes=["Rollback."],
            evaluation_rubric={"passing_threshold": 0.70},
        ),
    )
    attempt = ScenarioService.start_attempt(session, u1.id, scen.scenario_id)

    class MalformedEvaluator:
        def evaluate(self, s, r):
            return ScenarioEvaluationResult(
                score=999.0,
                max_score=1.0,
                normalized_score=999.0,
                passed=True,
                competency_evidence={},
                subskill_evidence={},
                rubric_results={},
            )

    initial_ev_count = len(session.execute(select(Evidence)).scalars().all())

    with pytest.raises(EvaluationValidationError):
        ScenarioService.submit_attempt(
            session,
            user_id=u1.id,
            attempt_id=attempt.attempt_id,
            response_payload={"answer": "Crash me"},
            evaluator=MalformedEvaluator(),
        )

    # Ensure no orphan evidence was committed
    post_ev_count = len(session.execute(select(Evidence)).scalars().all())
    assert post_ev_count == initial_ev_count
