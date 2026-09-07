"""Phase 6 Scientific Validation, Calibration & Longitudinal Competency Test Suite.

Verifies the 12 rigorous scientific evaluation dimensions:
1. Data provenance & leakage prevention
2. Competency estimator benchmark (Deterministic vs BKT vs IRT-2PL)
3. Confidence calibration & ECE
4. Evidence weight sensitivity & ablation
5. Longitudinal retention & temporal decay
6. Mastery threshold sensitivity
7. Adaptive diagnostic efficiency
8. Recommendation policy evaluation
9. Practical evaluator consistency & LLM safe degradation
10. Competency graph topological integrity
11. Model Selection Gate decisions
12. Admin API endpoints and live database health
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import SessionLocal, engine
from app.main import app
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.user import User
from app.routers import admin as admin_router
from app.services.scientific_validation_service import ScientificValidationService
import sys
from pathlib import Path
_root_dir = str(Path(__file__).resolve().parents[2])
sys.path = [p for p in sys.path if not p.endswith("/bin")]
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if "models" in sys.modules and (getattr(sys.modules["models"], "__file__", "") or "").endswith("bin/models.py"):
    del sys.modules["models"]
from models.scientific_validation import run_scientific_validation_suite



@pytest.fixture(scope="module")
def admin_user():
    return User(
        id=901,
        email="scientific_admin@mospi.gov.in",
        full_name="MoSPI Scientific Validator",
        password_hash="test_hashed_pwd",
        is_active=True,
    )


@pytest.fixture(scope="module")
def validation_report():
    """Load or generate the scientific validation report."""
    return ScientificValidationService.load_validation_report()


def test_data_provenance_catalog(validation_report):
    """Verify that all datasets are explicitly tagged with provenance and synthetic flags."""
    catalog = validation_report.get("data_provenance_catalog", {})
    assert len(catalog) >= 5, "Catalog should track at least 5 primary data sources"

    for name, item in catalog.items():
        assert "provenance" in item
        assert "is_real_workforce_data" in item
        assert "description" in item
        assert item["provenance"].startswith(("[SYNTHETIC:", "[REAL/", "[CURATED:"))

    # Ensure synthetic datasets are marked clearly
    assert catalog["learner_interactions.csv"]["is_real_workforce_data"] is False
    assert catalog["learner_interactions.csv"]["provenance"] == "[SYNTHETIC:SIMULATED]"

    # Ensure real course catalogs are marked accurately
    assert catalog["igot_course_catalog.json"]["is_real_workforce_data"] is True


def test_data_leakage_audit(validation_report):
    """Verify that data leakage audit confirms strict disjoint splits and temporal validity."""
    leakage = validation_report.get("leakage_audit", {})
    assert leakage.get("audit_passed") is True
    assert leakage.get("identity_leakage_detected") is False
    assert leakage.get("identity_overlap_count") == 0
    assert leakage.get("temporal_leakage_detected") is False
    assert leakage.get("temporal_ordering_violations") == 0
    assert leakage.get("train_learner_count") > 0
    assert leakage.get("test_learner_count") > 0


def test_competency_estimator_benchmark(validation_report):
    """Verify multi-model comparison across Deterministic Baseline, BKT, and IRT-2PL."""
    estimators = validation_report.get("competency_estimator_evaluation", {})
    assert "deterministic_baseline" in estimators
    assert "bkt" in estimators
    assert "irt_2pl" in estimators

    det = estimators["deterministic_baseline"]
    bkt = estimators["bkt"]
    irt = estimators["irt_2pl"]

    for name, metrics in [("deterministic", det), ("bkt", bkt), ("irt", irt)]:
        assert 0.0 <= metrics["rmse"] <= 1.0, f"{name} RMSE out of range"
        assert 0.0 <= metrics["mae"] <= 1.0, f"{name} MAE out of range"
        assert 0.5 <= metrics["auc_roc"] <= 1.0, f"{name} AUC-ROC should be better than chance"
        assert 0.0 <= metrics["brier_score"] <= 1.0, f"{name} Brier score out of range"
        assert 0.0 <= metrics["expected_calibration_error"] <= 0.5, f"{name} ECE out of range"

    # Verify BKT and IRT provide competitive psychometrics
    assert bkt["rmse"] <= det["rmse"] + 0.05
    assert irt["auc_roc"] >= 0.60


def test_confidence_calibration_and_reliability_diagrams(validation_report):
    """Verify expected calibration error and reliability diagram bins."""
    estimators = validation_report.get("competency_estimator_evaluation", {})
    det = estimators.get("deterministic_baseline", {})
    
    assert "expected_calibration_error" in det
    assert 0.0 <= det["expected_calibration_error"] <= 0.35

    # Check reliability bins exist and have valid structure
    bins = det.get("reliability_bins", [])
    assert len(bins) == 10
    for b in bins:
        assert "mean_confidence" in b
        assert "observed_accuracy" in b
        assert "calibration_gap" in b


def test_evidence_weight_ablation_sensitivity(validation_report):
    """Verify ablation analysis measures the contribution of each evidence modality."""
    ablation = validation_report.get("evidence_weight_ablation", {})
    configs = ablation.get("configurations", {})
    assert "FULL_HEURISTIC_MODEL" in configs
    assert "NO_PRACTICAL_EVIDENCE" in configs
    assert "NO_SCENARIO_EVIDENCE" in configs
    assert "EQUAL_WEIGHTS_ABLATION" in configs

    full_rmse = configs["FULL_HEURISTIC_MODEL"]["rmse"]
    scenario_rmse = configs["NO_SCENARIO_EVIDENCE"]["rmse"]

    # Removing scenario assessments should degrade predictive accuracy (higher RMSE)
    assert scenario_rmse >= full_rmse, "Ablating scenario evidence must increase or equal prediction error"
    assert configs["NO_SCENARIO_EVIDENCE"]["delta_rmse_vs_full"] >= 0.0


def test_temporal_decay_benchmark(validation_report):
    """Verify linear and exponential forgetting curve benchmarks against 90-day trajectories."""
    temporal = validation_report.get("recency_decay_validation", {})
    benchmarks = temporal.get("decay_model_benchmarks", {})
    assert "LINEAR_DECAY_0_01" in benchmarks
    assert "EXPONENTIAL_HALF_LIFE_60D" in benchmarks
    assert "NO_DECAY" in benchmarks

    linear_rmse = benchmarks["LINEAR_DECAY_0_01"]["rmse"]
    no_decay_rmse = benchmarks["NO_DECAY"]["rmse"]

    # Linear decay heuristic should better match simulated forgetting than assuming zero decay
    assert linear_rmse <= no_decay_rmse


def test_mastery_threshold_sensitivity(validation_report):
    """Verify classification behavior across multiple decision cutoffs."""
    thresholds = validation_report.get("mastery_threshold_sensitivity", {})
    evals = thresholds.get("threshold_evaluations", {})

    for tau_str in ["threshold_0.50", "threshold_0.60", "threshold_0.70", "threshold_0.75", "threshold_0.80"]:
        assert tau_str in evals
        metrics = evals[tau_str]
        assert 0.0 <= metrics["precision"] <= 1.0
        assert 0.0 <= metrics["recall_sensitivity"] <= 1.0
        assert 0.0 <= metrics["f1_score"] <= 1.0

    assert thresholds.get("recommended_threshold") == 0.70


def test_adaptive_diagnostic_efficiency(validation_report):
    """Verify adaptive diagnostic reduces question burden while maintaining coverage."""
    diag = validation_report.get("diagnostic_efficiency", {})
    adaptive = diag.get("adaptive_strategy", {})
    random_strat = diag.get("random_static_strategy", {})

    assert adaptive["mean_questions_required"] < random_strat["mean_questions_required"]
    assert adaptive["repeated_question_rate"] == 0.0
    assert diag["efficiency_gain_percent"] >= 30.0


def test_recommendation_policy_evaluation(validation_report):
    """Verify heuristic ranker delivers positive competency gains and transparent justifications."""
    rec_policies = validation_report.get("recommendation_policy_evaluation", {})
    policies = rec_policies.get("policy_comparison", {})
    heuristic = policies.get("deterministic_heuristic_baseline", {})
    random_pol = policies.get("random_policy", {})

    assert heuristic["mean_observed_competency_gain"] > random_pol["mean_observed_competency_gain"]
    assert heuristic["decision"] == "RETAIN AS PRODUCTION BASELINE"


def test_practical_evaluator_consistency_and_degradation(validation_report):
    """Verify deterministic evaluator reproducibility and safe degradation on LLM failure."""
    practical = validation_report.get("practical_evaluator_audit", {})
    det_repro = practical.get("deterministic_reproducibility", {})
    llm_audit = practical.get("llm_evaluator_audit", {})

    assert det_repro["is_invariant"] is True
    assert det_repro["score_variance"] == 0.0
    assert llm_audit["degradation_handled_safely"] is True
    assert llm_audit["fallback_evaluator_type"] == "LLM_ASSISTED_FALLBACK"


def test_competency_graph_integrity(validation_report):
    """Verify graph topological integrity: no cycles, no orphan competencies."""
    graph = validation_report.get("competency_graph_validation", {})
    assert graph["graph_topology_valid"] is True
    assert graph["prerequisite_cycles_detected"] is False
    assert graph["orphan_competency_count"] == 0
    assert graph["competency_count"] >= 40
    assert graph["subskill_count"] >= 160


def test_model_selection_gate_structure(validation_report):
    """Verify that every system mechanism has an unambiguous scientific decision."""
    gates = validation_report.get("model_selection_gate", [])
    assert len(gates) >= 6

    valid_statuses = {
        "PRODUCTION BASELINE",
        "RESEARCH CANDIDATE",
        "EXPERIMENTAL",
        "ENGINEERING HEURISTIC",
        "DEFERRED",
        "NOT VALIDATED",
    }

    for gate in gates:
        assert "mechanism" in gate
        assert "scientific_status" in gate
        assert gate["scientific_status"] in valid_statuses
        assert "justification" in gate and len(gate["justification"]) > 10
        assert "dataset_evaluated" in gate


def test_admin_scientific_audit_endpoint(admin_user):
    """Test GET /api/admin/validation/scientific-audit endpoint with admin auth."""
    app.dependency_overrides[admin_router.get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            response = client.get("/api/admin/validation/scientific-audit")
            assert response.status_code == 200
            data = response.json()
            assert "scientific_report" in data
            assert "live_database_validation" in data
            assert data["validation_status"] == "SCIENTIFICALLY_VALIDATED"
            assert "model_gate_summary" in data
    finally:
        app.dependency_overrides.pop(admin_router.get_current_admin, None)


def test_admin_model_selection_gate_endpoint(admin_user):
    """Test GET /api/admin/validation/model-selection-gate endpoint."""
    app.dependency_overrides[admin_router.get_current_admin] = lambda: admin_user
    try:
        with TestClient(app) as client:
            response = client.get("/api/admin/validation/model-selection-gate")
            assert response.status_code == 200
            gates = response.json()
            assert isinstance(gates, list)
            assert len(gates) >= 6
            mechanisms = [g["mechanism"] for g in gates]
            assert "Heterogeneous Evidence Competency Estimator" in mechanisms
    finally:
        app.dependency_overrides.pop(admin_router.get_current_admin, None)


def test_admin_endpoints_unauthenticated_rejected():
    """Verify that unauthenticated requests to admin validation endpoints are rejected."""
    with TestClient(app) as client:
        # Without any authorization credentials, HTTPBearer returns 401 or 403
        r1 = client.get("/api/admin/validation/scientific-audit")
        assert r1.status_code in (401, 403), f"Expected 401/403, got {r1.status_code}"

        r2 = client.get("/api/admin/validation/model-selection-gate")
        assert r2.status_code in (401, 403), f"Expected 401/403, got {r2.status_code}"


def test_admin_endpoints_learner_forbidden():
    """Verify that authenticated non-admin learners cannot access admin validation endpoints."""
    # Mock user whose role is not admin
    learner_user = User(
        id=902,
        email="field_investigator@mospi.gov.in",
        full_name="MoSPI Field Investigator",
        password_hash="test_hashed_pwd",
        role_id=1,  # Non-admin role
        is_active=True,
    )
    # When get_current_user returns a non-admin learner, get_current_admin should raise 403
    from app.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: learner_user
    try:
        with TestClient(app) as client:
            r1 = client.get("/api/admin/validation/scientific-audit", headers={"Authorization": "Bearer fake-token"})
            assert r1.status_code == 403
            assert "Administrator access required" in r1.json()["detail"]

            r2 = client.get("/api/admin/validation/model-selection-gate", headers={"Authorization": "Bearer fake-token"})
            assert r2.status_code == 403
            assert "Administrator access required" in r2.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_live_database_health_metrics():
    """Verify live database graph and boundedness metrics via service."""
    db = SessionLocal()
    try:
        health = ScientificValidationService.get_live_database_health(db)
        assert health["competency_count"] > 0
        assert health["graph_topology_clean"] is True
        assert health["states_within_bounds"] is True
        assert health["boundedness_violations"]["unbounded_mastery"] == 0
        assert health["boundedness_violations"]["unbounded_confidence"] == 0
    finally:
        db.close()
