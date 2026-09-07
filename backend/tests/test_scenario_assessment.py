from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("JWT_SECRET", "scenario-test-secret-that-is-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import ScenarioAttempt, ScenarioEvaluation, ScenarioItem
from app.models.user import User
from app.routers import scenario as scenario_router
from app.services.scenario_interfaces import (
    CriterionResult,
    EvaluationDetails,
    EvaluationEvidence,
    EvaluationFeedback,
    ProviderMetadata,
    ReasoningContract,
    Rubric,
    RubricCriterion,
    ScenarioContent,
    ScenarioEvaluationOutput,
    ScenarioGeneratorOutput,
    ScenarioProviderUnavailable,
    ScenarioTask,
)


@dataclass
class FakeGenerator:
    output: ScenarioGeneratorOutput

    def generate(self, request):
        return self.output


@dataclass
class FakeEvaluator:
    output: ScenarioEvaluationOutput | None = None
    unavailable: bool = False
    calls: int = 0
    requests: list = None

    def evaluate(self, request):
        self.calls += 1
        if self.requests is None:
            self.requests = []
        self.requests.append(request)
        if self.unavailable:
            raise ScenarioProviderUnavailable("test evaluator unavailable")
        return self.output


@dataclass
class FailingEvaluator:
    calls: int = 0

    def evaluate(self, request):
        self.calls += 1
        raise RuntimeError("evaluation failed")


@dataclass
class RawEvaluator:
    output: object

    def evaluate(self, request):
        return self.output


@dataclass
class RawGenerator:
    output: object

    def generate(self, request):
        return self.output


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    role = Role(name="Scenario Role")
    session.add(role)
    session.flush()
    learner = User(email="scenario@example.com", full_name="Scenario Learner", password_hash="hashed", role_id=role.id)
    other = User(email="other-scenario@example.com", full_name="Other Learner", password_hash="hashed", role_id=role.id)
    competency = Competency(name="Scenario Competency", role_id=role.id)
    session.add_all([learner, other, competency])
    session.flush()
    subskill = SubSkill(name="Scenario Subskill", competency_id=competency.id)
    session.add(subskill)
    session.add(RoleCompetency(role_id=role.id, competency_id=competency.id))
    session.commit()
    yield session, learner, other, competency, subskill
    session.close()
    engine.dispose()


def generated_scenario(competency_id: int, subskill_id: int | None, scenario_id: str = "scenario-001") -> ScenarioGeneratorOutput:
    return ScenarioGeneratorOutput(
        scenario_id=scenario_id,
        competency_id=competency_id,
        subskill_id=subskill_id,
        scenario=ScenarioContent(
            title="Sampling scenario",
            context="A survey team must choose a design.",
            context_data={"population": 1000},
            task=ScenarioTask(
                question="Choose and justify a sampling method.",
                response_type="structured_text",
                instructions="Explain the decision.",
            ),
        ),
        expected_reasoning=ReasoningContract(key_points=["justify coverage"], reference_answer="Use a defensible design."),
        rubric=Rubric(criteria=[RubricCriterion(criterion_id="c1", description="Justification", max_score=10)], max_score=10),
        difficulty="medium",
        cognitive_level="application",
        metadata=ProviderMetadata(provider="TEST", model="fake", model_version="1"),
    )


def evaluated_scenario(scenario_id: str, competency_id: int, subskill_id: int | None) -> ScenarioEvaluationOutput:
    return ScenarioEvaluationOutput(
        scenario_id=scenario_id,
        competency_id=competency_id,
        subskill_id=subskill_id,
        evaluation=EvaluationDetails(
            score=8,
            max_score=10,
            percentage=80,
            criterion_results=[CriterionResult(criterion_id="c1", result="met", score=8, feedback="Clear.")],
            overall_result="partially_correct",
        ),
        feedback=EvaluationFeedback(summary="Good application."),
        evidence=EvaluationEvidence(demonstrated_competency=True, evidence_type="scenario_assessment", confidence=0.86),
        metadata=ProviderMetadata(provider="TEST", evaluator_version="fake-1"),
    )


def override_dependencies(session, user, generator=None, evaluator=None):
    app.dependency_overrides[scenario_router.get_current_user] = lambda: user
    app.dependency_overrides[scenario_router.get_db] = lambda: session
    if generator is not None:
        app.dependency_overrides[scenario_router.get_scenario_generator] = lambda: generator
    if evaluator is not None:
        app.dependency_overrides[scenario_router.get_scenario_evaluator] = lambda: evaluator


def clear_dependencies():
    for dependency in (
        scenario_router.get_current_user,
        scenario_router.get_db,
        scenario_router.get_scenario_generator,
        scenario_router.get_scenario_evaluator,
    ):
        app.dependency_overrides.pop(dependency, None)


def test_generator_persists_scenario_and_delivery_hides_private_fields(db):
    session, learner, _, competency, subskill = db
    override_dependencies(session, learner, FakeGenerator(generated_scenario(competency.id, subskill.id)))
    try:
        response = TestClient(app).post(
            "/api/scenario-assessments",
            json={"competency_id": competency.id, "subskill_id": subskill.id},
        )
    finally:
        clear_dependencies()
    assert response.status_code == 200
    assert response.json()["scenario_id"] == "scenario-001"
    assert "expected_reasoning" not in response.json()
    stored = session.execute(select(ScenarioItem).where(ScenarioItem.scenario_id == "scenario-001")).scalar_one()
    assert response.json()["task_id"] == stored.id
    assert stored.rubric["max_score"] == 10
    assert stored.generator_metadata["provider"] == "TEST"


def test_attempt_and_evaluation_create_application_evidence_and_recalculate(db):
    session, learner, _, competency, subskill = db
    item = ScenarioItem(**generated_scenario(competency.id, subskill.id).model_dump(exclude={"scenario"}, exclude_unset=True))
    item.title = "Sampling scenario"
    item.context = "A survey team must choose a design."
    item.context_data = {"population": 1000}
    item.task_question = "Choose and justify a sampling method."
    item.response_type = "structured_text"
    item.instructions = "Explain the decision."
    item.expected_reasoning = generated_scenario(competency.id, subskill.id).expected_reasoning.model_dump()
    item.rubric = generated_scenario(competency.id, subskill.id).rubric.model_dump()
    item.difficulty = "medium"
    item.cognitive_level = "application"
    item.source_metadata = {}
    item.generator_metadata = {}
    session.add(item)
    session.commit()
    override_dependencies(session, learner, evaluator=FakeEvaluator(evaluated_scenario("scenario-001", competency.id, subskill.id)))
    try:
        client = TestClient(app)
        created = client.post("/api/scenario-assessments/scenario-001/attempts")
        attempt_id = created.json()["attempt_id"]
        submitted = client.post(
            f"/api/scenario-assessments/scenario-001/attempts/{attempt_id}/submit",
            json={"response": {"text": "Use stratified sampling because groups differ."}},
        )
    finally:
        clear_dependencies()
    assert created.status_code == 200
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "EVALUATED"
    evidence = session.execute(select(Evidence).where(Evidence.user_id == learner.id, Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO)).scalar_one()
    assert evidence.score == 0.8
    evaluation = session.execute(select(ScenarioEvaluation)).scalar_one()
    assert evaluation.percentage == 80
    assert session.scalar(select(func.count()).select_from(ScenarioAttempt)) == 1


def test_repeated_submission_returns_existing_evaluation_without_duplicate_work(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    evaluator = FakeEvaluator(evaluated_scenario("scenario-001", competency.id, subskill.id))
    override_dependencies(session, learner, FakeGenerator(output), evaluator)
    try:
        client = TestClient(app)
        assert client.post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id}).status_code == 200
        attempt_id = client.post("/api/scenario-assessments/scenario-001/attempts").json()["attempt_id"]
        payload = {"response": {"text": "Use stratified sampling because groups differ."}}
        first = client.post(f"/api/scenario-assessments/scenario-001/attempts/{attempt_id}/submit", json=payload)
        evaluation_count = session.scalar(select(func.count()).select_from(ScenarioEvaluation))
        evidence_count = session.scalar(select(func.count()).select_from(Evidence).where(Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO))
        second = client.post(f"/api/scenario-assessments/scenario-001/attempts/{attempt_id}/submit", json=payload)
    finally:
        clear_dependencies()
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["evaluation_id"] == first.json()["evaluation_id"]
    assert second.json()["evaluation"]["score"] == 8
    assert second.json()["evaluation"]["percentage"] == 80
    assert second.json()["evaluation"]["overall_result"] == "partially_correct"
    assert evaluator.calls == 1
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == evaluation_count == 1
    assert session.scalar(select(func.count()).select_from(Evidence).where(Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO)) == evidence_count == 1


def test_unavailable_generator_and_evaluator_are_explicit(db):
    session, learner, _, competency, subskill = db
    override_dependencies(session, learner)
    try:
        generated = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
    finally:
        clear_dependencies()
    assert generated.status_code == 503
    assert generated.json()["detail"]["status"] == "PROVIDER_UNAVAILABLE"


def test_malformed_generator_output_is_rejected(db):
    session, learner, _, competency, subskill = db
    override_dependencies(session, learner, RawGenerator({"scenario_id": "missing-contract-fields"}))
    try:
        response = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
    finally:
        clear_dependencies()
    assert response.status_code == 422
    assert session.scalar(select(func.count()).select_from(ScenarioItem)) == 0


def test_evaluator_unavailable_preserves_pending_attempt_without_evidence(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output))
    try:
        assert TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id}).status_code == 200
    finally:
        clear_dependencies()
    override_dependencies(session, learner, evaluator=FakeEvaluator(unavailable=True))
    try:
        client = TestClient(app)
        attempt = client.post("/api/scenario-assessments/scenario-001/attempts").json()["attempt_id"]
        response = client.post(f"/api/scenario-assessments/scenario-001/attempts/{attempt}/submit", json={"response": {"text": "answer"}})
    finally:
        clear_dependencies()
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_EVALUATION"
    assert session.scalar(select(func.count()).select_from(Evidence).where(Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO)) == 0


def test_legacy_evaluator_exception_retains_previous_rollback_behavior(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output), FailingEvaluator())
    try:
        client = TestClient(app)
        assert client.post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id}).status_code == 200
        attempt = client.post("/api/scenario-assessments/scenario-001/attempts").json()["attempt_id"]
        with pytest.raises(RuntimeError, match="evaluation failed"):
            client.post(f"/api/scenario-assessments/scenario-001/attempts/{attempt}/submit", json={"response": {"text": "answer"}})
    finally:
        clear_dependencies()
    assert session.scalar(select(func.count()).select_from(ScenarioAttempt)) == 1
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == 0
    assert session.scalar(select(func.count()).select_from(Evidence)) == 0


def test_legacy_invalid_evaluator_output_retains_previous_422_behavior(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output), RawEvaluator({"scenario_id": "scenario-001"}))
    try:
        client = TestClient(app)
        assert client.post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id}).status_code == 200
        attempt = client.post("/api/scenario-assessments/scenario-001/attempts").json()["attempt_id"]
        response = client.post(f"/api/scenario-assessments/scenario-001/attempts/{attempt}/submit", json={"response": {"text": "answer"}})
    finally:
        clear_dependencies()
    assert response.status_code == 422
    assert session.scalar(select(func.count()).select_from(ScenarioAttempt)) == 1
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == 0
    assert session.scalar(select(func.count()).select_from(Evidence)) == 0


def test_unauthorized_role_and_attempt_ownership_are_rejected(db):
    session, learner, other, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output))
    try:
        assert TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id}).status_code == 200
    finally:
        clear_dependencies()
    item = session.execute(select(ScenarioItem)).scalar_one()
    attempt = ScenarioAttempt(scenario_item_id=item.id, scenario_id=item.scenario_id, user_id=learner.id, competency_id=competency.id, subskill_id=subskill.id)
    session.add(attempt)
    session.commit()
    override_dependencies(session, other)
    try:
        response = TestClient(app).post(f"/api/scenario-assessments/{item.scenario_id}/attempts/{attempt.id}/submit", json={"response": {"text": "x"}})
    finally:
        clear_dependencies()
    assert response.status_code == 403


def test_direct_submission_creates_a_new_attempt_and_keeps_hidden_context(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    evaluator = FakeEvaluator(evaluated_scenario("scenario-001", competency.id, subskill.id))
    override_dependencies(session, learner, FakeGenerator(output), evaluator)
    try:
        generated = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
        scenario_id = generated.json()["task_id"]
        client = TestClient(app)
        first = client.post("/api/scenario/submit", json={"scenario_id": scenario_id, "response_text": "First decision"})
        second = client.post("/api/scenario/submit", json={"scenario_id": scenario_id, "response_text": "Second decision"})
    finally:
        clear_dependencies()
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "EVALUATED"
    assert second.json()["status"] == "EVALUATED"
    assert first.json()["attempt_id"] != second.json()["attempt_id"]
    assert session.scalar(select(func.count()).select_from(ScenarioAttempt)) == 2
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == 2
    assert len(evaluator.requests) == 2
    assert evaluator.requests[0].expected_reasoning.reference_answer
    assert evaluator.requests[0].rubric.max_score == 10


def test_direct_submission_requires_scenario_id_and_response_text(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output))
    try:
        generated = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
    finally:
        clear_dependencies()
    scenario_id = generated.json()["task_id"]
    override_dependencies(session, learner)
    client = TestClient(app)
    try:
        missing_scenario = client.post("/api/scenario/submit", json={"response_text": "Decision"})
        missing_response = client.post("/api/scenario/submit", json={"scenario_id": scenario_id})
        legacy_shape = client.post("/api/scenario/submit", json={"task_id": scenario_id, "response": {"text": "Decision"}})
        whitespace = client.post("/api/scenario/submit", json={"scenario_id": scenario_id, "response_text": "   "})
    finally:
        clear_dependencies()
    assert missing_scenario.status_code == 422
    assert missing_response.status_code == 422
    assert legacy_shape.status_code == 422
    assert whitespace.status_code == 422
    assert session.scalar(select(func.count()).select_from(ScenarioAttempt)) == 0


def test_direct_submission_failure_preserves_attempt_without_evidence(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output))
    try:
        generated = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
    finally:
        clear_dependencies()
    failing = FailingEvaluator()
    override_dependencies(session, learner, evaluator=failing)
    try:
        response = TestClient(app).post("/api/scenario/submit", json={"scenario_id": generated.json()["task_id"], "response_text": "Decision"})
    finally:
        clear_dependencies()
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    attempt = session.execute(select(ScenarioAttempt)).scalars().all()
    assert len(attempt) == 1
    assert attempt[0].response_text == "Decision"
    assert attempt[0].status == "FAILED"
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == 0
    assert session.scalar(select(func.count()).select_from(Evidence)) == 0


def test_invalid_evaluator_output_preserves_failed_attempt_without_evidence(db):
    session, learner, _, competency, subskill = db
    output = generated_scenario(competency.id, subskill.id)
    override_dependencies(session, learner, FakeGenerator(output))
    try:
        generated = TestClient(app).post("/api/scenario-assessments", json={"competency_id": competency.id, "subskill_id": subskill.id})
    finally:
        clear_dependencies()
    invalid = {
        "scenario_id": "scenario-001",
        "competency_id": competency.id,
        "subskill_id": subskill.id,
        "evaluation": {"score": 8, "max_score": 10, "percentage": 80, "criterion_results": [], "overall_result": "partially_correct"},
        "feedback": {"summary": "invalid criteria"},
        "evidence": {"demonstrated_competency": True, "evidence_type": "scenario_assessment", "confidence": 0.8},
    }
    override_dependencies(session, learner, evaluator=RawEvaluator(invalid))
    try:
        response = TestClient(app).post("/api/scenario/submit", json={"scenario_id": generated.json()["task_id"], "response_text": "Decision"})
    finally:
        clear_dependencies()
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert session.scalar(select(func.count()).select_from(ScenarioEvaluation)) == 0
    assert session.scalar(select(func.count()).select_from(Evidence)) == 0