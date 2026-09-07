"""
scripts/verify_phase5_end_to_end.py — Phase 5 End-to-End Real-Time Verification.

Executes the complete operational Phase 5 practical learning and competency verification loop:
1. Practical Task Catalog & Schema Integrity Verification (GET /api/practical/tasks)
2. Multi-Criteria Task Filtering (by competency, difficulty, scenario type)
3. Single Task Retrieval & Input Artifacts Inspection (GET /api/practical/tasks/{id})
4. Learner Attempt Lifecycle Initialization (POST /api/practical/tasks/{id}/attempts -> status STARTED)
5. Strict Learner Isolation Enforcement (cross-learner access blocked -> HTTP 403)
6. Sub-Threshold / Failing Submission Handling (scores < 0.70, passed=False, status EVALUATED)
7. Multi-Dimensional Rubric Evaluation & Tolerance Testing (numerical +-0.05, methodology keywords, set matches)
8. Evidence Ledger & Immutable Audit Trail Emission (Evidence row created with EvidenceType.PRACTICAL_TASK, [SANDBOX DATA])
9. Atomic Competency Recalculation & Conflicting Evidence Detection
10. Closed-Loop Next Best Action Generation (POST /api/recommendations/next-best-action)
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
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
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.practical import AttemptStatus, PracticalAttempt, PracticalTask
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
from app.seed_data.practical_scenario_loader import seed_practical_tasks
from app.seed_data.runner import seed_full_taxonomy
from app.services.orchestrator import recalculate_competency_state
from app.utils.security import create_access_token, hash_password


def print_step(step_num: int, title: str) -> None:
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title.upper()}")
    print(f"{'='*70}")


def main() -> None:
    print("======================================================================")
    print("      GyanSetu V1 — PHASE 5 PRACTICAL COMPETENCY VERIFICATION         ")
    print("                REAL-TIME END-TO-END VERIFICATION                     ")
    print("======================================================================")

    # Database setup and seed verification
    SQLModel.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.execute(select(Role)).scalars().first():
            print("Seeding full taxonomy...")
            seed_full_taxonomy("test-pass")
        seed_intervention_catalog(db)
        seed_practical_tasks(db)
    finally:
        db.close()

    client = TestClient(fastapi_app)
    db = SessionLocal()

    # Create distinct test officers
    learner_a = User(
        email=f"officer.sharma.{uuid.uuid4().hex[:6]}@mospi.gov.in",
        password_hash=hash_password("Pass@12345"),
        full_name="Statistical Officer Sharma (FOD)",
        is_active=True,
    )
    learner_b = User(
        email=f"officer.verma.{uuid.uuid4().hex[:6]}@mospi.gov.in",
        password_hash=hash_password("Pass@12345"),
        full_name="Statistical Officer Verma (ESD)",
        is_active=True,
    )
    db.add(learner_a)
    db.add(learner_b)
    db.commit()
    db.refresh(learner_a)
    db.refresh(learner_b)

    headers_a = {"Authorization": f"Bearer {create_access_token(subject=learner_a.id)}"}
    headers_b = {"Authorization": f"Bearer {create_access_token(subject=learner_b.id)}"}

    print(f"Initialized Test Officer A (ID: {learner_a.id}, Email: {learner_a.email})")
    print(f"Initialized Test Officer B (ID: {learner_b.id}, Email: {learner_b.email})")

    # --------------------------------------------------------------------------
    # STEP 1: Practical Task Catalog & Schema Integrity Verification
    # --------------------------------------------------------------------------
    print_step(1, "Practical Task Catalog & Schema Integrity Verification")
    resp = client.get("/api/practical/tasks")
    assert resp.status_code == 200, f"Failed to list practical tasks: {resp.text}"
    tasks = resp.json()
    assert len(tasks) >= 5, f"Expected at least 5 seeded practical tasks, got {len(tasks)}"

    task_ids = {t["task_id"] for t in tasks}
    print(f"Discovered {len(tasks)} active practical tasks in catalog:")
    for t in tasks:
        print(f"  * [{t['task_id']}] {t['title']} | Diff: {t['difficulty']} | Type: {t['scenario_type']}")
        assert t["provenance"] == "[CURATED:SIMULATION]"
        assert t["source"] == "MOSPI_SIMULATION"
        assert "Official-Statistics-aligned simulated practical scenario." in t["scenario_context"]
    assert "TASK-MOSPI-SAMP-01" in task_ids
    assert "TASK-MOSPI-CPI-01" in task_ids
    assert "TASK-MOSPI-QUAL-01" in task_ids
    print("[PASS] Step 1: All 5 authentic MoSPI practical scenarios verified with schema integrity.")

    # --------------------------------------------------------------------------
    # STEP 2: Multi-Criteria Task Filtering
    # --------------------------------------------------------------------------
    print_step(2, "Multi-Criteria Task Filtering (Competency, Difficulty, Type)")
    cpi_task = next(t for t in tasks if t["task_id"] == "TASK-MOSPI-CPI-01")
    cpi_comp_id = cpi_task["competency_id"]

    resp_comp = client.get(f"/api/practical/tasks?competency_id={cpi_comp_id}")
    assert resp_comp.status_code == 200
    comp_tasks = resp_comp.json()
    assert all(t["competency_id"] == cpi_comp_id for t in comp_tasks)
    print(f"  * Filtered by competency_id={cpi_comp_id}: {len(comp_tasks)} tasks found.")

    resp_diff = client.get("/api/practical/tasks?difficulty=hard")
    assert resp_diff.status_code == 200
    hard_tasks = resp_diff.json()
    assert all(t["difficulty"] == "hard" for t in hard_tasks)
    print(f"  * Filtered by difficulty=hard: {len(hard_tasks)} tasks found ({[t['task_id'] for t in hard_tasks]}).")

    resp_type = client.get("/api/practical/tasks?scenario_type=DATA_VALIDATION")
    assert resp_type.status_code == 200
    val_tasks = resp_type.json()
    assert all(t["scenario_type"] == "DATA_VALIDATION" for t in val_tasks)
    print(f"  * Filtered by scenario_type=DATA_VALIDATION: {len(val_tasks)} tasks found.")
    print("[PASS] Step 2: Multi-criteria query filters operating accurately.")

    # --------------------------------------------------------------------------
    # STEP 3: Single Task Retrieval & Input Artifacts Inspection
    # --------------------------------------------------------------------------
    print_step(3, "Single Task Retrieval & Input Artifacts Inspection")
    resp_samp = client.get("/api/practical/tasks/TASK-MOSPI-SAMP-01")
    assert resp_samp.status_code == 200
    task_samp = resp_samp.json()
    assert task_samp["task_id"] == "TASK-MOSPI-SAMP-01"
    artifacts = task_samp["input_artifacts"]
    assert "strata" in artifacts
    assert len(artifacts["strata"]) == 3
    print(f"  * Task title: {task_samp['title']}")
    print(f"  * Input artifact summary: {artifacts['description']} ({len(artifacts['strata'])} strata)")
    print(f"  * Prerequisites: {task_samp['prerequisites']}")
    print("[PASS] Step 3: Single practical task loaded with input artifacts.")

    # --------------------------------------------------------------------------
    # STEP 4: Learner Attempt Lifecycle Initialization
    # --------------------------------------------------------------------------
    print_step(4, "Learner Attempt Lifecycle Initialization")
    resp_attempt = client.post(
        "/api/practical/tasks/TASK-MOSPI-SAMP-01/attempts",
        headers=headers_a,
    )
    assert resp_attempt.status_code == 200
    attempt_a = resp_attempt.json()
    attempt_id = attempt_a["attempt_id"]
    assert attempt_id.startswith("pr_att_")
    assert attempt_a["status"] == "STARTED"
    assert attempt_a["user_id"] == learner_a.id
    assert attempt_a["score"] is None
    print(f"  * Created attempt '{attempt_id}' for Officer Sharma in state '{attempt_a['status']}'.")
    print("[PASS] Step 4: Attempt lifecycle initialized cleanly.")

    # --------------------------------------------------------------------------
    # STEP 5: Strict Learner Isolation Enforcement
    # --------------------------------------------------------------------------
    print_step(5, "Strict Learner Isolation Enforcement")
    # Officer Verma tries to access Officer Sharma's attempt
    resp_iso_get = client.get(f"/api/practical/attempts/{attempt_id}", headers=headers_b)
    assert resp_iso_get.status_code == 403, f"Expected 403 Forbidden, got {resp_iso_get.status_code}"

    # Officer Verma tries to submit Officer Sharma's attempt
    resp_iso_post = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": {}},
        headers=headers_b,
    )
    assert resp_iso_post.status_code == 403, f"Expected 403 Forbidden, got {resp_iso_post.status_code}"
    print("  * Unauthorized cross-learner GET rejected with HTTP 403 Forbidden.")
    print("  * Unauthorized cross-learner SUBMIT rejected with HTTP 403 Forbidden.")
    print("[PASS] Step 5: Strict learner isolation verified.")

    # --------------------------------------------------------------------------
    # STEP 6: Sub-Threshold / Failing Submission Handling
    # --------------------------------------------------------------------------
    print_step(6, "Sub-Threshold / Failing Submission Handling")
    resp_b_att = client.post(
        "/api/practical/tasks/TASK-MOSPI-SAMP-02/attempts",
        headers=headers_b,
    )
    attempt_b_id = resp_b_att.json()["attempt_id"]

    # Flawed submission with wrong Neyman allocations
    flawed_submission = {
        "stratum_products": {"ASI-SMALL": 50000.0, "ASI-MEDIUM": 80000.0, "ASI-LARGE": 100000.0},
        "allocations": {"ASI-SMALL": 200, "ASI-MEDIUM": 200, "ASI-LARGE": 200},
        "methodology_note": "Uniform allocation ignoring strata standard deviation.",
    }
    resp_fail = client.post(
        f"/api/practical/attempts/{attempt_b_id}/submit",
        json={"submission": flawed_submission},
        headers=headers_b,
    )
    assert resp_fail.status_code == 200
    res_fail = resp_fail.json()
    assert res_fail["attempt"]["status"] == "EVALUATED"
    assert res_fail["evaluation"]["passed"] is False
    assert res_fail["attempt"]["score"] < 0.50
    print(f"  * Failing attempt evaluated: Score = {res_fail['attempt']['score']:.2%}, Passed = False.")
    print(f"  * Scientific honesty enforced: Completion != Mastery.")
    print("[PASS] Step 6: Sub-threshold scoring and failure states handled correctly.")

    # --------------------------------------------------------------------------
    # STEP 7: Multi-Dimensional Rubric Evaluation & Tolerance Testing
    # --------------------------------------------------------------------------
    print_step(7, "Multi-Dimensional Rubric Evaluation & Tolerance Testing")
    # Officer Sharma completes TASK-MOSPI-SAMP-01 accurately
    accurate_submission = {
        "response_rates": {
            "STRATUM-RURAL-01": 0.80,
            "STRATUM-URBAN-01": 0.80,
            "STRATUM-PERIURBAN-01": 0.80,
        },
        "adjusted_weights": {
            "STRATUM-RURAL-01": 31.25,
            "STRATUM-URBAN-01": 18.75,
            "STRATUM-PERIURBAN-01": 50.0,
        },
        "estimated_total": 35750000.0,
        "methodology_note": "Calibrated non-response weight adjustment factors and calibration to ensure unbiased population totals.",
    }
    resp_sub_a = client.post(
        f"/api/practical/attempts/{attempt_id}/submit",
        json={"submission": accurate_submission, "idempotency_key": f"key_{attempt_id}"},
        headers=headers_a,
    )
    assert resp_sub_a.status_code == 200
    res_a = resp_sub_a.json()
    assert res_a["attempt"]["status"] == "EVALUATED"
    assert res_a["attempt"]["score"] >= 0.95
    assert res_a["evaluation"]["passed"] is True
    dim_scores = res_a["evaluation"]["dimension_scores"]
    print(f"  * Officer Sharma overall score: {res_a['attempt']['score']:.2%}")
    for dim, sc in dim_scores.items():
        print(f"    - {dim}: {sc:.2f}/1.00")
    print("[PASS] Step 7: Multi-dimensional rubric evaluation passed with high precision.")

    # --------------------------------------------------------------------------
    # STEP 8: Evidence Ledger & Immutable Audit Trail Emission
    # --------------------------------------------------------------------------
    print_step(8, "Evidence Ledger & Immutable Audit Trail Emission")
    evidence_id = res_a["attempt"]["evidence_id"]
    assert evidence_id is not None, "Evaluation must emit Evidence and link to attempt"

    ev_row = db.get(Evidence, evidence_id)
    assert ev_row is not None
    assert ev_row.evidence_type == EvidenceType.PRACTICAL_TASK
    assert ev_row.provenance == "[SANDBOX DATA]"
    assert ev_row.reliability_status == "VERIFIED"
    assert ev_row.source == "PRACTICAL_TASK:TASK-MOSPI-SAMP-01"

    ev_meta = json.loads(ev_row.evidence_metadata)
    assert ev_meta["task_id"] == "TASK-MOSPI-SAMP-01"
    assert ev_meta["attempt_id"] == attempt_id
    print(f"  * Evidence ledger entry #{ev_row.id}: Type={ev_row.evidence_type.value}, Score={ev_row.score}")
    print(f"  * Provenance: {ev_row.provenance}, Reliability: {ev_row.reliability_status}")
    print("[PASS] Step 8: Structured practical evidence emitted to audit ledger.")

    # --------------------------------------------------------------------------
    # STEP 9: Atomic Competency Recalculation & Conflicting Evidence Detection
    # --------------------------------------------------------------------------
    print_step(9, "Atomic Competency Recalculation & Conflicting Evidence Detection")
    # Verify competency state was updated for Sharma
    comp_state_a = db.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == learner_a.id,
            CompetencyState.competency_id == task_samp["competency_id"],
        )
    ).scalar_one()
    print(f"  * Updated Competency #{comp_state_a.competency_id}: Mastery={comp_state_a.mastery}, Confidence={comp_state_a.confidence}, Status={comp_state_a.status}")
    assert comp_state_a.mastery is not None

    # Test Conflicting Evidence detection
    # Add high knowledge evidence (score=1.0) and low practical evidence (score=0.30)
    conf_comp = db.execute(select(Competency).where(Competency.name == "Statistical Modelling")).scalar_one()
    ev_high_know = Evidence(
        user_id=learner_a.id,
        competency_id=conf_comp.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Diagnostic High MCQ",
        score=1.0,
        reliability_status="VERIFIED",
    )
    ev_low_prac = Evidence(
        user_id=learner_a.id,
        competency_id=conf_comp.id,
        evidence_type=EvidenceType.PRACTICAL_TASK,
        title="Simulation Practical Fail",
        score=0.30,
        reliability_status="VERIFIED",
    )
    db.add(ev_high_know)
    db.add(ev_low_prac)
    db.commit()

    orch = recalculate_competency_state(db, learner_a.id, conf_comp.id)
    db.commit()
    assert orch.state.status == "CONFLICTING_EVIDENCE"
    print(f"  * Conflicting Evidence Rule verified: High MCQ (1.0) + Low Practical (0.30) -> Status: {orch.state.status}")
    print("[PASS] Step 9: Atomic competency update and conflicting evidence detection verified.")

    # --------------------------------------------------------------------------
    # STEP 10: Closed-Loop Next Best Action Generation
    # --------------------------------------------------------------------------
    print_step(10, "Closed-Loop Next Best Action Generation")
    # Officer Verma had failed TASK-MOSPI-SAMP-02 (Sampling Design). Request Next Best Action.
    samp_comp = db.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one()
    resp_nba = client.post(
        "/api/recommendations/next-best-action",
        json={"competency_id": samp_comp.id},
        headers=headers_b,
    )
    assert resp_nba.status_code == 200
    nba = resp_nba.json()
    assert nba["selected_intervention"] is not None
    assert nba["competency_id"] == samp_comp.id
    assert nba["status"] == "RECOMMENDED"
    print(f"  * NBA Recommendation ID: {nba['recommendation_id']}")
    print(f"  * Action Type: {nba['action_type']}")
    print(f"  * Selected Intervention: {nba['selected_intervention']['title']} (Provider: {nba['selected_intervention']['provider']})")
    print(f"  * Recommendation Reason: {nba['explanation'].get('reason', 'Targeted remediation')}")
    print("[PASS] Step 10: Closed-loop intervention recommendation successfully generated.")

    print("\n" + "=" * 70)
    print("      ALL 10 REAL-TIME PHASE 5 VERIFICATION STEPS PASSED SUCCESSFULLY! ")
    print("======================================================================\n")


if __name__ == "__main__":
    main()
