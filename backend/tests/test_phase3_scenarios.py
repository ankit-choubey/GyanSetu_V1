from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.competency import Competency, CompetencyDomain, Role, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.adapters.provider_adapters import get_adapter_for_provider


from sqlalchemy.pool import StaticPool

@pytest.fixture
def scenario_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()

    # Seed Role
    role = Role(name="Statistical Officer", description="Role")
    db.add(role)
    db.flush()

    # Seed Competencies
    comp1 = Competency(
        role_id=role.id,
        name="Sampling Design",
        domain=CompetencyDomain.STATISTICAL,
        description="Sampling competency",
    )
    comp2 = Competency(
        role_id=role.id,
        name="Data Quality",
        domain=CompetencyDomain.STATISTICAL,
        description="Data Quality competency",
    )
    db.add_all([comp1, comp2])
    db.flush()

    # Seed Subskills
    sub1 = SubSkill(competency_id=comp1.id, name="Stratified sampling")
    sub2 = SubSkill(competency_id=comp1.id, name="Probability sampling")
    db.add_all([sub1, sub2])
    db.flush()

    # Role Competency link
    rc1 = RoleCompetency(role_id=role.id, competency_id=comp1.id, required_level=0.75)
    rc2 = RoleCompetency(role_id=role.id, competency_id=comp2.id, required_level=0.80)
    db.add_all([rc1, rc2])
    db.flush()

    # Seed Learners
    learner_a = User(id=1, email="learner.a@mospi.gov.in", full_name="Learner A", password_hash="pw", role_id=role.id)
    learner_b = User(id=2, email="learner.b@mospi.gov.in", full_name="Learner B", password_hash="pw", role_id=role.id)
    db.add_all([learner_a, learner_b])

    # Seed Seeded Interventions
    interv1 = Intervention(
        id=101,
        source_id="TEST-INT-101",
        title="Scenario Practice: Stratified Sampling in Field Surveys",
        competency_id=comp1.id,
        subskill_id=sub1.id,
        intervention_type="scenario_practice",
        provider="INTERNAL",
        modality="PRACTICE_SCENARIO",
        status="ACTIVE",
        priority=1,
    )
    interv2 = Intervention(
        id=102,
        source_id="TEST-INT-102",
        title="Interactive Probability Sampling Lab",
        competency_id=comp1.id,
        subskill_id=sub2.id,
        intervention_type="virtual_lab",
        provider="VIRTUAL_LAB",
        modality="VIRTUAL_LAB",
        status="ACTIVE",
        priority=2,
    )
    interv_misc = Intervention(
        id=103,
        source_id="TEST-INT-103",
        title="Concept Repair: Stratified vs Cluster Sampling",
        competency_id=comp1.id,
        subskill_id=sub1.id,
        intervention_type="remediation",
        provider="INTERNAL",
        modality="PRACTICE_SCENARIO",
        target_misconception_pattern="CONFUSED_STRATIFIED_WITH_CLUSTER",
        status="ACTIVE",
        priority=1,
    )
    interv_unavail = Intervention(
        id=104,
        source_id="TEST-INT-104",
        title="High Performance Computing Cluster Drill",
        competency_id=comp1.id,
        subskill_id=sub1.id,
        intervention_type="virtual_lab",
        provider="VIRTUAL_LAB",
        modality="VIRTUAL_LAB",
        status="UNAVAILABLE",
        availability="UNAVAILABLE",
        priority=1,
    )

    db.add_all([interv1, interv2, interv_misc, interv_unavail])
    db.commit()

    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def client(scenario_db: Session):
    def override_get_db():
        yield scenario_db

    # Default auth as learner A
    def override_get_current_user():
        return scenario_db.get(User, 1)

    from app.database import get_db as db_get_db
    from app.dependencies import get_db as dep_get_db, get_current_user as dep_get_user
    from app.routers.intervention import get_db as router_get_db, get_current_user as router_get_user

    app.dependency_overrides[db_get_db] = override_get_db
    app.dependency_overrides[dep_get_db] = override_get_db
    app.dependency_overrides[router_get_db] = override_get_db
    app.dependency_overrides[dep_get_user] = override_get_current_user
    app.dependency_overrides[router_get_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ==============================================================================
# SCENARIO A — Known Competency Gap
# ==============================================================================
def test_scenario_a_known_competency_gap(client: TestClient, scenario_db: Session):
    """Scenario A: Seeded competency state with a gap -> next-best-action selected with explanation."""
    # Give Learner A existing state with gap (mastery 0.35, confidence 0.60)
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.35,
        confidence=0.60,
        status="ASSESSED",
    )
    scenario_db.add(state)
    scenario_db.commit()

    response = client.post("/api/recommendations/next-best-action", json={"competency_id": 1})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["action_type"] == "INTERVENTION"
    assert data["selected_intervention"] is not None
    assert data["selected_intervention"]["competency_id"] == 1
    assert data["selected_intervention"]["id"] == 101  # Highest priority subskill match

    explanation = data["explanation"]
    assert "positive_factors" in explanation
    assert len(explanation["positive_factors"]) > 0

    # Verify candidate rejections contains other candidates
    assert len(data["rejected_candidates"]) > 0
    statuses = {c["status"] for c in data["rejected_candidates"]}
    assert "UNAVAILABLE" in statuses or "LOWER_RANKED" in statuses


# ==============================================================================
# SCENARIO B — Misconception-Aware Intervention
# ==============================================================================
def test_scenario_b_misconception_aware_intervention(client: TestClient, scenario_db: Session):
    """Scenario B: Learner has active misconception -> Recommendation prioritizes specific remediation."""
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.50,
        confidence=0.60,
        status="ASSESSED",
    )
    misc = Misconception(
        learner_id=1,
        competency_id=1,
        subskill_id=1,
        pattern_key="CONFUSED_STRATIFIED_WITH_CLUSTER",
        misconception_type="sampling_confusion",
        description="Confused stratified with cluster",
        occurrences=2,
        resolved=False,
    )
    scenario_db.add_all([state, misc])
    scenario_db.commit()

    response = client.post("/api/recommendations/next-best-action", json={"competency_id": 1})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # The remediation intervention (ID 103) should be selected over generic practice (ID 101)
    assert data["selected_intervention"]["id"] == 103
    assert data["selected_intervention"]["target_misconception_pattern"] == "CONFUSED_STRATIFIED_WITH_CLUSTER"
    assert any("misconception" in f.lower() for f in data["explanation"]["positive_factors"])


# ==============================================================================
# SCENARIO C — Cold Start (Unassessed Learner)
# ==============================================================================
def test_scenario_c_cold_start(client: TestClient, scenario_db: Session):
    """Scenario C: New learner with no evidence -> System does NOT invent low mastery, recommends diagnostic."""
    # Learner A has no evidence and no competency state records
    response = client.post("/api/recommendations/next-best-action", json={"competency_id": 1})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["action_type"] == "DIAGNOSTIC"
    assert data["selected_intervention"] is None
    assert "diagnostic" in data["objective"].lower()
    assert "UNASSESSED" in data["explanation"]["why"]


# ==============================================================================
# SCENARIO D — Unavailable Provider Fallback
# ==============================================================================
def test_scenario_d_unavailable_provider_fallback(client: TestClient, scenario_db: Session):
    """Scenario D: External provider unavailable -> Disqualified, alternative eligible candidate selected."""
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.45,
        confidence=0.50,
        status="ASSESSED",
    )
    scenario_db.add(state)
    scenario_db.commit()

    # Force VIRTUAL_LAB provider adapter failure
    vlab_adapter = get_adapter_for_provider("VIRTUAL_LAB")
    vlab_adapter.set_simulated_availability(False)

    try:
        response = client.post("/api/recommendations/next-best-action", json={"competency_id": 1})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # The VIRTUAL_LAB intervention (ID 102) must NOT be selected
        assert data["selected_intervention"]["provider"] != "VIRTUAL_LAB"
        assert data["selected_intervention"]["id"] == 101

        # Check rejection log has UNAVAILABLE for provider failure
        rejections = data["rejected_candidates"]
        vlab_rejection = next((r for r in rejections if r["intervention_id"] == 102), None)
        assert vlab_rejection is not None
        assert vlab_rejection["status"] == "UNAVAILABLE"
    finally:
        vlab_adapter.set_simulated_availability(True)


# ==============================================================================
# SCENARIO E — Outcome Feedback Loop & State Update
# ==============================================================================
def test_scenario_e_outcome_feedback_state_update(client: TestClient, scenario_db: Session):
    """Scenario E: Recommendation -> Accepted -> Started -> Completed with Evidence -> State Updated."""
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.30,
        confidence=0.20,
        status="ASSESSED",
    )
    scenario_db.add(state)
    scenario_db.commit()

    # 1. Get recommendation
    rec_res = client.post("/api/recommendations/next-best-action", json={"competency_id": 1})
    rec_id = rec_res.json()["recommendation_id"]

    # 2. Accept recommendation
    feed_res = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPTED"})
    assert feed_res.status_code == status.HTTP_200_OK
    assert feed_res.json()["status"] == "ACCEPTED"

    # 3. Start intervention
    start_res = client.post(f"/api/recommendations/{rec_id}/start")
    assert start_res.status_code == status.HTTP_200_OK
    assert start_res.json()["status"] == "STARTED"

    # 4. Complete with post-assessment evidence (Score: 0.90)
    outcome_res = client.post(
        "/api/interventions/101/outcome",
        json={
            "status": "COMPLETED",
            "completion_score": 0.90,
            "has_post_assessment_evidence": True,
            "recommendation_id": rec_id,
        },
    )
    assert outcome_res.status_code == status.HTTP_200_OK
    outcome_data = outcome_res.json()

    assert outcome_data["status"] == "COMPLETED"
    assert outcome_data["evidence_id"] is not None
    assert outcome_data["post_competency_mastery"] is not None
    # Mastery increased from 0.30 due to high score on practical task
    assert outcome_data["post_competency_mastery"] > 0.30

    # Verify new evidence was actually written to ledger
    new_ev = scenario_db.get(Evidence, outcome_data["evidence_id"])
    assert new_ev is not None
    assert new_ev.score == 0.90
    assert new_ev.source == "INTERVENTION_POST_ASSESSMENT"


# ==============================================================================
# SCENARIO F — Completion Without Evidence Does NOT Change Mastery
# ==============================================================================
def test_scenario_f_completion_without_evidence(client: TestClient, scenario_db: Session):
    """Scenario F: Activity completed without post-assessment evidence -> Mastery is UNCHANGED."""
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.42,
        confidence=0.50,
        status="ASSESSED",
    )
    scenario_db.add(state)
    scenario_db.commit()

    outcome_res = client.post(
        "/api/interventions/101/outcome",
        json={
            "status": "COMPLETED",
            "completion_score": None,
            "has_post_assessment_evidence": False,
        },
    )
    assert outcome_res.status_code == status.HTTP_200_OK
    outcome_data = outcome_res.json()

    assert outcome_data["status"] == "COMPLETED"
    assert outcome_data["evidence_id"] is None
    # Crucial scientific check: mastery must remain identical!
    assert outcome_data["post_competency_mastery"] == 0.42
    assert "competency unchanged" in outcome_data["notes"]


# ==============================================================================
# SCENARIO G — Duplicate / Idempotency Protection
# ==============================================================================
def test_scenario_g_idempotency_protection(client: TestClient, scenario_db: Session):
    """Scenario G: Submitting the same outcome twice with idempotency key does not duplicate evidence or state."""
    state = CompetencyState(
        user_id=1,
        competency_id=1,
        mastery=0.40,
        confidence=0.40,
        status="ASSESSED",
    )
    scenario_db.add(state)
    scenario_db.commit()

    key = "mospi-submission-guid-998877"
    payload = {
        "status": "COMPLETED",
        "completion_score": 0.85,
        "has_post_assessment_evidence": True,
        "idempotency_key": key,
    }

    # First submission
    res1 = client.post("/api/interventions/101/outcome", json=payload)
    assert res1.status_code == status.HTTP_200_OK
    out1_id = res1.json()["id"]
    ev1_id = res1.json()["evidence_id"]

    # Second submission with same idempotency key
    res2 = client.post("/api/interventions/101/outcome", json=payload)
    assert res2.status_code == status.HTTP_200_OK
    out2_id = res2.json()["id"]
    ev2_id = res2.json()["evidence_id"]

    # Must return existing record without generating duplicate evidence
    assert out1_id == out2_id
    assert ev1_id == ev2_id

    total_ev = scenario_db.query(Evidence).filter_by(user_id=1, source="INTERVENTION_POST_ASSESSMENT").count()
    assert total_ev == 1


# ==============================================================================
# SCENARIO H — Learner Isolation & Authorization
# ==============================================================================
def test_scenario_h_learner_isolation(client: TestClient, scenario_db: Session):
    """Scenario H: Learner A cannot access Learner B's recommendation explanation."""
    # Create recommendation for Learner B (User ID 2)
    rec_b = RecommendationRecord(
        recommendation_id="rec_learner_b_secret",
        user_id=2,
        competency_id=1,
        action_type="INTERVENTION",
        status="RECOMMENDED",
        confidence=0.75,
    )
    scenario_db.add(rec_b)
    scenario_db.commit()

    # Current client is authenticated as Learner A (User ID 1)
    res = client.get("/api/recommendations/rec_learner_b_secret/explanation")
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "prohibited" in res.json()["detail"].lower()

    # Attempt feedback on Learner B's recommendation
    feed_res = client.post(
        "/api/recommendations/rec_learner_b_secret/feedback",
        json={"action": "ACCEPTED"},
    )
    assert feed_res.status_code == status.HTTP_403_FORBIDDEN
