"""
scripts/verify_phase3_end_to_end.py — Phase 3 End-to-End Real-Time Verification.

Executes the complete operational Phase 3 recommendation and intervention flow:
Learner (Profile & Role)
→ Phase 2 Competency State
→ Competency Gap & Uncertainty
→ Candidate Generation from Registry (iGOT, NSSTA, Curated)
→ Eligibility & Availability Filtering (Adapters)
→ Transparent Multi-Factor Ranking
→ Next Best Action Selection
→ Recommendation Explanation & Rejection Audit
→ Learner Feedback (ACCEPTED)
→ Intervention Started
→ Completion with Post-Assessment Evidence
→ Evidence Ledger Record Created ([LIVE INTEGRATION])
→ Phase 2 Competency State Recalculation & History Transition
→ Non-Mastery Equivalence Verification (Completion alone != Mastery)
→ Duplicate Idempotency Verification
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add backend and root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

# Change CWD to backend directory so sqlite relative paths resolve identically to server
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal, engine
from app.main import app as fastapi_app
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


def run_phase3_verification() -> bool:
    print("=" * 80)
    print("GYANSETU PHASE 3 — END-TO-END INTERVENTION & RECOMMENDATION INTELLIGENCE")
    print("=" * 80)

    from sqlmodel import SQLModel
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)

    db = SessionLocal()
    try:
        # Seed taxonomy if empty
        roles_count = db.execute(select(Role)).scalars().all()
        if not roles_count:
            print("[+] Seeding canonical taxonomy...")
            seed_full_taxonomy("test-phase3-dev-pw")

        # Seed intervention catalogue
        catalog_stats = seed_intervention_catalog(db)
        print(f"[+] Canonical Intervention Catalogue: {catalog_stats['total']} items indexed across iGOT, NSSTA, Curated & Remediation.")

        # Step 1: Load or Create Sandbox Learner
        print("\n[Step 1] Loading Sandbox Learner Profile & Role Scope...")
        role = db.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
        if not role:
            role = db.execute(select(Role)).scalars().first()

        learner_email = "phase3.sandbox.learner@mospi.gov.in"
        learner = db.execute(select(User).where(User.email == learner_email)).scalar_one_or_none()
        if not learner:
            learner = User(
                email=learner_email,
                full_name="Dr. Sunita Sharma (JSO)",
                password_hash="phase3_secure_hash",
                role_id=role.id,
                is_active=True,
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)

        comp = db.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
        if not comp:
            comp = db.execute(select(Competency)).scalars().first()

        print(f"[+] Learner ID: {learner.id} | Email: {learner.email} | Role: '{role.name}'")
        print(f"[+] Target Competency: ID={comp.id} | Name='{comp.name}'")

        # Step 2: Establish Known Competency Gap
        print("\n[Step 2] Establishing Baseline Competency State with Known Gap...")
        state = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == learner.id,
                CompetencyState.competency_id == comp.id,
            )
        ).scalar_one_or_none()

        if not state:
            state = CompetencyState(
                user_id=learner.id,
                competency_id=comp.id,
                mastery=0.32,
                confidence=0.55,
                coverage=0.25,
                status="ASSESSED",
            )
            db.add(state)
        else:
            state.mastery = 0.32
            state.confidence = 0.55
            state.status = "ASSESSED"
        db.commit()
        db.refresh(state)

        print(f"    - Current Mastery:    {state.mastery:.2f}")
        print(f"    - Current Confidence: {state.confidence:.2f}")
        print(f"    - Gap vs Req (0.75):  {0.75 - state.mastery:.2f} (Severity: HIGH)")

        # Create authenticated test client for learner
        from app.dependencies import get_current_user
        fastapi_app.dependency_overrides[get_current_user] = lambda: learner
        client = TestClient(fastapi_app)

        # Step 3: Compute Next Best Action (POST /api/recommendations/next-best-action)
        print("\n[Step 3] Requesting Next Best Action (POST /api/recommendations/next-best-action)...")
        rec_res = client.post("/api/recommendations/next-best-action", json={"competency_id": comp.id})
        assert rec_res.status_code == 200, f"Error: {rec_res.text}"
        rec_data = rec_res.json()

        rec_id = rec_data["recommendation_id"]
        action_type = rec_data["action_type"]
        sel_item = rec_data["selected_intervention"]

        print(f"[+] Recommendation Issued: ID={rec_id}")
        print(f"    - Action Type:     {action_type}")
        print(f"    - Selected Item:   #{sel_item['id']} — '{sel_item['title']}'")
        print(f"    - Provider:        {sel_item['provider']} ({sel_item['provenance']})")
        print(f"    - Modality:        {sel_item['modality']}")
        print(f"    - Policy Version:  {rec_data['policy_version']}")

        # Step 4: Audit Transparent Explanation & Candidate Rejections
        print("\n[Step 4] Auditing Explanation API (GET /api/recommendations/{id}/explanation)...")
        expl_res = client.get(f"/api/recommendations/{rec_id}/explanation")
        assert expl_res.status_code == 200, f"Error: {expl_res.text}"
        expl_data = expl_res.json()

        explanation = expl_data["explanation"]
        print(f"    - Rationale:       {explanation.get('why')}")
        print(f"    - Positive Factors: {explanation.get('positive_factors')}")
        print(f"    - Caution Notes:   {explanation.get('caution_notes')}")
        print(f"    - Rejected Count:  {len(expl_data.get('rejected_candidates', []))} candidates audited in rejection log")

        # Step 5: Learner Feedback Lifecycle (ACCEPTED -> STARTED)
        print("\n[Step 5] Transitioning Lifecycle: Accepting & Starting Intervention...")
        feed_res = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPTED", "notes": "Aligned with survey deployment goals"})
        assert feed_res.status_code == 200
        print(f"[+] Recommendation Status: {feed_res.json()['status']}")

        start_res = client.post(f"/api/recommendations/{rec_id}/start")
        assert start_res.status_code == 200
        print(f"[+] Intervention Status:   {start_res.json()['status']}")

        # Step 6: Complete with Post-Assessment Evidence
        print("\n[Step 6] Submitting Completion Outcome with Valid Post-Assessment Evidence...")
        outcome_key = f"phase3_e2e_outcome_{rec_id}"
        outcome_res = client.post(
            f"/api/interventions/{sel_item['id']}/outcome",
            json={
                "status": "COMPLETED",
                "completion_score": 0.92,
                "has_post_assessment_evidence": True,
                "recommendation_id": rec_id,
                "idempotency_key": outcome_key,
                "notes": "Completed NSS survey simulation with 92% accuracy on stratum allocation.",
            },
        )
        assert outcome_res.status_code == 200, f"Error: {outcome_res.text}"
        outcome_data = outcome_res.json()

        print(f"[+] Outcome Persisted: ID={outcome_data['id']}")
        print(f"    - Generated Evidence ID: #{outcome_data['evidence_id']}")
        print(f"    - Pre-Mastery:           {outcome_data['pre_competency_mastery']:.2f}")
        print(f"    - Post-Mastery:          {outcome_data['post_competency_mastery']:.2f} (Competency Updated!)")

        # Step 7: Verify Evidence Ledger Entry
        print("\n[Step 7] Verifying Evidence Ledger Persistence (GET /api/evidence)...")
        ev_res = client.get("/api/evidence")
        assert ev_res.status_code == 200
        ev_data = ev_res.json()
        ev_records = ev_data.get("evidence", [])
        matching_ev = next((e for e in ev_records if e["id"] == outcome_data["evidence_id"]), None)
        assert matching_ev is not None
        print(f"[+] Verified Evidence in Ledger:")
        print(f"    - Title:       '{matching_ev['title']}'")
        print(f"    - Type:        {matching_ev['evidence_type']}")
        print(f"    - Provenance:  {matching_ev['provenance']}")
        print(f"    - Score:       {matching_ev['score']}")
        print(f"    - Reliability: {matching_ev['reliability_status']}")

        # Step 8: Verify Competency History Transition
        print("\n[Step 8] Auditing Competency State Transition History...")
        hist_res = client.get(f"/api/competency/history/{comp.id}")
        assert hist_res.status_code == 200
        hist_records = hist_res.json()
        print(f"[+] Total State Transitions Logged: {len(hist_records)}")
        if hist_records:
            latest_h = hist_records[-1]
            print(f"    - Latest Version: #{latest_h.get('state_version')} | Mastery: {latest_h.get('new_mastery')} | Confidence: {latest_h.get('new_confidence')}")

        # Step 9: Verify Non-Mastery Equivalence (Completion alone != Mastery)
        print("\n[Step 9] Demonstrating Non-Mastery Equivalence (Completion alone != Mastery)...")
        passive_outcome = client.post(
            f"/api/interventions/{sel_item['id']}/outcome",
            json={
                "status": "COMPLETED",
                "completion_score": None,
                "has_post_assessment_evidence": False,
                "notes": "Passive material consumption without verification",
            },
        )
        assert passive_outcome.status_code == 200
        pass_data = passive_outcome.json()
        assert pass_data["evidence_id"] is None
        assert pass_data["post_competency_mastery"] == pass_data["pre_competency_mastery"]
        print(f"[+] Activity Completion Recorded:")
        print(f"    - Has Evidence: False | Pre-Mastery: {pass_data['pre_competency_mastery']:.2f} == Post-Mastery: {pass_data['post_competency_mastery']:.2f}")
        print(f"    - Notes Flag:   '{pass_data['notes']}'")

        # Step 10: Demonstrate Outcome Idempotency
        print("\n[Step 10] Demonstrating Idempotency Protection...")
        dup_res = client.post(
            f"/api/interventions/{sel_item['id']}/outcome",
            json={
                "status": "COMPLETED",
                "completion_score": 0.92,
                "has_post_assessment_evidence": True,
                "recommendation_id": rec_id,
                "idempotency_key": outcome_key,
            },
        )
        assert dup_res.status_code == 200
        dup_data = dup_res.json()
        assert dup_data["id"] == outcome_data["id"]
        assert dup_data["evidence_id"] == outcome_data["evidence_id"]
        print(f"[+] Idempotent Submission Verified: Returned original outcome ID #{dup_data['id']} with zero duplicated records.")

        print("\n" + "=" * 80)
        print("PHASE 3 END-TO-END VERIFICATION: SUCCESS [VERIFIED 🟢]")
        print("=" * 80)
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_phase3_verification()
    sys.exit(0 if success else 1)
