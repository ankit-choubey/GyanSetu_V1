"""Phase 7: Workforce Intelligence, Fairness, Governance & Longitudinal Validation Test Suite.

Verifies the 15 mandatory Phase 7 scenarios (A through O):
- Scenario A: Admin requests workforce overview (200 OK, aggregated, zero learner IDs).
- Scenario B: Learner requests workforce analytics (403 Forbidden).
- Scenario C: Small cohort (N < 5) privacy suppression (SUPPRESSED_SMALL_COHORT).
- Scenario D: Low-confidence gap triage -> NEEDS_MORE_EVIDENCE.
- Scenario E: High-confidence gap triage -> ACTIONABLE.
- Scenario F: Stale evidence (>180d) -> DATA_QUALITY_WARNING with STALE_EVIDENCE.
- Scenario G: Conflicting evidence -> DATA_QUALITY_WARNING with CONFLICTING_EVIDENCE.
- Scenario H: Insufficient fairness data / missing demographics -> FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA.
- Scenario I: Operational cohort parity check -> POTENTIAL_DISPARITY / REQUIRES_REVIEW or NO_MATERIAL_DIFFERENCE_DETECTED.
- Scenario J: Intervention outcome associations -> Non-causal observed deltas.
- Scenario K: Longitudinal trend monitoring -> IMPROVING, STABLE, DECLINING, INSUFFICIENT_HISTORY.
- Scenario L: Emerging skills radar -> EMERGING_SIGNAL with time window and provenance.
- Scenario M: Learner cross-query / endpoint abuse rejection (403 Forbidden).
- Scenario N: Competency UNDER_REVIEW reflects governance state.
- Scenario O: Model registry reflects production baseline vs research/experimental.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import SessionLocal, engine
from app.main import app
from app.models.competency import Competency, Role
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.governance import (
    CompetencyGovernance,
    ModelRegistryRecord,
    ModelStatus,
    ReviewStatus,
    WorkforceAuditLog,
)
from app.models.user import User
from app.dependencies import get_current_admin, get_current_user
from app.services.governance_service import GovernanceService
from app.services.fairness_audit_service import FairnessAuditService
from app.services.data_quality_service import DataQualityService
from app.services.workforce_analytics_service import WorkforceAnalyticsService


@pytest.fixture(scope="module")
def admin_user():
    """Mock administrative user with role_id=2 (Administrator)."""
    return User(
        id=888,
        email="workforce_admin@mospi.gov.in",
        full_name="MoSPI Workforce Administrator",
        password_hash="test_pwd_hash",
        role_id=2,  # Admin role
        is_active=True,
    )


@pytest.fixture(scope="module")
def learner_user():
    """Mock civil service learner user with role_id=1 (Field Investigator / Non-admin)."""
    return User(
        id=777,
        email="learner_investigator@mospi.gov.in",
        full_name="MoSPI Field Investigator",
        password_hash="test_pwd_hash",
        role_id=1,  # Non-admin role
        is_active=True,
    )


@pytest.fixture(scope="module", autouse=True)
def setup_governance_data():
    """Ensure baseline governance and model registry data are initialized in DB."""
    db = SessionLocal()
    try:
        GovernanceService.initialize_governance_data(db)
    finally:
        db.close()


# ==============================================================================
# Scenario A: Admin requests workforce overview
# ==============================================================================
def test_scenario_a_admin_overview_authorized_and_anonymized(admin_user):
    """Scenario A: Admin requests overview -> 200, aggregated, zero learner IDs exposed."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/overview")
            assert resp.status_code == 200
            data = resp.json()

            # Verify aggregated summary structure
            assert "workforce_summary" in data
            summary = data["workforce_summary"]
            assert "total_workforce_learners" in summary
            assert "overall_average_mastery" in summary
            assert "overall_average_confidence" in summary
            assert "overall_average_coverage" in summary

            # Verify strict privacy guardrail
            assert "privacy_parameters" in data
            assert data["privacy_parameters"]["small_cell_protection_enabled"] is True
            assert data["privacy_parameters"]["learner_identification_policy"] == "STRICT_ANONYMIZATION_ZERO_IDS_EXPOSED"

            # Verify non-autonomous decision support guardrail
            assert "governance_guardrail" in data
            assert "DECISION SUPPORT ONLY" in data["governance_guardrail"]

            # Verify zero learner IDs exposed in the response
            assert "user_id" not in summary
            assert "learner_id" not in summary
            assert "users" not in data
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario B: Learner requests workforce analytics
# ==============================================================================
def test_scenario_b_learner_overview_forbidden(learner_user):
    """Scenario B: Learner requests workforce overview -> 403 Forbidden."""
    app.dependency_overrides[get_current_user] = lambda: learner_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/overview", headers={"Authorization": "Bearer dummy_token"})
            assert resp.status_code == 403
            assert "Administrator access required" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# Scenario C: Small cohort (N < 5) privacy suppression
# ==============================================================================
def test_scenario_c_small_cohort_suppression(admin_user):
    """Scenario C: Small cohort suppression -> SUPPRESSED_SMALL_COHORT and zero learner IDs."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            # Set minimum_group_size to high threshold (e.g. 50) so cohorts are suppressed
            resp = client.get("/api/workforce/competencies?minimum_group_size=50")
            assert resp.status_code == 200
            data = resp.json()

            assert "suppression_policy" in data
            assert data["suppression_policy"]["small_cell_protection_enabled"] is True
            assert data["suppressed_groups_count"] > 0

            # Check that suppressed items are marked properly
            suppressed = [c for c in data["competencies"] if c.get("aggregation_status") == "SUPPRESSED"]
            assert len(suppressed) > 0
            for item in suppressed:
                assert item["population_size"] < 50
                assert "estimated_mastery" not in item
                assert "mean_confidence" not in item
                assert "below minimum privacy threshold" in item["suppression_reason"]

            # Verify zero learner IDs
            raw_text = json.dumps(data)
            assert "user_id" not in raw_text
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario D: Low-confidence gap triage -> NEEDS_MORE_EVIDENCE
# ==============================================================================
def test_scenario_d_low_confidence_gap_triage(admin_user):
    """Scenario D: Low-confidence gaps are classified as NEEDS_MORE_EVIDENCE."""
    db = SessionLocal()
    try:
        # Guarantee a low-confidence gap cohort for competency 5
        existing_5 = db.execute(select(CompetencyState).where(CompetencyState.competency_id == 5)).scalars().all()
        if len(existing_5) < 5:
            for uid in range(500, 506):
                s = CompetencyState(user_id=uid, competency_id=5, mastery=0.40, confidence=0.20, status="ASSESSED", evidence_count=1)
                db.add(s)
            db.commit()
    finally:
        db.close()

    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/gaps")
            assert resp.status_code == 200
            data = resp.json()

            assert "workforce_gaps" in data
            gaps = data["workforce_gaps"]
            assert len(gaps) > 0

            needs_evidence = [g for g in gaps if g["classification"] == "NEEDS_MORE_EVIDENCE"]
            assert len(needs_evidence) > 0
            for gap in needs_evidence:
                assert gap["confidence"] < 0.35
                assert "diagnostic assessments" in gap["why_prioritized"].casefold()
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario E: High-confidence gap triage -> ACTIONABLE
# ==============================================================================
def test_scenario_e_high_confidence_gap_triage(admin_user):
    """Scenario E: High-confidence gaps are classified as ACTIONABLE."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/gaps")
            assert resp.status_code == 200
            data = resp.json()

            assert "workforce_gaps" in data
            gaps = data["workforce_gaps"]
            actionable = [g for g in gaps if g["classification"] == "ACTIONABLE"]
            assert len(actionable) > 0
            for gap in actionable:
                assert gap["confidence"] >= 0.35
                assert "sufficient evidence confidence" in gap["why_prioritized"].casefold()
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario F: Stale evidence (>180d) -> DATA_QUALITY_WARNING
# ==============================================================================
def test_scenario_f_stale_evidence_detection(admin_user):
    """Scenario F: Stale evidence records (>180d) surface structured DATA_QUALITY_WARNING."""
    db = SessionLocal()
    try:
        # Insert a synthetic stale evidence item (>200 days old)
        stale_ev = Evidence(
            user_id=1,
            competency_id=1,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Stale Assessment Observation",
            description="Synthetic past baseline observation for data quality audit verification",
            score=0.75,
            weight=1.0,
            observed_at=datetime.now(timezone.utc) - timedelta(days=220),
        )
        db.add(stale_ev)
        db.commit()
    finally:
        db.close()

    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/data-quality")
            assert resp.status_code == 200
            data = resp.json()

            assert "warnings" in data
            stale_warnings = [w for w in data["warnings"] if w["category"] == "STALE_EVIDENCE"]
            assert len(stale_warnings) > 0
            w = stale_warnings[0]
            assert w["warning_type"] == "DATA_QUALITY_WARNING"
            assert w["affected_count"] > 0
            assert "remediation" in w
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario G: Conflicting evidence detection
# ==============================================================================
def test_scenario_g_conflicting_evidence_detection(admin_user):
    """Scenario G: Conflicting evidence states surface HIGH severity DATA_QUALITY_WARNING."""
    db = SessionLocal()
    try:
        # Ensure at least one conflicting state exists
        existing_conf = db.execute(
            select(CompetencyState).where(CompetencyState.status == "CONFLICTING_EVIDENCE")
        ).scalars().first()

        if not existing_conf:
            state = CompetencyState(
                user_id=1,
                competency_id=2,
                mastery=0.45,
                confidence=0.50,
                status="CONFLICTING_EVIDENCE",
                evidence_count=4,
            )
            db.add(state)
            db.commit()
    finally:
        db.close()

    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/data-quality")
            assert resp.status_code == 200
            data = resp.json()

            assert "warnings" in data
            conf_warnings = [w for w in data["warnings"] if w["category"] == "CONFLICTING_EVIDENCE"]
            assert len(conf_warnings) > 0
            w = conf_warnings[0]
            assert w["warning_type"] == "DATA_QUALITY_WARNING"
            assert w["severity"] == "HIGH"
            assert "Schedule supervised practical verification" in w["remediation"]
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario H: Insufficient fairness data / missing demographics
# ==============================================================================
def test_scenario_h_fairness_safe_demographic_handling(admin_user):
    """Scenario H: Missing demographics safely handled with FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/fairness")
            assert resp.status_code == 200
            data = resp.json()

            assert data["fairness_framework"] == "OPERATIONAL_COHORT_PARITY_AUDIT"
            assert data["sensitive_attribute_status"] == "FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA"
            assert "Protected demographic characteristics" in data["demographic_data_disclosure"]
            assert data["provenance"] == "[OPERATIONAL_AUDIT:NON_SENSITIVE]"
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario I: Operational cohort parity check (Four-Fifths Rule)
# ==============================================================================
def test_scenario_i_operational_cohort_parity_audit(admin_user):
    """Scenario I: Evaluates operational cohort parity without claiming 'bias confirmed'."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/fairness")
            assert resp.status_code == 200
            data = resp.json()

            assert data["overall_classification"] in (
                "NO_MATERIAL_DIFFERENCE_DETECTED",
                "POTENTIAL_DISPARITY",
                "INSUFFICIENT_DATA",
            )
            assert data["decision"] in ("ACCEPTABLE", "REQUIRES_REVIEW")

            # Check disparity evaluations
            for ev in data.get("disparity_evaluations", []):
                assert ev["benchmark"] == 0.80
                assert ev["classification"] in ("NO_MATERIAL_DIFFERENCE_DETECTED", "POTENTIAL_DISPARITY")
                # Confirm scientific caution: never claims "bias confirmed"
                assert "bias confirmed" not in ev["interpretation"].casefold()
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario J: Intervention outcome associations (Non-causal)
# ==============================================================================
def test_scenario_j_intervention_outcome_associations(admin_user):
    """Scenario J: Evaluates intervention outcomes using non-causal association wording."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/interventions")
            assert resp.status_code == 200
            data = resp.json()

            assert "provider_comparison" in data
            assert "causality_disclaimer" in data
            assert "not randomized controlled trial (RCT) causal effects" in data["causality_disclaimer"]

            # Inspect providers
            for p_name, p_data in data["provider_comparison"].items():
                if p_data["status"] == "EVALUATED":
                    assert "mean_observed_change" in p_data
                    assert "non-causal association" in p_data["scientific_interpretation"].casefold()
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario K: Longitudinal trend monitoring
# ==============================================================================
def test_scenario_k_longitudinal_trend_monitoring(admin_user):
    """Scenario K: Analyzes competency trajectory states (IMPROVING, STABLE, DECLINING, INSUFFICIENT_HISTORY)."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/trends")
            assert resp.status_code == 200
            data = resp.json()

            assert "longitudinal_trends" in data
            assert "overall_trend_distribution" in data
            trends = data["longitudinal_trends"]
            assert len(trends) > 0

            valid_statuses = {"IMPROVING", "STABLE", "DECLINING", "INSUFFICIENT_HISTORY", "SUPPRESSED"}
            for t in trends:
                assert t["trajectory_status"] in valid_statuses
                assert "velocity" in t
                assert "confidence_trend" in t
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario L: Emerging skill radar
# ==============================================================================
def test_scenario_l_emerging_skills_radar(admin_user):
    """Scenario L: Surfaces EMERGING_SIGNAL with explicit time window and provenance."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/emerging-skills")
            assert resp.status_code == 200
            data = resp.json()

            assert "emerging_skills_radar" in data
            assert data["total_signals_detected"] > 0
            signals = data["emerging_skills_radar"]

            for sig in signals:
                assert sig["status"] == "EMERGING_SIGNAL"
                assert "time_window" in sig
                assert "provenance" in sig
                assert sig["provenance"].startswith("[")
                assert "confidence" in sig

            # Verify disclaimer: emerging != certain
            assert "does not assert certainty" in data["signal_methodology"]
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario M: Learner unauthorized cross-query rejection (403 Forbidden)
# ==============================================================================
def test_scenario_m_learner_cross_query_endpoints_rejected(learner_user):
    """Scenario M: Learner is rejected with 403 Forbidden on all workforce endpoints."""
    app.dependency_overrides[get_current_user] = lambda: learner_user
    endpoints_to_test = [
        "/api/workforce/gaps",
        "/api/workforce/trends",
        "/api/workforce/fairness",
        "/api/workforce/data-quality",
        "/api/workforce/insights",
        "/api/workforce/governance/models",
        "/api/workforce/audit-logs",
    ]
    try:
        with TestClient(app) as client:
            for ep in endpoints_to_test:
                resp = client.get(ep, headers={"Authorization": "Bearer dummy_token"})
                assert resp.status_code == 403, f"Endpoint {ep} expected 403, got {resp.status_code}"
                assert "Administrator access required" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# Scenario N: Competency governance state & under-review handling
# ==============================================================================
def test_scenario_n_competency_governance_under_review(admin_user):
    """Scenario N: Competency #40 has UNDER_REVIEW review status and is non-authoritative."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/governance/competency/40")
            assert resp.status_code == 200
            gov = resp.json()

            assert gov["competency_id"] == 40
            assert gov["review_status"] == "UNDER_REVIEW"
            assert gov["is_authoritative_for_scoring"] is False
            assert "[CURATED:MOSPI_TAXONOMY]" in gov["mapping_provenance"]

            # Test updating governance review status
            update_payload = {
                "review_status": "PROVISIONAL",
                "review_notes": "Reviewed by MoSPI Expert Panel — granted provisional status.",
            }
            post_resp = client.post("/api/workforce/governance/competency/40", json=update_payload)
            assert post_resp.status_code == 200
            post_data = post_resp.json()
            assert post_data["status"] == "success"
            assert post_data["governance"]["review_status"] == "PROVISIONAL"

            # Restore to UNDER_REVIEW
            restore_payload = {
                "review_status": "UNDER_REVIEW",
                "review_notes": "Restored to UNDER_REVIEW for test suite consistency.",
            }
            client.post("/api/workforce/governance/competency/40", json=restore_payload)
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Scenario O: Model registry reflects baseline vs research/experimental
# ==============================================================================
def test_scenario_o_model_registry_statuses(admin_user):
    """Scenario O: Model registry lists production baseline models alongside research candidates."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/governance/models")
            assert resp.status_code == 200
            data = resp.json()

            assert "model_registry" in data
            models = data["model_registry"]
            assert len(models) >= 6

            baselines = [m for m in models if m["scientific_status"] == "PRODUCTION BASELINE"]
            research = [m for m in models if m["scientific_status"] == "RESEARCH"]
            heuristics = [m for m in models if m["scientific_status"] == "ENGINEERING HEURISTIC"]

            assert len(baselines) >= 2, "Expected at least 2 PRODUCTION BASELINE models"
            assert len(research) >= 2, "Expected at least 2 RESEARCH models (BKT, IRT, LinUCB)"
            assert len(heuristics) >= 1, "Expected at least 1 ENGINEERING HEURISTIC model"

            # Every model record must document limitations and evaluation reference
            for m in models:
                assert "limitations" in m and len(m["limitations"]) > 0
                assert "evaluation_reference" in m and len(m["evaluation_reference"]) > 0
    finally:
        app.dependency_overrides.pop(get_current_admin, None)


# ==============================================================================
# Additional Audit Log Verification
# ==============================================================================
def test_audit_logs_recording_and_retrieval(admin_user):
    """Verify that administrative queries produce immutable WorkforceAuditLog entries."""
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            resp = client.get("/api/workforce/audit-logs?limit=10")
            assert resp.status_code == 200
            data = resp.json()

            assert "audit_logs" in data
            logs = data["audit_logs"]
            assert len(logs) > 0

            latest = logs[0]
            assert latest["endpoint"].startswith("/api/workforce/")
            assert latest["authorization_decision"] == "AUTHORIZED"
            assert latest["actor_role"] in ("ADMINISTRATOR", "ADMIN")
    finally:
        app.dependency_overrides.pop(get_current_admin, None)
