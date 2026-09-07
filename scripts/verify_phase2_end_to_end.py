"""
scripts/verify_phase2_end_to_end.py — Phase 2 End-to-End Real-Time Verification.

Executes the complete Phase 2 competency and diagnostic pipeline:
synthetic/sandbox learner
→ role
→ required competencies
→ initial evidence
→ competency state (baseline)
→ diagnostic start (POST /api/diagnostic/start)
→ adaptive question selection with inspectable rationale
→ response submission (POST /api/diagnostic/respond)
→ evidence update in ledger
→ competency state & history update
→ misconception tracking
→ adaptive remediation question
→ diagnostic completion & stopping criteria
→ learner dashboard reflection (GET /api/dashboard/learner)
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

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app as fastapi_app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.misconception import Misconception
from app.models.user import User


def run_phase2_verification() -> bool:
    print("=" * 80)
    print("GYANSETU PHASE 2 — END-TO-END COMPETENCY STATE & ADAPTIVE DIAGNOSTIC")
    print("=" * 80)

    from sqlmodel import SQLModel
    from app.database import engine
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)

    db = SessionLocal()
    client = TestClient(fastapi_app)

    try:
        # Step 1: Ensure Sandbox Learner & Role
        print("\n[Step 1] Loading Sandbox Learner Profile & Role Scope...")
        role = db.execute(select(Role).where(Role.name == "Junior Statistical Officer")).scalar_one_or_none()
        if not role:
            role = db.execute(select(Role)).scalars().first()
            if not role:
                print("[-] Error: No roles found in database. Run taxonomy seeder first.")
                return False

        learner_email = "phase2.sandbox.learner@mospi.gov.in"
        learner = db.execute(select(User).where(User.email == learner_email)).scalar_one_or_none()
        if not learner:
            from app.utils.security import hash_password
            learner = User(
                email=learner_email,
                full_name="Sandbox Analyst (Phase 2)",
                password_hash=hash_password("sandbox-phase2-pass"),
                role_id=role.id,
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)

        print(f"[+] [SANDBOX DATA] Learner ID: {learner.id}, Email: {learner.email}, Role: {role.name}")

        # Find an assigned competency that has assessment items
        competencies = db.execute(
            select(Competency)
            .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
            .where(RoleCompetency.role_id == role.id)
            .order_by(Competency.id)
        ).scalars().all()

        target_comp = None
        for comp in competencies:
            count = db.execute(
                select(AssessmentItem).where(
                    AssessmentItem.competency_id == comp.id,
                    AssessmentItem.user_id.is_(None),
                )
            ).scalars().all()
            if len(count) >= 3:
                target_comp = comp
                break

        if not target_comp:
            print("[-] Error: Could not find competency with >= 3 candidate assessment items.")
            return False

        print(f"[+] Target Competency: ID={target_comp.id}, Name='{target_comp.name}'")

        # Reset previous test evidence/state for sandbox learner to verify fresh unassessed flow
        from app.models.diagnostic import DiagnosticItem, DiagnosticSession
        for ev in db.execute(select(Evidence).where(Evidence.user_id == learner.id, Evidence.competency_id == target_comp.id)).scalars().all():
            db.delete(ev)
        for ds in db.execute(select(DiagnosticSession).where(DiagnosticSession.user_id == learner.id, DiagnosticSession.competency_id == target_comp.id)).scalars().all():
            for di in ds.items:
                db.delete(di)
            db.delete(ds)
        prior_st = db.execute(select(CompetencyState).where(CompetencyState.user_id == learner.id, CompetencyState.competency_id == target_comp.id)).scalar_one_or_none()
        if prior_st:
            db.delete(prior_st)
        db.commit()

        # Step 2: Check Initial Competency State
        print("\n[Step 2] Querying Initial Competency State from System of Record...")
        st = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == learner.id,
                CompetencyState.competency_id == target_comp.id,
            )
        ).scalar_one_or_none()

        baseline_mastery = st.mastery if st else None
        baseline_conf = st.confidence if st else 0.0
        baseline_unc = st.uncertainty if st else 1.0
        baseline_status = st.status if st else "UNASSESSED"

        print(f"    - Mastery:     {baseline_mastery}")
        print(f"    - Confidence:  {baseline_conf:.2f}")
        print(f"    - Uncertainty: {baseline_unc:.2f}")
        print(f"    - Status:      {baseline_status}")

        # Authenticate TestClient as Sandbox Learner
        from app.dependencies import get_current_user
        fastapi_app.dependency_overrides[get_current_user] = lambda: learner

        # Step 3: Diagnostic Session Start (API)
        print("\n[Step 3] Initiating Adaptive Diagnostic Session (POST /api/diagnostic/start)...")
        start_payload = {"competency_id": target_comp.id, "max_questions": 3}
        resp = client.post("/api/diagnostic/start", json=start_payload)
        if resp.status_code != 200:
            print(f"[-] Diagnostic start failed: {resp.status_code} - {resp.text}")
            return False

        start_data = resp.json()
        session_id = start_data["session_id"]
        q1 = start_data["first_question"]
        if not q1:
            print("[-] No initial question returned by adaptive diagnostic start.")
            return False

        print(f"[+] [LIVE INTEGRATION] Diagnostic Session #{session_id} Initialized (Status: {start_data['status']})")
        print(f"    - Question 1 ID: {q1['question_id']}")
        print(f"    - Difficulty:    {q1['difficulty']}")
        print(f"    - Stem:          {q1['question_text'][:75]}...")
        print(f"    - Rationale:     {q1['selection_rationale']}")

        # Step 4: Respond Correctly to Question 1
        print("\n[Step 4] Submitting Response to Q1 (Correct Answer)...")
        source_item1 = db.get(AssessmentItem, q1["question_id"])
        ans1_resp = client.post(
            "/api/diagnostic/respond",
            json={
                "session_id": session_id,
                "assessment_item_id": q1["question_id"],
                "selected_option": source_item1.correct_option,
                "response_time_ms": 14200,
            },
        )
        if ans1_resp.status_code != 200:
            print(f"[-] Response submission failed: {ans1_resp.status_code} - {ans1_resp.text}")
            return False

        ans1_data = ans1_resp.json()
        print(f"[+] Response Evaluated: is_correct={ans1_data['is_correct']}, score={ans1_data['score']}")
        print(f"    - Updated Estimated Mastery: {ans1_data['updated_mastery']}")
        print(f"    - Updated Confidence:        {ans1_data['updated_confidence']:.2f}")
        print(f"    - Updated Uncertainty:       {ans1_data['updated_uncertainty']:.2f}")

        q2 = ans1_data["next_question"]
        if not q2:
            print("[-] Expected adaptive question 2, got None.")
            return False

        print(f"[+] Next Question Served: ID={q2['question_id']}, Difficulty='{q2['difficulty']}'")
        print(f"    - Rationale: {q2['selection_rationale']}")

        # Step 5: Respond Incorrectly to Question 2 (Trigger Misconception Tracking & Remediation)
        print("\n[Step 5] Submitting Response to Q2 (Distractor Choice to Test Remediation)...")
        source_item2 = db.get(AssessmentItem, q2["question_id"])
        options2 = json.loads(source_item2.options_json)
        labels2 = [str(opt).split(".", 1)[0].strip().upper() for opt in options2]
        distractor = next(lbl for lbl in labels2 if lbl != source_item2.correct_option.strip().upper())

        ans2_resp = client.post(
            "/api/diagnostic/respond",
            json={
                "session_id": session_id,
                "assessment_item_id": q2["question_id"],
                "selected_option": distractor,
                "response_time_ms": 28500,
            },
        )
        if ans2_resp.status_code != 200:
            print(f"[-] Q2 response submission failed: {ans2_resp.status_code} - {ans2_resp.text}")
            return False

        ans2_data = ans2_resp.json()
        print(f"[+] Response Evaluated: is_correct={ans2_data['is_correct']}, score={ans2_data['score']}")
        print(f"    - Misconception Pattern Flagged: {ans2_data['misconception_flagged']}")
        print(f"    - Updated Estimated Mastery:     {ans2_data['updated_mastery']}")

        q3 = ans2_data["next_question"]
        if not q3:
            print("[-] Expected adaptive remediation question 3, got None.")
            return False

        print(f"[+] Remediation Question Served: ID={q3['question_id']}, Difficulty='{q3['difficulty']}'")
        print(f"    - Rationale: {q3['selection_rationale']}")

        # Step 6: Respond to Question 3 (Final Question to Trigger Stopping Criteria)
        print("\n[Step 6] Submitting Response to Q3 (Reaching Max Questions Stopping Gate)...")
        source_item3 = db.get(AssessmentItem, q3["question_id"])
        ans3_resp = client.post(
            "/api/diagnostic/respond",
            json={
                "session_id": session_id,
                "assessment_item_id": q3["question_id"],
                "selected_option": source_item3.correct_option,
                "response_time_ms": 11000,
            },
        )
        if ans3_resp.status_code != 200:
            print(f"[-] Q3 response submission failed: {ans3_resp.status_code} - {ans3_resp.text}")
            return False

        ans3_data = ans3_resp.json()
        print(f"[+] Diagnostic Completion Reached: is_complete={ans3_data['is_complete']}")
        print(f"    - Stop Reason:                   {ans3_data['stop_reason']}")
        print(f"    - Final Estimated Mastery:       {ans3_data['updated_mastery']}")
        print(f"    - Final Confidence:              {ans3_data['updated_confidence']:.2f}")
        print(f"    - Final Uncertainty:             {ans3_data['updated_uncertainty']:.2f}")

        # Step 7: Verify Evidence Ledger
        print("\n[Step 7] Auditing Evidence Ledger API (GET /api/evidence)...")
        ev_resp = client.get(f"/api/evidence?competency_id={target_comp.id}")
        assert ev_resp.status_code == 200
        ev_data = ev_resp.json()
        print(f"[+] Total Evidence Records in Ledger: {ev_data['total_records']}")
        for entry in ev_data["evidence"][:3]:
            print(f"    - [{entry['provenance']}] {entry['title']} | Score={entry['score']} | Status={entry['reliability_status']}")

        # Step 8: Verify Competency History Ledger
        print("\n[Step 8] Auditing Competency History API (GET /api/competency/history/{id})...")
        hist_resp = client.get(f"/api/competency/history/{target_comp.id}")
        assert hist_resp.status_code == 200
        hist_records = hist_resp.json()
        print(f"[+] Total State Transitions Logged: {len(hist_records)}")
        for h in hist_records:
            print(f"    - Version {h['state_version']}: {h['previous_status']} -> {h['new_status']} (Mastery: {h['previous_mastery']} -> {h['new_mastery']})")

        # Step 9: Verify Learner Dashboard Propagation
        print("\n[Step 9] Auditing Learner Dashboard Propagation (GET /api/dashboard/learner)...")
        dash_resp = client.get("/api/dashboard/learner")
        assert dash_resp.status_code == 200
        dash_comps = {c["competency_id"]: c for c in dash_resp.json()["competencies"]}
        comp_summary = dash_comps.get(target_comp.id)
        assert comp_summary is not None
        print(f"[+] Dashboard Real-Time Reflection: Status={comp_summary['status']}, Mastery={comp_summary['mastery']}, Confidence={comp_summary['confidence']}")

        print("\n" + "=" * 80)
        print("PHASE 2 END-TO-END VERIFICATION: SUCCESS [VERIFIED 🟢]")
        print("=" * 80)
        return True

    finally:
        fastapi_app.dependency_overrides.clear()
        db.close()


if __name__ == "__main__":
    success = run_phase2_verification()
    sys.exit(0 if success else 1)
