from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.user import User
from app.services.adapters import get_adapter_for_provider
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
    email = f"phase4.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("test-password-phase4"),
        full_name="Phase 4 Test Officer",
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
    email = f"other.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("test-password-phase4"),
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
# SCENARIO A: Provider Discovery
# ==============================================================================
def test_scenario_a_provider_discovery(client: TestClient, test_learner: User):
    """Actual API request retrieves canonical interventions and provider health overview."""
    resp = client.get("/api/ecosystem/providers", headers=auth_headers(test_learner))
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 5

    names = {p["provider"].upper() for p in providers}
    assert {"IGOT", "NSSTA", "TPAC", "VIRTUAL_LAB", "INTERNAL"}.issubset(names)

    for p in providers:
        assert p["status"] in ("HEALTHY", "DEGRADED", "UNAVAILABLE")
        assert p["mode"] in ("LIVE", "SANDBOX", "REPLAY")
        assert p["latency_ms"] >= 0.0


# ==============================================================================
# SCENARIO B: Recommendation -> Provider Resolution
# ==============================================================================
def test_scenario_b_recommendation_to_provider(client: TestClient, db_session: Session, test_learner: User):
    """Verify that a Next Best Action recommendation resolves through the correct provider adapter."""
    # Seed a known gap in Sampling Design
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    state = CompetencyState(
        user_id=test_learner.id,
        competency_id=comp.id,
        mastery=0.35,
        confidence=0.6,
        status="ASSESSED",
    )
    db_session.add(state)
    db_session.commit()

    # Request Next Best Action
    rec_resp = client.post(
        "/api/recommendations/next-best-action",
        json={"competency_id": comp.id},
        headers=auth_headers(test_learner),
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["action_type"] == "INTERVENTION"
    intervention = rec_data["selected_intervention"]
    assert intervention is not None

    # Launch through ecosystem API
    launch_resp = client.post(
        f"/api/ecosystem/resources/{intervention['id']}/launch",
        headers=auth_headers(test_learner),
    )
    assert launch_resp.status_code == 200
    launch_data = launch_resp.json()
    assert launch_data["provider"] == intervention["provider"]
    assert launch_data["provider_activity_id"] is not None
    assert launch_data["status"] in ("ACTIVE", "INITIALIZED")


# ==============================================================================
# SCENARIO C: Provider Unavailable Fallback
# ==============================================================================
def test_scenario_c_provider_unavailable_fallback(client: TestClient, db_session: Session, test_learner: User):
    """Simulate primary provider outage and verify resilient fallback to an alternative candidate."""
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # Seed baseline gap state
    state = CompetencyState(
        user_id=test_learner.id,
        competency_id=comp.id,
        mastery=0.35,
        confidence=0.6,
        status="ASSESSED",
    )
    db_session.add(state)
    db_session.commit()

    # Disable INTERNAL provider temporarily
    internal_adapter = get_adapter_for_provider("INTERNAL")
    internal_adapter.set_simulated_availability(False)

    try:
        rec_resp = client.post(
            "/api/recommendations/next-best-action",
            json={"competency_id": comp.id},
            headers=auth_headers(test_learner),
        )
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        assert rec_data["action_type"] == "INTERVENTION"
        # Since INTERNAL is offline, recommendation must choose an available provider (e.g. VIRTUAL_LAB, iGOT, or NSSTA)
        assert rec_data["selected_intervention"]["provider"] != "INTERNAL"
    finally:
        internal_adapter.set_simulated_availability(True)


# ==============================================================================
# SCENARIO D: Stale Resource Rejection
# ==============================================================================
def test_scenario_d_stale_resource_rejection(client: TestClient, db_session: Session, test_learner: User):
    """Verify that resources older than 180 days are excluded from recommendations and marked STALE."""
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # Seed baseline gap state
    state = CompetencyState(
        user_id=test_learner.id,
        competency_id=comp.id,
        mastery=0.35,
        confidence=0.6,
        status="ASSESSED",
    )
    db_session.add(state)
    db_session.commit()

    stale_item = db_session.execute(
        select(Intervention).where(
            Intervention.competency_id == comp.id,
            Intervention.status == "STALE",
        )
    ).scalar_one_or_none()

    if not stale_item:
        stale_item = Intervention(
            provider="INTERNAL",
            title="Outdated MoSPI 2018 Sampling Reference",
            competency_id=comp.id,
            intervention_type="reading",
            modality="ONLINE_SELF_PACED",
            duration_minutes=30,
            difficulty="easy",
            source="SYSTEM",
            source_id="FIXTURE-STALE-001",
            status="STALE",
            last_verified_at=datetime.now(timezone.utc) - timedelta(days=200),
        )
        db_session.add(stale_item)
        db_session.commit()

    # Recommender must never pick the STALE item
    rec_resp = client.post(
        "/api/recommendations/next-best-action",
        json={"competency_id": comp.id},
        headers=auth_headers(test_learner),
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["selected_intervention"]["id"] != stale_item.id
    assert rec_data["selected_intervention"]["status"] == "ACTIVE"


# ==============================================================================
# SCENARIO E: Invalid Competency Mapping
# ==============================================================================
def test_scenario_e_invalid_competency_mapping(client: TestClient, db_session: Session, test_learner: User):
    """Verify that unverified/malformed external mappings are quarantined as UNDER_REVIEW."""
    from app.services.ecosystem import CompetencyMappingService

    mapper = CompetencyMappingService(db_session)
    res = mapper.resolve_mapping("Quantum Astrology Fortune Telling")
    assert res.status == "UNDER_REVIEW"
    assert res.competency_id is None
    assert "quarantined" in res.reason.lower()


# ==============================================================================
# SCENARIO F: Duplicate Synchronization Idempotency
# ==============================================================================
def test_scenario_f_duplicate_sync_idempotency(client: TestClient, test_learner: User):
    """Verify that repeated synchronization runs add 0 duplicate items."""
    # First sync
    resp1 = client.post("/api/ecosystem/providers/iGOT/sync", headers=auth_headers(test_learner))
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second sync immediately following
    resp2 = client.post("/api/ecosystem/providers/iGOT/sync", headers=auth_headers(test_learner))
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data2["added_count"] == 0
    assert data2["updated_count"] == data1["total_processed"]


# ==============================================================================
# SCENARIO G: Provider Mode Distinction
# ==============================================================================
def test_scenario_g_provider_mode_distinction(client: TestClient, test_learner: User):
    """Verify that API explicitly reports actual integration mode (REPLAY/SANDBOX vs LIVE)."""
    resp = client.get("/api/ecosystem/providers", headers=auth_headers(test_learner))
    assert resp.status_code == 200
    providers = {p["provider"].upper(): p for p in resp.json()}

    assert providers["IGOT"]["mode"] == "REPLAY"
    assert providers["NSSTA"]["mode"] == "REPLAY"
    assert providers["VIRTUAL_LAB"]["mode"] == "SANDBOX"
    assert providers["INTERNAL"]["mode"] == "LIVE"


# ==============================================================================
# SCENARIO H: Outcome Propagation to Evidence Ledger & Competency State
# ==============================================================================
def test_scenario_h_outcome_propagation(client: TestClient, db_session: Session, test_learner: User):
    """Verify provider intervention completion with verified post-assessment evidence updates competency state."""
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # Baseline competency
    state = CompetencyState(
        user_id=test_learner.id,
        competency_id=comp.id,
        mastery=0.40,
        confidence=0.5,
        status="ASSESSED",
    )
    db_session.add(state)
    db_session.commit()

    # Find an intervention for this competency
    intervention = db_session.execute(
        select(Intervention).where(
            Intervention.competency_id == comp.id,
            Intervention.status == "ACTIVE",
        )
    ).scalars().first()
    assert intervention is not None

    # Submit outcome with post-assessment score 0.90
    outcome_resp = client.post(
        f"/api/ecosystem/resources/{intervention.id}/outcome",
        json={
            "status": "COMPLETED",
            "completion_score": 0.90,
            "has_post_assessment_evidence": True,
            "provider_activity_id": "act_verified_123",
            "idempotency_key": f"key_{uuid.uuid4().hex}",
            "notes": "Verified post-assessment passed with 90%",
        },
        headers=auth_headers(test_learner),
    )
    assert outcome_resp.status_code == 200
    out_data = outcome_resp.json()
    assert out_data["competency_updated"] is True
    assert out_data["post_competency_mastery"] > 0.40

    # Verify Evidence record in database
    evidence = db_session.get(Evidence, out_data["evidence_id"])
    assert evidence is not None
    assert evidence.score == 0.90
    assert evidence.reliability_status == "VERIFIED"


# ==============================================================================
# SCENARIO I: Completion Without Mastery Evidence
# ==============================================================================
def test_scenario_i_completion_without_mastery_evidence(client: TestClient, db_session: Session, test_learner: User):
    """Verify that passive activity completion alone does NOT update competency mastery."""
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    # Baseline state
    state = db_session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == test_learner.id,
            CompetencyState.competency_id == comp.id,
        )
    ).scalar_one_or_none()
    if not state:
        state = CompetencyState(
            user_id=test_learner.id,
            competency_id=comp.id,
            mastery=0.45,
            confidence=0.5,
            status="ASSESSED",
        )
        db_session.add(state)
        db_session.commit()
    initial_mastery = state.mastery

    intervention = db_session.execute(
        select(Intervention).where(
            Intervention.competency_id == comp.id,
            Intervention.status == "ACTIVE",
        )
    ).scalars().first()
    assert intervention is not None

    # Submit completion WITHOUT post-assessment evidence
    outcome_resp = client.post(
        f"/api/ecosystem/resources/{intervention.id}/outcome",
        json={
            "status": "COMPLETED",
            "has_post_assessment_evidence": False,
            "idempotency_key": f"key_no_eval_{uuid.uuid4().hex}",
        },
        headers=auth_headers(test_learner),
    )
    assert outcome_resp.status_code == 200
    out_data = outcome_resp.json()
    assert out_data["competency_updated"] is False
    assert out_data["evidence_id"] is None
    assert out_data["post_competency_mastery"] == initial_mastery


# ==============================================================================
# SCENARIO J: Learner Isolation
# ==============================================================================
def test_scenario_j_learner_isolation(client: TestClient, db_session: Session, test_learner: User, other_learner: User):
    """Verify that cross-learner tampering with idempotency keys or outcomes is strictly rejected."""
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None

    intervention = db_session.execute(
        select(Intervention).where(Intervention.competency_id == comp.id)
    ).scalars().first()
    assert intervention is not None

    shared_key = f"shared_idemp_key_{uuid.uuid4().hex}"

    # Learner A submits outcome
    resp_a = client.post(
        f"/api/ecosystem/resources/{intervention.id}/outcome",
        json={
            "status": "COMPLETED",
            "has_post_assessment_evidence": False,
            "idempotency_key": shared_key,
        },
        headers=auth_headers(test_learner),
    )
    assert resp_a.status_code == 200

    # Learner B attempts to replay or access Learner A's outcome with the same idempotency key
    resp_b = client.post(
        f"/api/ecosystem/resources/{intervention.id}/outcome",
        json={
            "status": "COMPLETED",
            "has_post_assessment_evidence": False,
            "idempotency_key": shared_key,
        },
        headers=auth_headers(other_learner),
    )
    assert resp_b.status_code == 403
    assert "Idempotency key conflict" in resp_b.json()["detail"]
