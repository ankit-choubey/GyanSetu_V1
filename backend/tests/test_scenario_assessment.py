import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("JWT_SECRET", "scenario-assessment-test-secret")
sys.path.insert(0, str(Path(__file__).parents[2]))

from app.main import app
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import ScenarioItem
from app.models.scenario_attempt import ScenarioAttempt
from app.models.user import User
from app.routers import scenario as scenario_router
from app.services import scenario_assessment


@pytest.fixture
def database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        role = Role(name="Learner")
        competency = Competency(name="Sampling Design")
        user = User(
            email="learner@example.com",
            full_name="Learner",
            password_hash="hashed",
        )
        session.add_all([role, competency, user])
        session.flush()
        user.role_id = role.id
        session.add(RoleCompetency(role_id=role.id, competency_id=competency.id))
        scenario = ScenarioItem(
            competency_id=competency.id,
            title="Sampling Scenario",
            scenario_text="A survey team must select a sampling method.",
            context_data=json.dumps({"dataset": "survey summary"}),
            question="Which method should the team choose and why?",
            response_type="structured_text",
            instructions="Explain your reasoning.",
            expected_reasoning=json.dumps({"key_points": ["Match method to design"]}),
            rubric=json.dumps(
                {
                    "criteria": [
                        {"criterion_id": "C1", "max_score": 4},
                        {"criterion_id": "C2", "max_score": 6},
                    ],
                    "max_score": 10,
                }
            ),
            difficulty="medium",
            cognitive_level="application",
            source_reference="training material",
        )
        session.add(scenario)
        session.commit()
        session.refresh(user)
        session.refresh(scenario)
        yield engine, user, scenario


@pytest.fixture
def client(database):
    engine, user, _ = database

    def override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[scenario_router.get_current_user] = lambda: user
    app.dependency_overrides[scenario_router.get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client, engine, user
    app.dependency_overrides.pop(scenario_router.get_current_user, None)
    app.dependency_overrides.pop(scenario_router.get_db, None)


@pytest.fixture
def evaluation_result():
    return {
        "evaluation": {
            "score": 8,
            "max_score": 10,
            "percentage": 80,
            "criterion_results": [
                {"criterion_id": "C1", "score": 4, "max_score": 4, "result": "met", "feedback": "Correct method."},
                {"criterion_id": "C2", "score": 4, "max_score": 6, "result": "partially_met", "feedback": "Justification needs detail."},
            ],
            "overall_result": "partially_correct",
        },
        "feedback": {
            "summary": "Most reasoning was demonstrated.",
            "strengths": ["Correct method selection."],
            "areas_for_improvement": ["Expand justification."],
            "recommended_next_step": "Review the supporting rationale.",
        },
        "evidence": {
            "demonstrated_competency": True,
            "evidence_type": "scenario_assessment",
            "confidence": 0.8,
        },
    }


def test_authorized_scenario_retrieval_hides_evaluation_material(client, database):
    test_client, _, _ = client
    _, _, scenario = database

    response = test_client.get(f"/api/scenario/{scenario.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == scenario.id
    assert body["context_data"] == {"dataset": "survey summary"}
    for private_field in (
        "expected_reasoning",
        "rubric",
        "evaluation_feedback",
        "evaluation_criterion_results",
        "confidence",
        "demonstrated_competency",
    ):
        assert private_field not in body


def test_unauthorized_scenario_retrieval_is_rejected(client, database):
    test_client, engine, user = client
    _, _, scenario = database
    with Session(engine) as session:
        other_role = Role(name="Other role")
        session.add(other_role)
        session.commit()
        stored_user = session.get(User, user.id)
        stored_user.role_id = other_role.id
        session.add(stored_user)
        session.commit()
        user.role_id = other_role.id

    response = test_client.get(f"/api/scenario/{scenario.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Scenario is outside the authenticated user's scope."


def test_invalid_scenario_id_is_rejected(client):
    test_client, _, _ = client

    response = test_client.get("/api/scenario/99999")

    assert response.status_code == 404


def test_unauthorized_scenario_submission_is_rejected(client, database, monkeypatch, evaluation_result):
    test_client, engine, user = client
    _, _, scenario = database
    with Session(engine) as session:
        other_role = Role(name="Other role")
        session.add(other_role)
        session.commit()
        stored_user = session.get(User, user.id)
        stored_user.role_id = other_role.id
        session.add(stored_user)
        session.commit()
        user.role_id = other_role.id

    evaluator = Mock(return_value=evaluation_result)
    monkeypatch.setattr(
        scenario_assessment.scenario_ml_adapter,
        "evaluate_scenario_response",
        evaluator,
    )

    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "A response."},
    )

    assert response.status_code == 403
    evaluator.assert_not_called()


def test_valid_submission_persists_attempt_evidence_and_recalculation(
    client,
    database,
    evaluation_result,
    monkeypatch,
):
    test_client, engine, user = client
    _, _, scenario = database
    original_recalculate = scenario_assessment.recalculate_competency_state
    calls = []

    def spy_recalculate(*args, **kwargs):
        calls.append((args, kwargs))
        return original_recalculate(*args, **kwargs)

    monkeypatch.setattr(
        scenario_assessment,
        "recalculate_competency_state",
        spy_recalculate,
    )
    evaluator = Mock(return_value=evaluation_result)
    monkeypatch.setattr(
        scenario_assessment.scenario_ml_adapter,
        "evaluate_scenario_response",
        evaluator,
    )

    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "Choose the matching method."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 8
    assert body["percentage"] == 80
    assert body["feedback"]["summary"] == "Most reasoning was demonstrated."
    assert body["demonstrated_competency"] is True
    assert len(calls) == 1
    evaluator.assert_called_once_with(
        {
            "title": "Sampling Scenario",
            "context": "A survey team must select a sampling method.",
            "context_data": {"dataset": "survey summary"},
        },
        {
            "question": "Which method should the team choose and why?",
            "response_type": "structured_text",
            "instructions": "Explain your reasoning.",
        },
        {"key_points": ["Match method to design"]},
        {
            "criteria": [
                {"criterion_id": "C1", "max_score": 4},
                {"criterion_id": "C2", "max_score": 6},
            ],
            "max_score": 10,
        },
        "Choose the matching method.",
    )

    with Session(engine) as session:
        attempts = session.exec(select(ScenarioAttempt)).all()
        evidence = session.exec(select(Evidence)).all()
        assert len(attempts) == 1
        assert len(evidence) == 1
        assert evidence[0].evidence_type == EvidenceType.APPLICATION_SCENARIO
        assert evidence[0].score == 0.8
        assert json.loads(attempts[0].evaluation_feedback)["summary"] == "Most reasoning was demonstrated."
        assert json.loads(attempts[0].evaluation_criterion_results)[0]["criterion_id"] == "C1"
        metadata = json.loads(evidence[0].evidence_metadata)
        assert metadata["scenario_id"] == scenario.id
        assert metadata["attempt_id"] == attempts[0].id
        assert metadata["source_reference"] == "training material"
        assert attempts[0].user_id == user.id


def test_empty_response_is_rejected(client, database):
    test_client, _, _ = client
    _, _, scenario = database

    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "   "},
    )

    assert response.status_code == 400


def test_malformed_stored_json_is_rejected(client, database):
    test_client, engine, _ = client
    _, _, scenario = database
    with Session(engine) as session:
        stored = session.get(ScenarioItem, scenario.id)
        stored.expected_reasoning = "not-json"
        session.add(stored)
        session.commit()

    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "A response."},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Stored scenario data is malformed."


@pytest.mark.parametrize(
    "bad_result",
    [
        {},
        {"evaluation": {}, "feedback": {}, "evidence": {}},
    ],
)
def test_invalid_evaluator_output_is_rejected(client, database, monkeypatch, bad_result):
    test_client, engine, _ = client
    _, _, scenario = database
    monkeypatch.setattr(
        scenario_assessment.scenario_ml_adapter,
        "evaluate_scenario_response",
        lambda *args: bad_result,
    )

    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "A response."},
    )

    assert response.status_code == 502
    with Session(engine) as session:
        assert session.exec(select(ScenarioAttempt)).all() == []
        assert session.exec(select(Evidence)).all() == []


def test_ml_failure_returns_controlled_error(client, database, monkeypatch):
    test_client, engine, _ = client
    _, _, scenario = database

    def fail(*args):
        raise RuntimeError("secret provider failure")

    monkeypatch.setattr(
        scenario_assessment.scenario_ml_adapter,
        "evaluate_scenario_response",
        fail,
    )
    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "A response."},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Scenario evaluation failed."
    assert "secret" not in response.text
    with Session(engine) as session:
        assert session.exec(select(ScenarioAttempt)).all() == []
        assert session.exec(select(Evidence)).all() == []


def test_recalculation_failure_rolls_back_attempt_and_evidence(
    client,
    database,
    evaluation_result,
    monkeypatch,
):
    test_client, engine, _ = client
    _, _, scenario = database
    monkeypatch.setattr(
        scenario_assessment.scenario_ml_adapter,
        "evaluate_scenario_response",
        lambda *args: evaluation_result,
    )

    def fail_recalculation(db, user_id, competency_id, **kwargs):
        db.add(
            CompetencyState(
                user_id=user_id,
                competency_id=competency_id,
                mastery=0.8,
                confidence=0.2,
                coverage=0.1,
                evidence_count=1,
                evidence_diversity=1,
                status="ASSESSED",
            )
        )
        db.flush()
        raise RuntimeError("database write failed")

    monkeypatch.setattr(
        scenario_assessment,
        "recalculate_competency_state",
        fail_recalculation,
    )
    response = test_client.post(
        "/api/scenario/submit",
        json={"scenario_id": scenario.id, "response_text": "A response."},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Scenario submission could not be completed."
    with Session(engine) as session:
        assert session.exec(select(ScenarioAttempt)).all() == []
        assert session.exec(select(Evidence)).all() == []
        assert session.exec(select(CompetencyState)).all() == []