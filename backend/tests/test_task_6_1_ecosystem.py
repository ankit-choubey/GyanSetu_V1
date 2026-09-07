"""
backend/tests/test_task_6_1_ecosystem.py — Task 6.1 Ecosystem Integration Test Suite.

Verifies 20 required scenarios:
1. provider discovery
2. provider mode returned
3. provider health
4. resource synchronization
5. resource persistence
6. duplicate synchronization
7. invalid mapping
8. stale resource rejection
9. provider unavailable
10. launch available resource
11. launch unavailable resource
12. provider activity ID handling
13. outcome recording
14. outcome -> evidence
15. evidence -> competency state
16. learner isolation
17. unauthorized admin operation
18. idempotent outcome retry
19. sync failure preservation
20. provider mode cannot falsely report LIVE
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.user import User
from app.services.adapters import (
    AvailabilityStatus,
    HealthStatus,
    IGOTAdapter,
    InternalAdapter,
    NSSTAAdapter,
    TPACAdapter,
    VirtualLabAdapter,
    get_adapter_for_provider,
    list_all_adapters,
)
from app.services.ecosystem import CompetencyMappingService, EcosystemSyncService
from app.utils.security import create_access_token, hash_password


@pytest.fixture(scope="module", autouse=True)
def setup_module_data():
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
def learner_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    email = f"t61.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Task 6.1 Test Learner",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name.in_(["Administrator", "admin"]))).scalars().first()
    if not role:
        role = Role(name="Administrator", description="System Administrator")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    email = f"t61.admin.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("adminpass123"),
        full_name="Task 6.1 Test Admin",
        role_id=role.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    email = f"t61.other.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Task 6.1 Other Learner",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


# 1. Provider discovery
def test_01_provider_discovery(client: TestClient, learner_user: User):
    resp = client.get("/api/ecosystem/providers", headers=auth_h(learner_user))
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 5
    names = {p["provider"].upper() for p in providers}
    assert {"IGOT", "NSSTA", "TPAC", "VIRTUAL_LAB", "INTERNAL"}.issubset(names)


# 2. Provider mode returned
def test_02_provider_mode_returned(client: TestClient, learner_user: User):
    resp = client.get("/api/ecosystem/providers", headers=auth_h(learner_user))
    assert resp.status_code == 200
    modes = {p["provider"].upper(): p["mode"] for p in resp.json()}
    assert modes["IGOT"] == "REPLAY"
    assert modes["NSSTA"] == "REPLAY"
    assert modes["TPAC"] == "REPLAY"
    assert modes["VIRTUAL_LAB"] == "SANDBOX"
    assert modes["INTERNAL"] == "LIVE"


# 3. Provider health
def test_03_provider_health(client: TestClient, learner_user: User):
    resp = client.get("/api/ecosystem/providers/iGOT/health", headers=auth_h(learner_user))
    assert resp.status_code == 200
    health = resp.json()
    assert health["provider"] == "iGOT"
    assert health["status"] in ("HEALTHY", "DEGRADED", "UNAVAILABLE")
    assert health["latency_ms"] >= 0.0
    assert "checked_at" in health


# 4. Resource synchronization
def test_04_resource_synchronization(client: TestClient, admin_user: User):
    resp = client.post("/api/ecosystem/providers/iGOT/sync", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "iGOT"
    assert data["total_processed"] > 0
    assert "synced_at" in data


# 5. Resource persistence
def test_05_resource_persistence(db_session: Session):
    igot_items = db_session.execute(
        select(Intervention).where(Intervention.provider == "iGOT")
    ).scalars().all()
    assert len(igot_items) > 0
    sample = igot_items[0]
    assert sample.source_id is not None
    assert sample.title is not None
    assert sample.integration_mode == "REPLAY"


# 6. Duplicate synchronization
def test_06_duplicate_synchronization(client: TestClient, admin_user: User, db_session: Session):
    count_before = len(db_session.execute(select(Intervention).where(Intervention.provider == "iGOT")).scalars().all())
    resp = client.post("/api/ecosystem/providers/iGOT/sync", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["added_count"] == 0
    assert data["updated_count"] == data["total_processed"]
    count_after = len(db_session.execute(select(Intervention).where(Intervention.provider == "iGOT")).scalars().all())
    assert count_before == count_after


# 7. Invalid mapping
def test_07_invalid_mapping(db_session: Session):
    mapper = CompetencyMappingService(db_session)
    res_fake_comp = mapper.resolve_mapping("NonExistentAstrologyCompetency")
    assert res_fake_comp.status == "UNDER_REVIEW"
    assert res_fake_comp.competency_id is None

    # Subskill from different competency
    res_mismatch = mapper.resolve_mapping("Sampling Design", "CPI compilation")
    assert res_mismatch.status == "UNDER_REVIEW"
    assert res_mismatch.subskill_id is None

    # validate_mapping helper
    valid, _ = mapper.validate_mapping(competency_id=999999)
    assert valid is False


# 8. Stale resource rejection
def test_08_stale_resource_rejection(client: TestClient, db_session: Session, learner_user: User):
    comp = db_session.execute(select(Competency)).scalars().first()
    stale_item = Intervention(
        provider="TEST_ECOSYSTEM",
        title="Stale Verification Test Module",
        competency_id=comp.id if comp else 1,
        intervention_type="COURSE",
        modality="ONLINE_SELF_PACED",
        duration_minutes=30,
        difficulty="easy",
        source="ECOSYSTEM_SYNC",
        source_id="STALE-RES-T61",
        status="STALE",
        last_verified_at=datetime.now(timezone.utc) - timedelta(days=250),
    )
    db_session.add(stale_item)
    db_session.commit()
    db_session.refresh(stale_item)

    try:
        # Launching a STALE resource must fail with HTTP 400
        resp = client.post(f"/api/ecosystem/resources/{stale_item.id}/launch", headers=auth_h(learner_user))
        assert resp.status_code == 400
        assert "STALE" in resp.json()["detail"]
    finally:
        db_session.delete(stale_item)
        db_session.commit()


# 9. Provider unavailable
def test_09_provider_unavailable(client: TestClient, learner_user: User):
    adapter = get_adapter_for_provider("iGOT")
    adapter.set_simulated_availability(False)
    try:
        resp = client.get("/api/ecosystem/providers/iGOT/health", headers=auth_h(learner_user))
        assert resp.status_code == 200
        assert resp.json()["status"] == HealthStatus.UNAVAILABLE.value
    finally:
        adapter.set_simulated_availability(True)


# 10. Launch available resource
def test_10_launch_available_resource(client: TestClient, db_session: Session, learner_user: User):
    item = db_session.execute(
        select(Intervention).where(Intervention.provider == "INTERNAL", Intervention.status == "ACTIVE")
    ).scalars().first()
    assert item is not None
    resp = client.post(f"/api/ecosystem/resources/{item.id}/launch", headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "INTERNAL"
    assert data["status"] == "ACTIVE"
    assert data["provider_activity_id"] is not None


# 11. Launch unavailable resource
def test_11_launch_unavailable_resource(client: TestClient, db_session: Session, learner_user: User):
    item = db_session.execute(
        select(Intervention).where(Intervention.provider == "VIRTUAL_LAB", Intervention.status == "ACTIVE")
    ).scalars().first()
    assert item is not None
    adapter = get_adapter_for_provider("VIRTUAL_LAB")
    adapter.set_simulated_availability(False)
    try:
        resp = client.post(f"/api/ecosystem/resources/{item.id}/launch", headers=auth_h(learner_user))
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()
    finally:
        adapter.set_simulated_availability(True)


# 12. Provider activity ID handling
def test_12_provider_activity_id_handling(client: TestClient, db_session: Session, learner_user: User):
    item = db_session.execute(
        select(Intervention).where(Intervention.provider == "INTERNAL", Intervention.status == "ACTIVE")
    ).scalars().first()
    assert item is not None
    resp = client.post(f"/api/ecosystem/resources/{item.id}/launch", headers=auth_h(learner_user))
    assert resp.status_code == 200
    act_id = resp.json()["provider_activity_id"]
    assert act_id.startswith("int_act_")


# 13. Outcome recording
def test_13_outcome_recording(client: TestClient, db_session: Session, learner_user: User):
    item = db_session.execute(select(Intervention).where(Intervention.status == "ACTIVE")).scalars().first()
    assert item is not None
    resp = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={"status": "COMPLETED", "completion_score": 0.85, "has_post_assessment_evidence": False},
        headers=auth_h(learner_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["outcome_id"] is not None


# 14. Outcome -> evidence
def test_14_outcome_to_evidence(client: TestClient, db_session: Session, learner_user: User):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    item = db_session.execute(
        select(Intervention).where(Intervention.competency_id == comp.id, Intervention.status == "ACTIVE")
    ).scalars().first()
    assert item is not None

    resp = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={
            "status": "COMPLETED",
            "completion_score": 0.95,
            "has_post_assessment_evidence": True,
            "idempotency_key": f"key_ev_{uuid.uuid4().hex}",
        },
        headers=auth_h(learner_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["competency_updated"] is True
    assert data["evidence_id"] is not None

    ev = db_session.get(Evidence, data["evidence_id"])
    assert ev is not None
    assert ev.score == 0.95


# 15. Evidence -> competency state
def test_15_evidence_to_competency_state(client: TestClient, db_session: Session, learner_user: User):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    state_before = db_session.execute(
        select(CompetencyState).where(CompetencyState.user_id == learner_user.id, CompetencyState.competency_id == comp.id)
    ).scalar_one_or_none()
    m_before = state_before.mastery if state_before and state_before.mastery is not None else 0.0

    item = db_session.execute(
        select(Intervention).where(Intervention.competency_id == comp.id, Intervention.status == "ACTIVE")
    ).scalars().first()
    assert item is not None

    resp = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={
            "status": "COMPLETED",
            "completion_score": 0.98,
            "has_post_assessment_evidence": True,
            "idempotency_key": f"key_state_{uuid.uuid4().hex}",
        },
        headers=auth_h(learner_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["post_competency_mastery"] >= m_before


# 16. Learner isolation
def test_16_learner_isolation(client: TestClient, db_session: Session, learner_user: User, other_user: User):
    item = db_session.execute(select(Intervention).where(Intervention.status == "ACTIVE")).scalars().first()
    assert item is not None
    shared_key = f"iso_key_{uuid.uuid4().hex}"

    # Learner A records outcome
    resp_a = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={"status": "COMPLETED", "idempotency_key": shared_key},
        headers=auth_h(learner_user),
    )
    assert resp_a.status_code == 200

    # Learner B attempts to replay Learner A's outcome
    resp_b = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={"status": "COMPLETED", "idempotency_key": shared_key},
        headers=auth_h(other_user),
    )
    assert resp_b.status_code == 403


# 17. Unauthorized admin operation
def test_17_unauthorized_admin_operation(client: TestClient, learner_user: User):
    # Standard learner cannot invoke POST /api/ecosystem/sync
    resp = client.post("/api/ecosystem/sync", headers=auth_h(learner_user))
    assert resp.status_code == 403


# 18. Idempotent outcome retry
def test_18_idempotent_outcome_retry(client: TestClient, db_session: Session, learner_user: User):
    item = db_session.execute(select(Intervention).where(Intervention.status == "ACTIVE")).scalars().first()
    assert item is not None
    key = f"retry_key_{uuid.uuid4().hex}"

    resp1 = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={"status": "COMPLETED", "completion_score": 0.88, "idempotency_key": key},
        headers=auth_h(learner_user),
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["idempotent_replay"] is False

    # Exact same request retry
    resp2 = client.post(
        f"/api/ecosystem/resources/{item.id}/outcome",
        json={"status": "COMPLETED", "completion_score": 0.88, "idempotency_key": key},
        headers=auth_h(learner_user),
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["idempotent_replay"] is True
    assert data2["outcome_id"] == data1["outcome_id"]


# 19. Sync failure preservation
def test_19_sync_failure_preservation(client: TestClient, admin_user: User, db_session: Session):
    count_before = len(db_session.execute(select(Intervention).where(Intervention.provider == "NSSTA")).scalars().all())
    adapter = get_adapter_for_provider("NSSTA")
    adapter.set_simulated_availability(False)
    try:
        resp = client.post("/api/ecosystem/providers/NSSTA/sync", headers=auth_h(admin_user))
        assert resp.status_code == 200
        # Data in database should remain preserved, not deleted
        count_after = len(db_session.execute(select(Intervention).where(Intervention.provider == "NSSTA")).scalars().all())
        assert count_after == count_before
    finally:
        adapter.set_simulated_availability(True)


# 20. Provider mode cannot falsely report LIVE
def test_20_provider_mode_cannot_falsely_report_live():
    igot = IGOTAdapter()
    assert igot.get_integration_mode().value != "LIVE" or bool(igot._live_api_key and igot._live_api_base)
    nssta = NSSTAAdapter()
    assert nssta.get_integration_mode().value == "REPLAY"
    tpac = TPACAdapter()
    assert tpac.get_integration_mode().value == "REPLAY"
    vlab = VirtualLabAdapter()
    assert vlab.get_integration_mode().value == "SANDBOX"
