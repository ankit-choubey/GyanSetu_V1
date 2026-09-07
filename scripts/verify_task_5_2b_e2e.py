"""
scripts/verify_task_5_2b_e2e.py — Task 5.2b Scenario Backend End-to-End Runtime Verifier.

Exercises the complete HTTP API operational loop for realistic application scenarios:
TEST 1: Authenticated learner creates/requests a valid scenario.
TEST 2: Scenario is actually persisted.
TEST 3: Scenario references valid competency/subskill.
TEST 4: Learner creates an attempt.
TEST 5: Learner submits an answer/response.
TEST 6: Actual backend evaluation path executes.
TEST 7: Evaluation result is persisted.
TEST 8: Evidence is created (EvidenceType.APPLICATION_SCENARIO).
TEST 9: Competency state changes through real competency service.
TEST 10: Competency history records the transition.
TEST 11: Duplicate submission behaves idempotently.
TEST 12: Invalid scenario is rejected.
TEST 13: Invalid competency/subskill relationship is rejected.
TEST 14: Learner A cannot access learner B's attempt.
TEST 15: Unauthenticated request is rejected.
TEST 16: Malformed evaluator output is rejected.
TEST 17: Scenario provider/generator unavailable path degrades safely.
TEST 18: Database transaction rollback works on failure.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# Add backend and root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlmodel import SQLModel

from app.database import SessionLocal, engine
from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import Scenario, ScenarioAttempt, ScenarioEvaluation
from app.models.user import User
from app.services.scenarios.scenario_interfaces import (
    CandidateValidationError,
    EvaluationValidationError,
    LLMScenarioGenerator,
    ScenarioCandidate,
    ScenarioEvaluationResult,
    ScenarioGenerationContext,
    validate_evaluation_result,
    validate_scenario_candidate,
)
from app.services.scenarios.scenario_service import ScenarioService
from app.utils.security import create_access_token, hash_password


def run_verification() -> bool:
    print("=" * 80)
    print("TASK 5.2b — SCENARIO BACKEND RUNTIME E2E VERIFICATION")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    test_results: list[tuple[str, bool, str]] = []

    try:
        # Seed test users and ensure competencies exist
        role = db.execute(select(Role).where(Role.name == "Field Officer E2E")).scalar_one_or_none()
        if not role:
            role = Role(name="Field Officer E2E")
            db.add(role)
            db.flush()

        comp = db.execute(select(Competency)).scalars().first()
        if not comp:
            comp = Competency(name="E2E Sampling Competency")
            db.add(comp)
            db.flush()

        sub = db.execute(select(SubSkill).where(SubSkill.competency_id == comp.id)).scalars().first()
        if not sub:
            sub = SubSkill(name="E2E Subskill", competency_id=comp.id)
            db.add(sub)
            db.flush()

        # Ensure RoleCompetency link
        rc = db.execute(select(RoleCompetency).where(RoleCompetency.role_id == role.id, RoleCompetency.competency_id == comp.id)).scalar_one_or_none()
        if not rc:
            db.add(RoleCompetency(role_id=role.id, competency_id=comp.id))
            db.flush()

        # Users
        u1_email = f"learner_a_{uuid.uuid4().hex[:6]}@mospi.gov.in"
        u2_email = f"learner_b_{uuid.uuid4().hex[:6]}@mospi.gov.in"
        u1 = User(email=u1_email, full_name="Officer A", password_hash=hash_password("testpass"), role_id=role.id, is_active=True)
        u2 = User(email=u2_email, full_name="Officer B", password_hash=hash_password("testpass"), role_id=role.id, is_active=True)
        db.add_all([u1, u2])
        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        token_a = create_access_token(u1.id)
        token_b = create_access_token(u2.id)

        # TEST 1: Authenticated learner creates/requests valid scenario
        scenario_title = f"E2E PLFS Sample Stratification {uuid.uuid4().hex[:6]}"
        resp1 = client.post(
            "/api/scenarios",
            json={
                "title": scenario_title,
                "description": "Formulate stratum boundaries for urban sampling units in PLFS.",
                "scenario_type": "SURVEY_DESIGN",
                "competency_id": comp.id,
                "subskill_id": sub.id,
                "role_id": role.id,
                "difficulty": "medium",
                "expected_outcomes": ["Stratify urban frames appropriately."],
                "evaluation_rubric": {
                    "passing_threshold": 0.70,
                    "criteria": [
                        {"name": "strat", "weight": 0.5, "required_keyword": "stratification"},
                        {"name": "resamp", "weight": 0.5, "required_keyword": "resample"},
                    ],
                },
                "metadata": {"provenance": "[SANDBOX DATA]"},
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        t1_pass = resp1.status_code == 201 and resp1.json()["title"] == scenario_title
        test_results.append(("TEST 1: Authenticated scenario creation", t1_pass, f"Status: {resp1.status_code}"))
        scen_data = resp1.json()
        scenario_id = scen_data["scenario_id"]

        # TEST 2: Scenario actually persisted in DB
        db_scen = db.execute(select(Scenario).where(Scenario.scenario_id == scenario_id)).scalar_one_or_none()
        t2_pass = db_scen is not None and db_scen.title == scenario_title
        test_results.append(("TEST 2: Scenario DB persistence", t2_pass, f"DB id: {getattr(db_scen, 'id', None)}"))

        # TEST 3: Scenario references valid competency/subskill
        t3_pass = db_scen.competency_id == comp.id and db_scen.subskill_id == sub.id
        test_results.append(("TEST 3: Competency/Subskill relational reference", t3_pass, f"Comp: {db_scen.competency_id}, Sub: {db_scen.subskill_id}"))

        # TEST 4: Learner creates an attempt
        resp4 = client.post(f"/api/scenarios/{scenario_id}/attempts", headers={"Authorization": f"Bearer {token_a}"})
        t4_pass = resp4.status_code == 201 and resp4.json()["status"] == "STARTED"
        test_results.append(("TEST 4: Learner attempt initialization", t4_pass, f"Attempt ID: {resp4.json().get('attempt_id')}"))
        attempt_id = resp4.json()["attempt_id"]

        # TEST 5: Learner submits an answer/response
        resp5 = client.post(
            f"/api/scenarios/attempts/{attempt_id}/submit",
            json={"response_payload": {"answer": "Apply proper stratification and then resample the cluster."}},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        t5_pass = resp5.status_code == 200 and resp5.json()["attempt"]["status"] in ("EVALUATED", "REVIEW_REQUIRED")
        test_results.append(("TEST 5: Learner response submission", t5_pass, f"Status: {resp5.status_code}"))
        submit_data = resp5.json()

        # TEST 6: Actual backend evaluation path executes
        eval_data = submit_data.get("evaluation")
        t6_pass = eval_data is not None and eval_data["passed"] is True and eval_data["normalized_score"] == 1.0
        test_results.append(("TEST 6: Evaluator execution & scoring", t6_pass, f"Score: {eval_data.get('normalized_score')}"))

        # TEST 7: Evaluation result is persisted
        db_eval = db.execute(select(ScenarioEvaluation).where(ScenarioEvaluation.id == eval_data["id"])).scalar_one_or_none()
        t7_pass = db_eval is not None and db_eval.passed is True
        test_results.append(("TEST 7: Evaluation DB persistence", t7_pass, f"DB eval id: {getattr(db_eval, 'id', None)}"))

        # TEST 8: Evidence is created (EvidenceType.APPLICATION_SCENARIO)
        ev = db.execute(
            select(Evidence).where(
                Evidence.user_id == u1.id,
                Evidence.evidence_type == EvidenceType.APPLICATION_SCENARIO,
                Evidence.competency_id == comp.id,
            )
        ).scalar_one_or_none()
        t8_pass = ev is not None and "SCENARIO:" in ev.source and ev.provenance == "[SANDBOX DATA]"
        test_results.append(("TEST 8: Structured evidence emission", t8_pass, f"Evidence id: {getattr(ev, 'id', None)}, Type: {getattr(ev, 'evidence_type', None)}"))

        # TEST 9: Competency state changes through real competency service
        st = db.execute(select(CompetencyState).where(CompetencyState.user_id == u1.id, CompetencyState.competency_id == comp.id)).scalar_one_or_none()
        t9_pass = st is not None and st.mastery > 0.0
        test_results.append(("TEST 9: Real-time competency state recalculation", t9_pass, f"Mastery: {getattr(st, 'mastery', None)}, Status: {getattr(st, 'status', None)}"))

        # TEST 10: Competency history records the transition
        hist = db.execute(
            select(CompetencyHistory).where(CompetencyHistory.user_id == u1.id, CompetencyHistory.competency_id == comp.id)
        ).scalars().all()
        t10_pass = len(hist) >= 1 and hist[-1].new_mastery is not None
        test_results.append(("TEST 10: Competency history ledger audit", t10_pass, f"History records: {len(hist)}, Last new_mastery: {hist[-1].new_mastery if hist else None}"))

        # TEST 11: Duplicate submission behaves idempotently
        # Start new attempt to test duplicate idempotency key
        resp_att2 = client.post(f"/api/scenarios/{scenario_id}/attempts", headers={"Authorization": f"Bearer {token_a}"})
        att2_id = resp_att2.json()["attempt_id"]
        idemp_key = f"idemp_{uuid.uuid4().hex[:8]}"

        resp11_a = client.post(
            f"/api/scenarios/attempts/{att2_id}/submit",
            json={"response_payload": {"answer": "First execution"}, "idempotency_key": idemp_key},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        resp11_b = client.post(
            f"/api/scenarios/attempts/{att2_id}/submit",
            json={"response_payload": {"answer": "Duplicate execution"}, "idempotency_key": idemp_key},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        t11_pass = (
            resp11_a.status_code == 200
            and resp11_b.status_code == 200
            and resp11_a.json()["attempt"]["id"] == resp11_b.json()["attempt"]["id"]
            and resp11_b.json()["competency_update"] is None
        )
        test_results.append(("TEST 11: Idempotency enforcement", t11_pass, "Network retry produced identical outcome without duplicate evidence"))

        # TEST 12: Invalid scenario is rejected
        resp12 = client.post(
            "/api/scenarios",
            json={"title": "X", "description": "Too short", "competency_id": comp.id, "difficulty": "invalid"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        t12_pass = resp12.status_code in (400, 422)
        test_results.append(("TEST 12: Invalid scenario rejection", t12_pass, f"Status: {resp12.status_code}"))

        # TEST 13: Invalid competency/subskill relationship is rejected
        comp_other = db.query(Competency).filter(Competency.id != comp.id).first()
        cand13 = ScenarioCandidate(
            title="Mismatched Taxonomy Scenario",
            description="Testing invalid taxonomy relationship.",
            scenario_type="SURVEY_DESIGN",
            competency_id=comp_other.id,
            subskill_id=sub.id,  # sub belongs to comp, not comp_other
            expected_outcomes=["Outcome"],
            evaluation_rubric={"passing_threshold": 0.70},
        )
        t13_caught = False
        try:
            validate_scenario_candidate(db, cand13)
        except CandidateValidationError:
            t13_caught = True
        test_results.append(("TEST 13: Invalid taxonomy link rejection", t13_caught, "Mismatched subskill was rejected"))

        # TEST 14: Learner A cannot access Learner B's attempt
        resp14 = client.get(f"/api/scenarios/attempts/{attempt_id}", headers={"Authorization": f"Bearer {token_b}"})
        t14_pass = resp14.status_code == 403
        test_results.append(("TEST 14: Learner isolation enforcement", t14_pass, f"Cross-learner status: {resp14.status_code}"))

        # TEST 15: Unauthenticated request is rejected
        resp15 = client.get("/api/scenarios")
        t15_pass = resp15.status_code in (401, 403)
        test_results.append(("TEST 15: Unauthenticated access rejection", t15_pass, f"Status: {resp15.status_code}"))

        # TEST 16: Malformed evaluator output is rejected
        bad_result = ScenarioEvaluationResult(
            score=5.0,
            max_score=1.0,
            normalized_score=5.0,
            passed=True,
            competency_evidence={},
            subskill_evidence={},
            rubric_results={},
        )
        t16_caught = False
        try:
            validate_evaluation_result(bad_result)
        except EvaluationValidationError:
            t16_caught = True
        test_results.append(("TEST 16: Malformed evaluator rejection", t16_caught, "Normalized score > 1.0 was rejected"))

        # TEST 17: Scenario provider/generator unavailable path degrades safely
        llm_gen = LLMScenarioGenerator(available=False)
        ctx = ScenarioGenerationContext(competency_id=comp.id)
        t17_caught = False
        try:
            llm_gen.generate(ctx)
        except RuntimeError as e:
            if "unavailable" in str(e).lower():
                t17_caught = True
        test_results.append(("TEST 17: Unavailable provider safe degradation", t17_caught, "Graceful failure on provider outage"))

        # TEST 18: Database transaction rollback works on failure
        initial_ev_count = len(db.execute(select(Evidence)).scalars().all())
        attempt_fail = ScenarioService.start_attempt(db, u1.id, db_scen.scenario_id)

        class CrashingEvaluator:
            def evaluate(self, s, r):
                return ScenarioEvaluationResult(
                    score=999.0, max_score=1.0, normalized_score=999.0, passed=True,
                    competency_evidence={}, subskill_evidence={}, rubric_results={},
                )

        t18_caught = False
        try:
            ScenarioService.submit_attempt(
                db,
                user_id=u1.id,
                attempt_id=attempt_fail.attempt_id,
                response_payload={"answer": "crash"},
                evaluator=CrashingEvaluator(),
            )
        except EvaluationValidationError:
            t18_caught = True

        post_ev_count = len(db.execute(select(Evidence)).scalars().all())
        t18_pass = t18_caught and post_ev_count == initial_ev_count
        test_results.append(("TEST 18: Transaction rollback on failure", t18_pass, f"Evidence count preserved: {post_ev_count} == {initial_ev_count}"))

    finally:
        try:
            if 'scenario_id' in locals() and scenario_id:
                scen = db.get(Scenario, scenario_id)
                if scen:
                    # delete associated attempts, responses, evals
                    atts = db.query(ScenarioAttempt).filter(ScenarioAttempt.scenario_id == scen.id).all()
                    for a in atts:
                        db.delete(a)
                    db.delete(scen)
            if 'u1' in locals() and u1 and u1.id:
                db.delete(u1)
            if 'u2' in locals() and u2 and u2.id:
                db.delete(u2)
            db.commit()
        except Exception:
            db.rollback()
        db.close()

    # Print Report
    print("\n" + "-" * 80)
    all_passed = True
    for name, passed, detail in test_results:
        flag = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{flag}] {name:50} -> {detail}")
    print("-" * 80)
    print(f"5.2b SCENARIO RUNTIME STATUS: {'ALL PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
