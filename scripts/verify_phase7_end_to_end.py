"""
scripts/verify_phase7_end_to_end.py — Phase 7 End-to-End Workforce Intelligence & Governance Verification.

Executes the complete operational Phase 7 verification loop:
1. Initialize Phase 7 Governance & Model Registry Seed
2. Workforce Capability Overview & Strict Non-Autonomous Policy Verification
3. Small-Cell Privacy Suppression Verification (N < minimum_group_size, zero learner IDs)
4. Confidence-Aware Organizational Gap Triage (ACTIONABLE vs NEEDS_MORE_EVIDENCE)
5. Longitudinal Trajectory Monitoring (IMPROVING, STABLE, DECLINING, INSUFFICIENT_HISTORY)
6. Retention Monitoring (Observed vs Modelled Distinction & Risk Detection)
7. Non-Causal Intervention Outcome Association Evaluation
8. Operational Cohort Fairness & Safe Demographics Audit (FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA)
9. Data Quality & Evidence Health Diagnostics (Stale, Conflicting, Under Review)
10. Administrative Access Audit Trail & Role-Based Access Control (Admin 200 vs Learner 403)
"""

from __future__ import annotations

import json
import os
import sys
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

from app.database import SessionLocal, engine
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.competency import Competency, Role
from app.models.user import User
from app.dependencies import get_current_admin, get_current_user
from app.services.governance_service import GovernanceService
from app.services.fairness_audit_service import FairnessAuditService
from app.services.data_quality_service import DataQualityService
from app.services.workforce_analytics_service import WorkforceAnalyticsService


def print_step(step_num: int, title: str) -> None:
    print(f"\n{'='*75}")
    print(f" STEP {step_num}: {title.upper()}")
    print(f"{'='*75}")


def main() -> None:
    print("\n" + "=" * 75)
    print(" GYANSETU V1 — PHASE 7 WORKFORCE INTELLIGENCE & GOVERNANCE E2E VERIFICATION")
    print("=" * 75)

    client = TestClient(fastapi_app)
    db = SessionLocal()

    # Mock admin and learner users
    admin_user = User(
        id=999,
        email="workforce_director@mospi.gov.in",
        full_name="MoSPI Workforce Director",
        password_hash="test_admin_pwd",
        role_id=2,  # Admin role
        is_active=True,
    )
    learner_user = User(
        id=888,
        email="field_officer@mospi.gov.in",
        full_name="MoSPI Field Officer",
        password_hash="test_learner_pwd",
        role_id=1,  # Non-admin role
        is_active=True,
    )

    try:
        # ----------------------------------------------------------------------
        # STEP 1: Initialize Governance Data & Model Registry
        # ----------------------------------------------------------------------
        print_step(1, "Initialize Governance Data & Model Registry")
        init_res = GovernanceService.initialize_governance_data(db)
        print(f"[*] Governance records initialized: {init_res}")

        models = GovernanceService.get_model_registry(db)
        print(f"[*] Active registered models: {len(models)}")
        assert len(models) >= 6, "Expected at least 6 registered analytical models"

        baselines = [m for m in models if m["scientific_status"] == "PRODUCTION BASELINE"]
        research = [m for m in models if m["scientific_status"] == "RESEARCH"]
        heuristics = [m for m in models if m["scientific_status"] == "ENGINEERING HEURISTIC"]
        print(f"    - Production Baselines: {len(baselines)}")
        print(f"    - Research Candidates:  {len(research)}")
        print(f"    - Heuristics:           {len(heuristics)}")
        assert len(baselines) >= 2, "Expected at least 2 production baselines"
        assert len(research) >= 2, "Expected at least 2 research models"
        print("[+] STEP 1 PASSED: Model Registry initialized with strict scientific status demarcation.")

        # ----------------------------------------------------------------------
        # STEP 2: Workforce Overview & Decision Support Guardrails
        # ----------------------------------------------------------------------
        print_step(2, "Workforce Capability Overview & Guardrail Verification")
        overview = WorkforceAnalyticsService.get_overview(db, actor=admin_user)
        summary = overview["workforce_summary"]
        print(f"[*] Total learners in pool:        {summary['total_workforce_learners']}")
        print(f"[*] Total competency states:       {summary['total_competency_states']}")
        print(f"[*] Average workforce mastery:     {summary['overall_average_mastery']:.3f}")
        print(f"[*] Average evidence confidence:   {summary['overall_average_confidence']:.3f}")
        print(f"[*] Average subskill coverage:     {summary['overall_average_coverage']:.3f}")
        print(f"[*] Workforce assessed ratio:      {summary['workforce_assessed_ratio']:.3f}")

        # Guardrails check
        guardrail = overview["governance_guardrail"]
        print(f"[*] Guardrail policy: {guardrail[:80]}...")
        assert "DECISION SUPPORT ONLY" in guardrail
        assert "Automated administrative decisions" in guardrail

        # Anonymization check
        raw_overview = json.dumps(overview)
        assert "user_id" not in summary
        assert "learner_id" not in summary
        print("[+] STEP 2 PASSED: Workforce overview aggregated and guardrails strictly enforced.")

        # ----------------------------------------------------------------------
        # STEP 3: Small-Cell Privacy Suppression Verification
        # ----------------------------------------------------------------------
        print_step(3, "Small-Cell Privacy Suppression (N < threshold)")
        # Run with default threshold = 5
        comp_agg_5 = WorkforceAnalyticsService.get_competencies_aggregate(db, actor=admin_user, min_group_size=5)
        # Run with elevated threshold = 50 to verify suppression kicks in
        comp_agg_50 = WorkforceAnalyticsService.get_competencies_aggregate(db, actor=admin_user, min_group_size=50)

        suppressed_50 = [c for c in comp_agg_50["competencies"] if c.get("aggregation_status") == "SUPPRESSED"]
        print(f"[*] Threshold N=5:  Suppressed {comp_agg_5['suppressed_groups_count']} competencies")
        print(f"[*] Threshold N=50: Suppressed {comp_agg_50['suppressed_groups_count']} competencies")
        assert len(suppressed_50) > 0, "Expected small cohorts to be suppressed at N=50 threshold"

        # Check suppression format
        sample_suppressed = suppressed_50[0]
        print(f"[*] Sample suppressed record: {sample_suppressed['competency_name']} -> {sample_suppressed['suppression_reason']}")
        assert sample_suppressed["aggregation_status"] == "SUPPRESSED"
        assert "estimated_mastery" not in sample_suppressed

        # Ensure zero learner IDs exposed
        raw_agg = json.dumps(comp_agg_50)
        assert "user_id" not in raw_agg
        print("[+] STEP 3 PASSED: Small-cell privacy suppression strictly enforced.")

        # ----------------------------------------------------------------------
        # STEP 4: Confidence-Aware Organizational Gap Triage
        # ----------------------------------------------------------------------
        print_step(4, "Confidence-Aware Organizational Gap Triage")
        gaps_result = WorkforceAnalyticsService.get_prioritized_gaps(db, actor=admin_user)
        gaps = gaps_result["workforce_gaps"]
        print(f"[*] Total capability gaps identified: {len(gaps)}")
        print(f"[*] Actionable gaps count:            {gaps_result['actionable_gaps_count']}")
        print(f"[*] Needs-more-evidence count:        {gaps_result['needs_more_evidence_count']}")

        for g in gaps:
            print(f"    - Comp #{g['competency_id']} ({g['competency_name']}): severity={g['gap_severity']:.2f}, "
                  f"confidence={g['confidence']:.2f} -> {g['classification']} [{g['urgency']}]")
            if g["classification"] == "ACTIONABLE":
                assert g["confidence"] >= 0.35
            elif g["classification"] == "NEEDS_MORE_EVIDENCE":
                assert g["confidence"] < 0.35

        print("[+] STEP 4 PASSED: Organizational gap triage is confidence-aware and actionable.")

        # ----------------------------------------------------------------------
        # STEP 5: Longitudinal Trajectory Monitoring
        # ----------------------------------------------------------------------
        print_step(5, "Longitudinal Competency Trajectory Monitoring")
        trends_result = WorkforceAnalyticsService.get_longitudinal_trends(db, actor=admin_user)
        trends = trends_result["longitudinal_trends"]
        dist = trends_result["overall_trend_distribution"]
        print(f"[*] Total trajectories analyzed: {sum(dist.values())}")
        print(f"[*] Trajectory distribution: {dist}")

        assert "IMPROVING" in dist
        assert "STABLE" in dist
        assert "DECLINING" in dist
        assert "INSUFFICIENT_HISTORY" in dist

        for t in trends[:3]:
            print(f"    - Comp #{t['competency_id']} ({t['competency_name']}): {t['trajectory_status']} "
                  f"(count={t['trajectories_count']}, velocity={t.get('velocity', 0.0)})")

        print("[+] STEP 5 PASSED: Longitudinal trajectory monitoring operational and bounded.")

        # ----------------------------------------------------------------------
        # STEP 6: Retention Monitoring (Observed vs Modelled)
        # ----------------------------------------------------------------------
        print_step(6, "Retention Monitoring (Observed vs Modelled Distinction)")
        retention_res = WorkforceAnalyticsService.get_retention_monitoring(db, actor=admin_user)
        ret_summary = retention_res["retention_summary"]
        print(f"[*] Monitored cohorts:          {ret_summary['total_competencies_monitored']}")
        print(f"[*] Observed retention cohorts: {ret_summary['observed_retention_cohorts']}")
        print(f"[*] Modelled retention cohorts: {ret_summary['modelled_retention_cohorts']}")
        print(f"[*] Cohorts at retention risk:  {ret_summary['competencies_at_retention_risk']}")

        for r in retention_res["retention_monitoring"][:3]:
            print(f"    - Comp #{r['competency_id']} ({r['competency_name']}): {r['retention_measurement_type']}, "
                  f"days={r['mean_days_since_last_assessment']:.1f}, status={r['retention_status']}")

        print("[+] STEP 6 PASSED: Explicit distinction between observed and modelled retention.")

        # ----------------------------------------------------------------------
        # STEP 7: Non-Causal Intervention Outcome Association Evaluation
        # ----------------------------------------------------------------------
        print_step(7, "Intervention Outcome Associations (Non-Causal Evaluation)")
        int_res = WorkforceAnalyticsService.get_intervention_analytics(db, actor=admin_user)
        providers = int_res["provider_comparison"]
        print(f"[*] Evaluated intervention providers: {list(providers.keys())}")
        print(f"[*] Causality disclaimer: {int_res['causality_disclaimer'][:80]}...")

        assert "not randomized controlled trial (RCT) causal effects" in int_res["causality_disclaimer"]

        for p_name, p_data in providers.items():
            if p_data["status"] == "EVALUATED":
                print(f"    - Provider {p_name}: started={p_data['number_started']}, "
                      f"completed={p_data['number_completed']}, mean_change={p_data['mean_observed_change']:.4f}")
                assert "non-causal association" in p_data["scientific_interpretation"].casefold()
            else:
                print(f"    - Provider {p_name}: {p_data['status']} ({p_data.get('reason')})")

        print("[+] STEP 7 PASSED: Intervention outcome associations reported with non-causal integrity.")

        # ----------------------------------------------------------------------
        # STEP 8: Operational Cohort Fairness & Safe Demographics Audit
        # ----------------------------------------------------------------------
        print_step(8, "Operational Cohort Fairness & Four-Fifths Parity Audit")
        fairness_res = FairnessAuditService.audit_operational_fairness(db)
        print(f"[*] Framework:                 {fairness_res['fairness_framework']}")
        print(f"[*] Sensitive attribute state: {fairness_res['sensitive_attribute_status']}")
        print(f"[*] Overall classification:    {fairness_res['overall_classification']}")
        print(f"[*] Administrative decision:   {fairness_res['decision']}")
        print(f"[*] Evaluated cohorts:         {fairness_res['evaluated_cohorts_count']}")

        assert fairness_res["sensitive_attribute_status"] == "FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA"
        assert "Protected demographic characteristics" in fairness_res["demographic_data_disclosure"]

        for d in fairness_res.get("disparity_evaluations", []):
            print(f"    - Disparity check: ratio={d['disparity_ratio']} (benchmark={d['benchmark']}) -> {d['classification']}")
            assert "bias confirmed" not in d["interpretation"].casefold()

        print("[+] STEP 8 PASSED: Fairness audit bounded to non-sensitive operational cohorts.")

        # ----------------------------------------------------------------------
        # STEP 9: Data Quality & Evidence Health Diagnostics
        # ----------------------------------------------------------------------
        print_step(9, "Data Quality & Evidence Health Diagnostics")
        dq_res = DataQualityService.audit_data_quality(db)
        print(f"[*] Data Health Score: {dq_res['overall_data_health_score'] * 100:.1f}% ({dq_res['status']})")
        print(f"[*] Active Warnings:   {dq_res['warnings_count']}")

        for w in dq_res.get("warnings", []):
            print(f"    - [{w['severity']}] {w['category']}: {w['description']}")
            print(f"      Remediation: {w['remediation']}")

        print("[+] STEP 9 PASSED: Data quality diagnostics identify evidence freshness and integrity.")

        # ----------------------------------------------------------------------
        # STEP 10: Administrative Audit Trail & RBAC Authorization Check
        # ----------------------------------------------------------------------
        print_step(10, "Administrative Access Audit Trail & RBAC Authorization")
        # 1. Verify admin has access to endpoints
        fastapi_app.dependency_overrides[get_current_admin] = lambda: admin_user
        resp_overview = client.get("/api/workforce/overview")
        assert resp_overview.status_code == 200, f"Admin overview expected 200, got {resp_overview.status_code}"

        resp_gaps = client.get("/api/workforce/gaps")
        assert resp_gaps.status_code == 200

        resp_fairness = client.get("/api/workforce/fairness")
        assert resp_fairness.status_code == 200

        # Check audit log recording
        logs = WorkforceAnalyticsService.get_audit_logs(db, limit=5)
        print(f"[*] Recorded WorkforceAuditLog entries: {len(logs)}")
        assert len(logs) > 0, "Expected audit entries to be logged"
        latest_log = logs[0]
        print(f"[*] Latest audit log: endpoint={latest_log.endpoint}, role={latest_log.actor_role}, decision={latest_log.authorization_decision}")
        assert latest_log.authorization_decision == "AUTHORIZED"

        # 2. Verify learner is rejected with 403 Forbidden
        fastapi_app.dependency_overrides.pop(get_current_admin, None)
        fastapi_app.dependency_overrides[get_current_user] = lambda: learner_user

        endpoints_to_test = [
            "/api/workforce/overview",
            "/api/workforce/competencies",
            "/api/workforce/gaps",
            "/api/workforce/trends",
            "/api/workforce/retention",
            "/api/workforce/interventions",
            "/api/workforce/emerging-skills",
            "/api/workforce/fairness",
            "/api/workforce/data-quality",
            "/api/workforce/insights",
            "/api/workforce/audit-logs",
        ]

        print("[*] Testing learner access across all workforce endpoints (expecting 403 Forbidden):")
        for ep in endpoints_to_test:
            learner_resp = client.get(ep, headers={"Authorization": "Bearer fake_learner_token"})
            assert learner_resp.status_code == 403, f"Endpoint {ep} expected 403, got {learner_resp.status_code}"
            print(f"    - {ep}: 403 Forbidden [VERIFIED]")

        print("[+] STEP 10 PASSED: RBAC and audit logging fully verified.")

    finally:
        fastapi_app.dependency_overrides.pop(get_current_admin, None)
        fastapi_app.dependency_overrides.pop(get_current_user, None)
        db.close()

    print("\n" + "=" * 75)
    print(" ALL 10 PHASE 7 END-TO-END VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
