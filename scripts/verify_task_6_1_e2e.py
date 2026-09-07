"""
scripts/verify_task_6_1_e2e.py — Task 6.1 Ecosystem Integration Runtime E2E Verifier.

Executes real HTTP requests through FastAPI TestClient across all 20 required scenarios:
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

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select

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


def run_verification() -> bool:
    print("=" * 80)
    print("TASK 6.1 — ECOSYSTEM ADAPTERS RUNTIME E2E VERIFICATION")
    print("=" * 80)

    db = SessionLocal()
    client = TestClient(app)

    try:
        # Setup Test Users
        role_officer = db.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
        role_admin = db.execute(select(Role).where(Role.name.in_(["Administrator", "admin"]))).scalar_one_or_none()
        if not role_admin:
            role_admin = Role(name="Administrator", description="System Administrator")
            db.add(role_admin)
            db.commit()
            db.refresh(role_admin)

        learner = User(
            email=f"e2e61.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in",
            password_hash=hash_password("password123"),
            full_name="E2E 6.1 Learner",
            role_id=role_officer.id if role_officer else None,
            is_active=True,
        )
        admin = User(
            email=f"e2e61.admin.{uuid.uuid4().hex[:6]}@mospi.gov.in",
            password_hash=hash_password("adminpass123"),
            full_name="E2E 6.1 Admin",
            role_id=role_admin.id,
            is_active=True,
        )
        other_user = User(
            email=f"e2e61.other.{uuid.uuid4().hex[:6]}@mospi.gov.in",
            password_hash=hash_password("password123"),
            full_name="E2E 6.1 Other",
            role_id=role_officer.id if role_officer else None,
            is_active=True,
        )
        db.add_all([learner, admin, other_user])
        db.commit()
        db.refresh(learner)
        db.refresh(admin)
        db.refresh(other_user)

        token_learner = create_access_token(subject=learner.id)
        token_admin = create_access_token(subject=admin.id)
        token_other = create_access_token(subject=other_user.id)

        h_learner = {"Authorization": f"Bearer {token_learner}"}
        h_admin = {"Authorization": f"Bearer {token_admin}"}
        h_other = {"Authorization": f"Bearer {token_other}"}

        step = 0
        passes = 0

        # Step 1: Provider Discovery
        step += 1
        r = client.get("/api/ecosystem/providers", headers=h_learner)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        providers = r.json()
        assert len(providers) >= 5
        print(f"[{step:02d}/20] PASS: Provider discovery returned {len(providers)} registered providers.")
        passes += 1

        # Step 2: Provider Mode Returned
        step += 1
        modes = {p["provider"].upper(): p["mode"] for p in providers}
        assert modes["IGOT"] == "REPLAY" and modes["VIRTUAL_LAB"] == "SANDBOX" and modes["INTERNAL"] == "LIVE"
        print(f"[{step:02d}/20] PASS: Provider modes explicitly reported (IGOT={modes['IGOT']}, VIRTUAL_LAB={modes['VIRTUAL_LAB']}, INTERNAL={modes['INTERNAL']}).")
        passes += 1

        # Step 3: Provider Health
        step += 1
        r = client.get("/api/ecosystem/providers/iGOT/health", headers=h_learner)
        assert r.status_code == 200
        health = r.json()
        assert health["status"] in ("HEALTHY", "DEGRADED", "UNAVAILABLE")
        print(f"[{step:02d}/20] PASS: Provider health check verified for iGOT (status={health['status']}, latency={health['latency_ms']}ms).")
        passes += 1

        # Step 4: Resource Synchronization
        step += 1
        r = client.post("/api/ecosystem/providers/iGOT/sync", headers=h_admin)
        assert r.status_code == 200
        sync_res = r.json()
        assert sync_res["total_processed"] > 0
        print(f"[{step:02d}/20] PASS: Resource synchronization executed for iGOT ({sync_res['total_processed']} processed).")
        passes += 1

        # Step 5: Resource Persistence
        step += 1
        db_items = db.execute(select(Intervention).where(Intervention.provider == "iGOT")).scalars().all()
        assert len(db_items) > 0
        print(f"[{step:02d}/20] PASS: Resource persistence confirmed ({len(db_items)} items in DB for provider iGOT).")
        passes += 1

        # Step 6: Duplicate Synchronization
        step += 1
        count_before = len(db_items)
        r = client.post("/api/ecosystem/providers/iGOT/sync", headers=h_admin)
        assert r.status_code == 200
        data2 = r.json()
        assert data2["added_count"] == 0
        count_after = len(db.execute(select(Intervention).where(Intervention.provider == "iGOT")).scalars().all())
        assert count_before == count_after
        print(f"[{step:02d}/20] PASS: Duplicate synchronization idempotency verified (0 duplicates added).")
        passes += 1

        # Step 7: Invalid Mapping
        step += 1
        mapper = CompetencyMappingService(db)
        res_fake = mapper.resolve_mapping("InvalidFictionalCompetency")
        assert res_fake.status == "UNDER_REVIEW" and res_fake.competency_id is None
        res_cross = mapper.resolve_mapping("Sampling Design", "InvalidSubskill999")
        assert res_cross.status == "UNDER_REVIEW"
        print(f"[{step:02d}/20] PASS: Invalid/unmatched taxonomy mappings safely quarantined under review.")
        passes += 1

        # Step 8: Stale Resource Rejection
        step += 1
        comp = db.execute(select(Competency)).scalars().first()
        stale_item = Intervention(
            provider="iGOT",
            title="E2E Stale Item",
            competency_id=comp.id if comp else 1,
            intervention_type="COURSE",
            modality="ONLINE_SELF_PACED",
            duration_minutes=30,
            difficulty="easy",
            source="ECOSYSTEM_SYNC",
            source_id="STALE-E2E-001",
            status="STALE",
            last_verified_at=datetime.now(timezone.utc) - timedelta(days=220),
        )
        db.add(stale_item)
        db.commit()
        db.refresh(stale_item)

        r_stale = client.post(f"/api/ecosystem/resources/{stale_item.id}/launch", headers=h_learner)
        assert r_stale.status_code == 400
        print(f"[{step:02d}/20] PASS: Stale resource launch rejected with HTTP 400.")
        passes += 1

        # Step 9: Provider Unavailable
        step += 1
        adapter = get_adapter_for_provider("iGOT")
        adapter.set_simulated_availability(False)
        try:
            r_unavail = client.get("/api/ecosystem/providers/iGOT/health", headers=h_learner)
            assert r_unavail.status_code == 200 and r_unavail.json()["status"] == HealthStatus.UNAVAILABLE.value
            print(f"[{step:02d}/20] PASS: Simulated provider outage correctly diagnosed as UNAVAILABLE.")
            passes += 1
        finally:
            adapter.set_simulated_availability(True)

        # Step 10: Launch Available Resource
        step += 1
        active_item = db.execute(
            select(Intervention).where(Intervention.provider == "INTERNAL", Intervention.status == "ACTIVE")
        ).scalars().first()
        assert active_item is not None
        r_launch = client.post(f"/api/ecosystem/resources/{active_item.id}/launch", headers=h_learner)
        assert r_launch.status_code == 200
        l_data = r_launch.json()
        assert l_data["status"] == "ACTIVE"
        print(f"[{step:02d}/20] PASS: Available internal resource launched successfully ({l_data['provider_activity_id']}).")
        passes += 1

        # Step 11: Launch Unavailable Resource
        step += 1
        vlab_item = db.execute(
            select(Intervention).where(Intervention.provider == "VIRTUAL_LAB", Intervention.status == "ACTIVE")
        ).scalars().first()
        assert vlab_item is not None
        vlab_adapter = get_adapter_for_provider("VIRTUAL_LAB")
        vlab_adapter.set_simulated_availability(False)
        try:
            r_vlab_unavail = client.post(f"/api/ecosystem/resources/{vlab_item.id}/launch", headers=h_learner)
            assert r_vlab_unavail.status_code == 503
            print(f"[{step:02d}/20] PASS: Outage during resource launch safely failed with HTTP 503.")
            passes += 1
        finally:
            vlab_adapter.set_simulated_availability(True)

        # Step 12: Provider Activity ID Handling
        step += 1
        assert l_data["provider_activity_id"].startswith("int_act_")
        print(f"[{step:02d}/20] PASS: Provider activity ID generated with verified prefix: {l_data['provider_activity_id']}.")
        passes += 1

        # Step 13: Outcome Recording
        step += 1
        r_out = client.post(
            f"/api/ecosystem/resources/{active_item.id}/outcome",
            json={"status": "COMPLETED", "completion_score": 0.85, "has_post_assessment_evidence": False},
            headers=h_learner,
        )
        assert r_out.status_code == 200
        out_data = r_out.json()
        assert out_data["status"] == "COMPLETED"
        print(f"[{step:02d}/20] PASS: Outcome recorded successfully without post-assessment evidence (Outcome ID {out_data['outcome_id']}).")
        passes += 1

        # Step 14: Outcome -> Evidence
        step += 1
        comp_target = db.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
        comp_id = comp_target.id if comp_target else 1
        comp_item = db.execute(
            select(Intervention).where(Intervention.competency_id == comp_id, Intervention.status == "ACTIVE")
        ).scalars().first()
        assert comp_item is not None

        r_out_ev = client.post(
            f"/api/ecosystem/resources/{comp_item.id}/outcome",
            json={
                "status": "COMPLETED",
                "completion_score": 0.92,
                "has_post_assessment_evidence": True,
                "idempotency_key": f"e2e_key_ev_{uuid.uuid4().hex}",
            },
            headers=h_learner,
        )
        assert r_out_ev.status_code == 200
        ev_data = r_out_ev.json()
        assert ev_data["competency_updated"] is True
        assert ev_data["evidence_id"] is not None
        print(f"[{step:02d}/20] PASS: Validated outcome with post-assessment generated Evidence ID {ev_data['evidence_id']}.")
        passes += 1

        # Step 15: Evidence -> Competency State
        step += 1
        assert ev_data["post_competency_mastery"] is not None
        print(f"[{step:02d}/20] PASS: Atomic competency recalculation updated mastery to {ev_data['post_competency_mastery']:.4f}.")
        passes += 1

        # Step 16: Learner Isolation
        step += 1
        shared_key = f"e2e_iso_{uuid.uuid4().hex}"
        r_iso_1 = client.post(
            f"/api/ecosystem/resources/{active_item.id}/outcome",
            json={"status": "COMPLETED", "idempotency_key": shared_key},
            headers=h_learner,
        )
        assert r_iso_1.status_code == 200

        r_iso_2 = client.post(
            f"/api/ecosystem/resources/{active_item.id}/outcome",
            json={"status": "COMPLETED", "idempotency_key": shared_key},
            headers=h_other,
        )
        assert r_iso_2.status_code == 403
        print(f"[{step:02d}/20] PASS: Cross-learner idempotency key conflict rejected with HTTP 403.")
        passes += 1

        # Step 17: Unauthorized Admin Operation
        step += 1
        r_unauth = client.post("/api/ecosystem/sync", headers=h_learner)
        assert r_unauth.status_code == 403
        print(f"[{step:02d}/20] PASS: Learner attempt to trigger administrative sync rejected with HTTP 403.")
        passes += 1

        # Step 18: Idempotent Outcome Retry
        step += 1
        retry_key = f"e2e_retry_{uuid.uuid4().hex}"
        r_ret_1 = client.post(
            f"/api/ecosystem/resources/{active_item.id}/outcome",
            json={"status": "COMPLETED", "completion_score": 0.82, "idempotency_key": retry_key},
            headers=h_learner,
        )
        assert r_ret_1.status_code == 200
        d_ret_1 = r_ret_1.json()

        r_ret_2 = client.post(
            f"/api/ecosystem/resources/{active_item.id}/outcome",
            json={"status": "COMPLETED", "completion_score": 0.82, "idempotency_key": retry_key},
            headers=h_learner,
        )
        assert r_ret_2.status_code == 200
        d_ret_2 = r_ret_2.json()
        assert d_ret_2["idempotent_replay"] is True and d_ret_2["outcome_id"] == d_ret_1["outcome_id"]
        print(f"[{step:02d}/20] PASS: Outcome retry idempotency verified (idempotent_replay=True).")
        passes += 1

        # Step 19: Sync Failure Preservation
        step += 1
        nssta_count_before = len(db.execute(select(Intervention).where(Intervention.provider == "NSSTA")).scalars().all())
        nssta_adapter = get_adapter_for_provider("NSSTA")
        nssta_adapter.set_simulated_availability(False)
        try:
            r_sync_fail = client.post("/api/ecosystem/providers/NSSTA/sync", headers=h_admin)
            assert r_sync_fail.status_code == 200
            nssta_count_after = len(db.execute(select(Intervention).where(Intervention.provider == "NSSTA")).scalars().all())
            assert nssta_count_before == nssta_count_after
            print(f"[{step:02d}/20] PASS: Sync failure preservation verified; existing data remained intact ({nssta_count_after} items).")
            passes += 1
        finally:
            nssta_adapter.set_simulated_availability(True)

        # Step 20: Provider Mode Cannot Falsely Report LIVE
        step += 1
        igot_inst = IGOTAdapter()
        assert igot_inst.get_integration_mode().value != "LIVE" or bool(igot_inst._live_api_key and igot_inst._live_api_base)
        print(f"[{step:02d}/20] PASS: Provider mode truth in advertising verified; unconfigured live APIs run in REPLAY mode.")
        passes += 1

        print("=" * 80)
        print(f"RESULT: {passes}/{step} SCENARIOS PASSED")
        print("=" * 80)
        return passes == step

    finally:
        db.close()


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
