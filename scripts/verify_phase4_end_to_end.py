"""
scripts/verify_phase4_end_to_end.py — Phase 4 End-to-End Real-Time Verification.

Executes the complete operational Phase 4 ecosystem integration flow:
1. Provider Registry Discovery (GET /api/ecosystem/providers)
   - iGOT (REPLAY with fallback disclosure)
   - NSSTA (REPLAY with fallback disclosure)
   - TPAC (REPLAY with fallback disclosure)
   - Virtual Lab (SANDBOX mode)
   - Native GyanSetu Engine (LIVE mode)
2. Provider Health Checks (GET /api/ecosystem/providers/{provider}/health)
3. Provider Ingestion & Sync (POST /api/ecosystem/providers/{provider}/sync)
4. Deduplication & Idempotent Harvest Verification
5. Canonical Taxonomy Mapping (External Terminology -> MoSPI Competencies)
6. Ecosystem Intervention Launch Protocol (POST /api/ecosystem/resources/{id}/launch)
7. Non-Mastery Rule Enforcement (Completion without Assessment != Mastery)
8. Verified Outcome Submission (Evidence Emission + Atomic Competency Recalculation)
9. Fault Injection & Fallback Resilience (Simulated Outage Handling)
10. Stale Resource Validity Window (180-day Expiry Policy)
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend and root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

# Change CWD to backend directory so SQLite relative paths resolve identically to server
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlmodel import SQLModel

from app.database import SessionLocal, engine
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
from app.seed_data.runner import seed_full_taxonomy
from app.services.adapters import get_adapter_for_provider


def run_phase4_verification() -> bool:
    print("=" * 80)
    print("GYANSETU PHASE 4 — ECOSYSTEM ADAPTERS & INTEGRATION VERIFICATION")
    print("=" * 80)

    SQLModel.metadata.create_all(engine)
    db = SessionLocal()

    try:
        # 1. Initialize Baseline DB Environment
        print("\n[Step 0] Initializing Baseline Data Environment...")
        roles_count = db.execute(select(Role)).scalars().all()
        if not roles_count:
            seed_full_taxonomy(db)
            print("[+] Seeded official MoSPI competency taxonomy.")
        seed_intervention_catalog(db)
        print("[+] Seeded foundational intervention catalog.")

        # Ensure active learner exists
        learner_email = f"phase4.officer.{uuid.uuid4().hex[:6]}@mospi.gov.in"
        role = db.execute(select(Role)).scalars().first()
        learner = User(
            email=learner_email,
            password_hash="phase4_secure_hash",
            full_name="Phase 4 Integration Verification Officer",
            role_id=role.id if role else 1,
            is_active=True,
        )
        db.add(learner)
        db.commit()
        db.refresh(learner)

        from app.dependencies import get_current_user
        fastapi_app.dependency_overrides[get_current_user] = lambda: learner
        client = TestClient(fastapi_app)
        headers: dict[str, str] = {}
        print(f"[+] Authenticated Learner: {learner.full_name} (ID: #{learner.id})")

        # Step 1: Provider Registry Discovery
        print("\n[Step 1] Discovering Ecosystem Providers (GET /api/ecosystem/providers)...")
        res = client.get("/api/ecosystem/providers", headers=headers)
        assert res.status_code == 200, f"Provider listing failed: {res.text}"
        providers = res.json()
        print(f"[+] Discovered {len(providers)} registered providers:")
        provider_names = {p["provider"].upper(): p for p in providers}
        expected_providers = ["IGOT", "NSSTA", "TPAC", "VIRTUAL_LAB", "INTERNAL"]
        for exp in expected_providers:
            assert exp in provider_names, f"Expected provider '{exp}' not found in registry"
            info = provider_names[exp]
            print(f"    - {info['provider']:<12} | Mode: {info['mode']:<8} | Status: {info['status']} | Latency: {info['latency_ms']}ms")


        # Verify explicit REPLAY mode reporting for external platforms without live keys
        assert provider_names["IGOT"]["mode"] == "REPLAY"
        assert provider_names["NSSTA"]["mode"] == "REPLAY"
        assert provider_names["TPAC"]["mode"] == "REPLAY"
        assert provider_names["VIRTUAL_LAB"]["mode"] == "SANDBOX"
        assert provider_names["INTERNAL"]["mode"] == "LIVE"
        print("[+] Verified explicit mode distinction (Zero false claims of LIVE credentials).")

        # Step 2: Individual Provider Health Checks
        print("\n[Step 2] Performing Provider Health Inspections...")
        for p_name in ["IGOT", "VIRTUAL_LAB", "INTERNAL"]:
            h_res = client.get(f"/api/ecosystem/providers/{p_name}/health", headers=headers)
            assert h_res.status_code == 200
            h_data = h_res.json()
            assert h_data["provider"].upper() == p_name.upper()
            assert h_data["status"] == "HEALTHY"
            print(f"[+] Health Check {p_name}: status={h_data['status']} latency={h_data['latency_ms']}ms resources={h_data['resource_count']}")


        # Step 3: Provider Resource Sync & Ingestion
        print("\n[Step 3] Synchronizing Virtual Lab Resources (POST /api/ecosystem/providers/VIRTUAL_LAB/sync)...")
        sync_res = client.post("/api/ecosystem/providers/VIRTUAL_LAB/sync", headers=headers)
        assert sync_res.status_code == 200
        s_data = sync_res.json()
        print(f"[+] Virtual Lab Sync Result:")
        print(f"    - Total Processed: {s_data['total_processed']}")
        print(f"    - Added:           {s_data['added_count']}")
        print(f"    - Updated:         {s_data['updated_count']}")
        print(f"    - Mode:            {s_data['mode']}")
        assert s_data["total_processed"] > 0

        # Step 4: Duplicate Sync Idempotency Check
        print("\n[Step 4] Verifying Sync Idempotency (Second Sync with same payloads)...")
        sync_res_2 = client.post("/api/ecosystem/providers/VIRTUAL_LAB/sync", headers=headers)
        assert sync_res_2.status_code == 200
        s2_data = sync_res_2.json()
        assert s2_data["added_count"] == 0, f"Expected 0 new creations on duplicate sync, got {s2_data['added_count']}"
        assert s2_data["updated_count"] == s_data["total_processed"]
        print(f"[+] Sync Idempotency Confirmed: Added 0 duplicate entries, correctly updated existing {s2_data['updated_count']} records.")


        # Step 5: Canonical Taxonomy Mapping Resolution
        print("\n[Step 5] Checking Canonical Competency Resolution in Catalogue (GET /api/ecosystem/resources)...")
        cat_res = client.get("/api/ecosystem/resources?provider=VIRTUAL_LAB", headers=headers)
        assert cat_res.status_code == 200
        vlab_items = cat_res.json()
        assert len(vlab_items) > 0
        sample_vlab = vlab_items[0]
        print(f"[+] Verified Canonical Resource Mapping:")
        print(f"    - Resource ID:    #{sample_vlab['id']} ({sample_vlab['source_id']})")
        print(f"    - Title:          '{sample_vlab['title']}'")
        print(f"    - Competency ID:  #{sample_vlab['competency_id']}")
        print(f"    - Mapping Status: {sample_vlab['mapping_status']}")
        print(f"    - Confidence:     {sample_vlab['mapping_confidence']}")
        print(f"    - Mode:           {sample_vlab['integration_mode']}")
        assert sample_vlab["mapping_status"] in {"VERIFIED", "CURATED"}

        # Step 6: Ecosystem Resource Launch Protocol
        print(f"\n[Step 6] Testing Resource Launch Protocol for Resource #{sample_vlab['id']}...")
        launch_res = client.post(f"/api/ecosystem/resources/{sample_vlab['id']}/launch", headers=headers)
        assert launch_res.status_code == 200
        l_data = launch_res.json()
        print(f"[+] Resource Launch Response:")
        print(f"    - Provider:             {l_data['provider']}")
        print(f"    - Provider Activity ID: {l_data['provider_activity_id']}")
        print(f"    - Launch URL:           {l_data['launch_url']}")
        print(f"    - Status:               {l_data['status']}")
        print(f"    - Mode:                 {l_data['integration_mode']}")
        assert l_data["status"] == "ACTIVE"
        assert l_data["provider_activity_id"] is not None
        provider_activity_id = l_data["provider_activity_id"]

        # Step 7: Non-Mastery Equivalence Enforcement
        print("\n[Step 7] Testing Non-Mastery Equivalence (Activity Completion without Assessment Evidence)...")
        # Ensure learner has assessed state for this competency
        comp_id = sample_vlab["competency_id"] or 1
        comp = db.get(Competency, comp_id)
        assert comp is not None

        c_state = CompetencyState(
            user_id=learner.id,
            competency_id=comp.id,
            mastery=0.40,
            confidence=0.65,
            status="ASSESSED",
        )
        db.add(c_state)
        db.commit()

        unverified_outcome = client.post(
            f"/api/ecosystem/resources/{sample_vlab['id']}/outcome",
            headers=headers,
            json={
                "provider_activity_id": provider_activity_id,
                "status": "COMPLETED",
                "completion_score": 0.88,
                "has_post_assessment_evidence": False,
                "notes": "Completed sandbox exercises without formal post-assessment proctoring",
            },
        )
        assert unverified_outcome.status_code == 200
        u_data = unverified_outcome.json()
        print(f"[+] Unverified Outcome Result:")
        print(f"    - Status:          {u_data['status']}")
        print(f"    - Evidence ID:     {u_data['evidence_id']} (Expected: None)")
        print(f"    - Pre-Mastery:     {u_data['pre_competency_mastery']:.2f}")
        print(f"    - Post-Mastery:    {u_data['post_competency_mastery']:.2f}")
        print(f"    - Updated:         {u_data['competency_updated']}")
        assert u_data["evidence_id"] is None
        assert u_data["post_competency_mastery"] == u_data["pre_competency_mastery"]
        assert u_data["competency_updated"] is False
        print("[+] Non-Mastery Rule Enforced: Activity completion alone did NOT inflate competency mastery.")

        # Step 8: Verified Outcome with Post-Assessment Evidence
        print("\n[Step 8] Testing Verified Outcome (with Verified Post-Assessment Evidence)...")
        verified_outcome = client.post(
            f"/api/ecosystem/resources/{sample_vlab['id']}/outcome",
            headers=headers,
            json={
                "provider_activity_id": f"act_eval_{uuid.uuid4().hex[:8]}",
                "status": "COMPLETED",
                "completion_score": 0.94,
                "has_post_assessment_evidence": True,
                "notes": "Interactive practical assessment passed with 94% accuracy score",
            },
        )
        assert verified_outcome.status_code == 200
        v_data = verified_outcome.json()
        print(f"[+] Verified Outcome Result:")
        print(f"    - Status:          {v_data['status']}")
        print(f"    - Evidence ID:     #{v_data['evidence_id']}")
        print(f"    - Pre-Mastery:     {v_data['pre_competency_mastery']:.2f}")
        print(f"    - Post-Mastery:    {v_data['post_competency_mastery']:.2f}")
        print(f"    - Updated:         {v_data['competency_updated']}")
        assert v_data["evidence_id"] is not None
        assert v_data["post_competency_mastery"] is not None
        assert v_data["competency_updated"] is True


        # Inspect Evidence Ledger entry
        ev_record = db.get(Evidence, v_data["evidence_id"])
        assert ev_record is not None
        print(f"[+] Evidence Ledger Record Verified:")
        print(f"    - Title:       '{ev_record.title}'")
        print(f"    - Type:        {ev_record.evidence_type}")
        print(f"    - Provenance:  {ev_record.provenance}")
        print(f"    - Score:       {ev_record.score}")
        assert ev_record.provenance in ("[SANDBOX DATA]", "[LIVE INTEGRATION]")
        assert "VIRTUAL_LAB" in ev_record.source

        # Step 9: Fault Injection & Fallback Resilience
        print("\n[Step 9] Simulating External Provider Outage & Fallback Resilience...")
        vlab_adapter = get_adapter_for_provider("VIRTUAL_LAB")
        vlab_adapter.set_simulated_availability(False)

        try:
            # Check availability directly
            avail = vlab_adapter.check_availability("VL-SAMP-01")
            print(f"[+] Outage Availability Check: is_available={avail.is_available} status={avail.status.value}")
            assert not avail.is_available

            # Check health endpoint under outage
            h_outage = client.get("/api/ecosystem/providers/VIRTUAL_LAB/health", headers=headers)
            assert h_outage.status_code == 200
            assert h_outage.json()["status"] == "UNAVAILABLE"
            print(f"[+] Outage Health Inspection: status={h_outage.json()['status']} details='{h_outage.json()['details']}'")

            # Verify launch rejection during outage
            bad_launch = client.post(f"/api/ecosystem/resources/{sample_vlab['id']}/launch", headers=headers)
            assert bad_launch.status_code in (400, 503)
            print(f"[+] Resilient Launch Guard: Correctly rejected launch with HTTP {bad_launch.status_code}: {bad_launch.json()['detail']}")

        finally:
            vlab_adapter.set_simulated_availability(True)

        # Step 10: Stale Resource Verification Window
        print("\n[Step 10] Testing 180-Day Staleness Policy...")
        # Create an intervention verified 200 days ago
        stale_item = Intervention(
            title="Archived 2018 Economic Census Protocol (Expired)",
            provider="NSSTA",
            source_id="NSSTA-STALE-ARCHIVE",
            competency_id=comp.id,
            modality="READING",
            intervention_type="curated",
            duration_minutes=90,
            difficulty="intermediate",
            status="ACTIVE",
            priority=3,
            is_active=True,
            last_verified_at=datetime.now(timezone.utc) - timedelta(days=200),
            mapping_status="VERIFIED",
            integration_mode="REPLAY",
        )
        db.add(stale_item)
        db.commit()
        db.refresh(stale_item)

        from app.services.eligibility_engine import EligibilityEngine
        ee = EligibilityEngine()
        decision = ee.evaluate_candidate(db, learner, stale_item)
        print(f"[+] Eligibility Evaluation on 200-day-old resource:")
        print(f"    - Is Eligible: {decision.is_eligible}")
        print(f"    - Status:      {decision.status}")
        print(f"    - Reason:      '{decision.reason}'")
        assert not decision.is_eligible
        assert decision.status == "STALE"

        print("\n" + "=" * 80)
        print("PHASE 4 END-TO-END VERIFICATION: SUCCESS [VERIFIED 🟢]")
        print("=" * 80)
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_phase4_verification()
    sys.exit(0 if success else 1)
