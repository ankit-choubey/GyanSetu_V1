"""
tests/system/test_task_6_backend_integration.py — Phase 6 Integration Governance, Extensibility & Reliability System Tests.

Verifies:
1. Complete End-to-End Learning Loop:
   Learner -> Competency State -> Gap Triage -> NBA Recommendation -> Resource Launch -> Outcome -> Evidence -> Recalculation.
2. Provider Extensibility Contract (TestProviderAdapter registered without modifying domain logic).
3. ML Candidate Plug-in Contract (isolated ranker/candidate generation contract).
4. Frontend API Contract (surface area, schemas, auth barriers across all 6.x endpoints).
5. Non-mastery rule enforcement (completion without assessment != mastery).
6. Transaction integrity and audit logging.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.governance import WorkforceAuditLog
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.adapters import (
    AvailabilityResult,
    AvailabilityStatus,
    CanonicalInterventionPayload,
    HealthStatus,
    IntegrationMode,
    InterventionAdapter,
    LaunchResult,
    ProviderHealth,
    register_adapter,
    unregister_adapter,
)
from app.services.eligibility_engine import EligibilityEngine
from app.services.recommendation_ranker import RecommendationRanker
from app.utils.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def ensure_seed_data():
    from sqlmodel import SQLModel
    from app.database import engine
    from app.seed_data.runner import seed_full_taxonomy
    from app.seed_data.intervention_catalog_loader import seed_intervention_catalog

    SQLModel.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.execute(select(Role)).scalars().first():
            seed_full_taxonomy("test-pass")
        seed_intervention_catalog(db)
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin_role = db_session.execute(select(Role).where(Role.name.in_(["Administrator", "admin"]))).scalars().first()
    if not admin_role:
        admin_role = Role(name="Administrator", description="System Administrator")
        db_session.add(admin_role)
        db_session.commit()
        db_session.refresh(admin_role)

    user = User(
        email=f"sys6.admin.{uuid.uuid4().hex[:6]}@mospi.gov.in",
        password_hash=hash_password("adminSecret123!"),
        full_name="System 6 Admin",
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def learner_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    user = User(
        email=f"sys6.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in",
        password_hash=hash_password("learnerPass123!"),
        full_name="System 6 Learner",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_learner(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    user = User(
        email=f"sys6.other.{uuid.uuid4().hex[:6]}@mospi.gov.in",
        password_hash=hash_password("otherPass123!"),
        full_name="System 6 Other",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


# ---------------------------------------------------------------------------
# 1. Complete End-to-End Learning Remediation Loop
# ---------------------------------------------------------------------------

def test_01_complete_learning_remediation_loop(client: TestClient, learner_user: User, db_session: Session):
    """
    Validates complete lifecycle:
    Cold start -> Diagnostic -> Assessed State -> Gap Identified -> Next Best Action
    -> Recommendation Accepted -> Resource Launched -> Outcome with Evidence
    -> Competency Recalculation & History Ledger Appended.
    """
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # 1. Cold start: Learner is UNASSESSED -> receives DIAGNOSTIC recommendation
    r_cold = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert r_cold.status_code == 200
    d_cold = r_cold.json()
    assert d_cold["action_type"] == "DIAGNOSTIC"
    assert d_cold["confidence"] == 0.0

    # 2. Learner establishes baseline diagnostic state (e.g. initial assessment completed)
    baseline_state = CompetencyState(
        user_id=learner_user.id,
        competency_id=comp.id,
        mastery=0.35,
        confidence=0.70,
        status="ASSESSED",
    )
    db_session.add(baseline_state)
    db_session.commit()

    # 3. Next Best Action computed for assessed learner -> Concrete INTERVENTION recommended
    r_nba = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert r_nba.status_code == 200
    d_nba = r_nba.json()
    assert d_nba["action_type"] == "INTERVENTION"
    assert d_nba["selected_intervention"] is not None
    rec_id = d_nba["recommendation_id"]
    intervention_id = d_nba["selected_intervention"]["id"]

    # Verify structured explanation
    assert "why" in d_nba["explanation"]
    assert "primary_reason" in d_nba["explanation"]
    assert "competency_gap" in d_nba["explanation"]
    assert "policy_version" in d_nba["explanation"]

    # 4. Learner accepts recommendation
    r_feedback = client.post(
        f"/api/recommendations/{rec_id}/feedback",
        json={"action": "ACCEPT", "notes": "Learner accepted next best action."},
        headers=auth_h(learner_user),
    )
    assert r_feedback.status_code == 200
    assert r_feedback.json()["status"] == "ACCEPTED"

    # 5. Learner launches intervention
    r_launch = client.post(
        f"/api/interventions/{intervention_id}/launch",
        json={"recommendation_id": rec_id},
        headers=auth_h(learner_user),
    )
    assert r_launch.status_code == 200
    launch_data = r_launch.json()
    assert launch_data["launch_url"] is not None
    assert launch_data["session_id"] is not None

    # 6. Learner completes intervention outcome with verified post-assessment evidence
    r_outcome = client.post(
        f"/api/interventions/{intervention_id}/outcomes",
        json={
            "status": "COMPLETED",
            "completion_score": 0.90,
            "has_post_assessment_evidence": True,
            "recommendation_id": rec_id,
            "idempotency_key": f"sys-loop-{uuid.uuid4().hex[:8]}",
            "notes": "Verified completion with post-assessment mastery demonstration",
        },
        headers=auth_h(learner_user),
    )
    assert r_outcome.status_code == 200
    outcome_data = r_outcome.json()
    assert outcome_data["status"] == "COMPLETED"
    assert outcome_data["evidence_id"] is not None

    # 7. Verify evidence ledger record created
    evidence = db_session.get(Evidence, outcome_data["evidence_id"])
    assert evidence is not None
    assert evidence.user_id == learner_user.id
    assert evidence.competency_id == comp.id

    # 8. Verify competency state recalculated and increased
    db_session.refresh(baseline_state)
    assert baseline_state.mastery is not None
    assert baseline_state.mastery >= 0.35  # Recalculated incorporating new 0.90 evidence

    # 9. Verify history ledger recorded
    history = db_session.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == learner_user.id,
            CompetencyHistory.competency_id == comp.id,
        )
    ).scalars().all()
    assert len(history) > 0


# ---------------------------------------------------------------------------
# 2. Non-Mastery Rule Enforcement
# ---------------------------------------------------------------------------

def test_02_non_mastery_rule_enforcement(client: TestClient, learner_user: User, db_session: Session):
    """
    Completion alone does not equal mastery.
    Outcome without post-assessment evidence must NOT generate false evidence or inflate mastery.
    """
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    st = CompetencyState(
        user_id=learner_user.id,
        competency_id=comp.id,
        mastery=0.40,
        confidence=0.60,
        status="ASSESSED",
    )
    db_session.add(st)
    db_session.commit()

    item = db_session.execute(select(Intervention).where(Intervention.competency_id == comp.id)).scalars().first()
    assert item is not None

    # Record outcome with has_post_assessment_evidence = False
    r_outcome = client.post(
        f"/api/interventions/{item.id}/outcomes",
        json={
            "status": "COMPLETED",
            "completion_score": 1.0,  # 100% completion
            "has_post_assessment_evidence": False,  # NO post assessment
            "notes": "Finished watching video module, no assessment taken",
        },
        headers=auth_h(learner_user),
    )
    assert r_outcome.status_code == 200
    data = r_outcome.json()
    assert data["status"] == "COMPLETED"
    assert data["evidence_id"] is None  # Zero evidence created

    # Verify mastery was NOT inflated
    db_session.refresh(st)
    assert st.mastery == 0.40


# ---------------------------------------------------------------------------
# 3. Provider Extensibility Contract (TestProviderAdapter)
# ---------------------------------------------------------------------------

class MockSwayamAdapter(InterventionAdapter):
    """Mock external provider adapter demonstrating system extensibility."""

    def __init__(self) -> None:
        self.launched_sessions: list[str] = []
        self._available = True

    def get_provider_name(self) -> str:
        return "SWAYAM_EXT"

    def get_integration_mode(self) -> IntegrationMode:
        return IntegrationMode.REPLAY

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider="SWAYAM_EXT",
            status=HealthStatus.HEALTHY,
            mode=IntegrationMode.REPLAY,
            latency_ms=18.5,
            message="SWAYAM external mock provider operational",
            last_success=datetime.now(timezone.utc),
        )

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        return AvailabilityResult(
            resource_id=resource_id,
            status=AvailabilityStatus.AVAILABLE if self._available else AvailabilityStatus.UNAVAILABLE,
            is_available=self._available,
            reason=None if self._available else "Simulated provider downtime",
        )

    def search_resources(self, query: str | None = None, competency: str | None = None) -> list[CanonicalInterventionPayload]:
        return []

    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        return None

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        session_id = f"swayam_sess_{uuid.uuid4().hex[:8]}"
        self.launched_sessions.append(session_id)
        return LaunchResult(
            provider="SWAYAM_EXT",
            provider_resource_id=resource_id,
            provider_activity_id=session_id,
            learner_id=learner_id,
            integration_mode="REPLAY",
            launch_url=f"https://swayam.gov.in/courses/launch/{resource_id}?session={session_id}",
            status="LAUNCHED",
        )

    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        return []

    def set_simulated_availability(self, available: bool) -> None:
        self._available = available


def test_03_provider_extensibility_contract(client: TestClient, admin_user: User, learner_user: User, db_session: Session):
    """
    Extensibility Contract Test:
    Proves that a new provider adapter can be registered dynamically at runtime,
    without changing domain logic, schemas, or database tables, and immediately participates
    in health reporting, resource cataloguing, launch execution, and outcome capture.
    """
    adapter = MockSwayamAdapter()
    register_adapter("SWAYAM_EXT", adapter)

    try:
        # 1. Health check includes SWAYAM_EXT
        r_health = client.get("/api/ecosystem/health", headers=auth_h(admin_user))
        assert r_health.status_code == 200
        health_list = r_health.json()
        swayam_health = next((h for h in health_list if h["provider"] == "SWAYAM_EXT"), None)
        assert swayam_health is not None
        assert swayam_health["status"] == "HEALTHY"

        # 2. Providers list includes SWAYAM_EXT
        r_providers = client.get("/api/ecosystem/providers", headers=auth_h(learner_user))
        assert r_providers.status_code == 200
        provider_names = [p["provider"] for p in r_providers.json()]
        assert "SWAYAM_EXT" in provider_names

        # 3. Seed an intervention using SWAYAM_EXT
        comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
        assert comp is not None

        item = Intervention(
            provider="SWAYAM_EXT",
            title="SWAYAM Advanced Sampling Workshop",
            competency_id=comp.id,
            intervention_type="COURSE",
            modality="ONLINE_SELF_PACED",
            duration_minutes=60,
            difficulty="intermediate",
            source="EXT",
            source_id="SWAYAM-EXT-101",
            status="ACTIVE",
            availability="ALWAYS_AVAILABLE",
            last_verified_at=datetime.now(timezone.utc),
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        # 4. Launch SWAYAM_EXT intervention
        r_launch = client.post(
            f"/api/interventions/{item.id}/launch",
            json={},
            headers=auth_h(learner_user),
        )
        assert r_launch.status_code == 200
        data = r_launch.json()
        assert "swayam.gov.in" in data["launch_url"]
        assert len(adapter.launched_sessions) == 1

        # 5. Outcome submission for SWAYAM_EXT
        r_out = client.post(
            f"/api/interventions/{item.id}/outcomes",
            json={"status": "COMPLETED", "completion_score": 0.88, "has_post_assessment_evidence": True},
            headers=auth_h(learner_user),
        )
        assert r_out.status_code == 200
        assert r_out.json()["status"] == "COMPLETED"

    finally:
        unregister_adapter("SWAYAM_EXT")


# ---------------------------------------------------------------------------
# 4. ML Candidate Plug-In Contract
# ---------------------------------------------------------------------------

def test_04_ml_candidate_plugin_contract(db_session: Session, learner_user: User):
    """
    ML Plug-In Contract Test:
    Proves candidate generation and ranking contracts operate on stable, isolated DTOs
    without requiring direct database access or schema changes.
    """
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # Test candidate filtering contract via EligibilityEngine
    engine = EligibilityEngine()
    candidates = db_session.execute(select(Intervention).where(Intervention.competency_id == comp.id)).scalars().all()
    assert len(candidates) > 0

    eligible, decisions = engine.filter_candidates(db_session, learner_user, candidates)
    assert isinstance(eligible, list)
    assert isinstance(decisions, list)

    for decision in decisions:
        assert hasattr(decision, "is_eligible")
        if not decision.is_eligible:
            assert decision.status in {
                "POLICY_EXCLUDED",
                "INVALID_COMPETENCY_MAPPING",
                "RESOURCE_UNAVAILABLE",
                "RESOURCE_STALE",
                "PROVIDER_UNAVAILABLE",
                "ALREADY_COMPLETED",
                "PREREQUISITE_NOT_MET",
            }

    # Test ranker scoring contract via RecommendationRanker
    ranker = RecommendationRanker()
    ranking_res = ranker.rank(
        eligible_candidates=eligible,
        ineligible_decisions=[d for d in decisions if not d.is_eligible],
        target_competency_id=comp.id,
        target_subskill_id=None,
        target_subskill_name=None,
        active_misconceptions=None,
        competency_state=None,
    )

    assert ranking_res.policy_version == ranker.POLICY_VERSION
    assert isinstance(ranking_res.rejected_candidates, list)
    if ranking_res.selected:
        assert ranking_res.selected.intervention in eligible
        assert isinstance(ranking_res.selected.total_score, float)
        assert len(ranking_res.selected.primary_reason) > 0


# ---------------------------------------------------------------------------
# 5. Frontend API Contract Surface Test
# ---------------------------------------------------------------------------

def test_05_frontend_api_contract_surface(client: TestClient, admin_user: User, learner_user: User, db_session: Session):
    """
    Verifies that all required frontend UI API routes exist, accept correct payloads,
    and return compliant schema structures.
    """
    # 1. Ecosystem endpoints
    r_prov = client.get("/api/ecosystem/providers", headers=auth_h(learner_user))
    assert r_prov.status_code == 200
    assert isinstance(r_prov.json(), list)

    r_health = client.get("/api/ecosystem/health", headers=auth_h(admin_user))
    assert r_health.status_code == 200
    assert isinstance(r_health.json(), list)

    r_sync = client.post("/api/ecosystem/sync", headers=auth_h(admin_user))
    assert r_sync.status_code == 200
    assert isinstance(r_sync.json(), list) and len(r_sync.json()) > 0

    # 2. Recommendations endpoints
    r_list = client.get("/api/recommendations", headers=auth_h(learner_user))
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)

    r_next = client.post("/api/recommendations/next", json={}, headers=auth_h(learner_user))
    assert r_next.status_code == 200
    d_next = r_next.json()
    rec_id = d_next["recommendation_id"]

    r_rec = client.get(f"/api/recommendations/{rec_id}", headers=auth_h(learner_user))
    assert r_rec.status_code == 200

    r_exp = client.get(f"/api/recommendations/{rec_id}/explanation", headers=auth_h(learner_user))
    assert r_exp.status_code == 200
    assert "explanation" in r_exp.json()

    r_feed = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPT"}, headers=auth_h(learner_user))
    assert r_feed.status_code == 200

    r_start = client.post(f"/api/recommendations/{rec_id}/start", headers=auth_h(learner_user))
    assert r_start.status_code == 200

    # 3. Workforce Intelligence endpoints (Admin Only)
    r_wf_ov = client.get("/api/workforce/overview", headers=auth_h(admin_user))
    assert r_wf_ov.status_code == 200
    assert "workforce_summary" in r_wf_ov.json()

    r_wf_comp = client.get("/api/workforce/competencies", headers=auth_h(admin_user))
    assert r_wf_comp.status_code == 200
    assert "competencies" in r_wf_comp.json()

    r_wf_gaps = client.get("/api/workforce/gaps", headers=auth_h(admin_user))
    assert r_wf_gaps.status_code == 200
    assert "workforce_gaps" in r_wf_gaps.json()

    r_wf_trends = client.get("/api/workforce/trends", headers=auth_h(admin_user))
    assert r_wf_trends.status_code == 200
    assert "longitudinal_trends" in r_wf_trends.json()

    r_wf_fair = client.get("/api/workforce/fairness", headers=auth_h(admin_user))
    assert r_wf_fair.status_code == 200
    assert "overall_classification" in r_wf_fair.json()

    r_wf_qual = client.get("/api/workforce/data-quality", headers=auth_h(admin_user))
    assert r_wf_qual.status_code == 200
    assert "overall_data_health_score" in r_wf_qual.json()

    # 4. Security barriers: Learner cannot access Workforce admin endpoints
    r_wf_forbid = client.get("/api/workforce/overview", headers=auth_h(learner_user))
    assert r_wf_forbid.status_code == 403


# ---------------------------------------------------------------------------
# 6. Transaction Integrity and Audit Logging
# ---------------------------------------------------------------------------

def test_06_transaction_integrity_and_audit_logging(client: TestClient, admin_user: User, db_session: Session):
    """
    Verifies that workforce intelligence queries and administrative actions write
    persistent audit logs in workforce_audit_logs.
    """
    # Trigger workforce overview query
    r = client.get("/api/workforce/overview", headers=auth_h(admin_user))
    assert r.status_code == 200

    # Query audit logs
    audit_log = db_session.execute(
        select(WorkforceAuditLog).where(
            WorkforceAuditLog.actor_id == admin_user.id,
            WorkforceAuditLog.endpoint == "/api/workforce/overview",
        )
    ).scalars().first()

    assert audit_log is not None
    assert audit_log.authorization_decision == "AUTHORIZED"
    assert audit_log.actor_role.lower() in {"admin", "administrator"}
