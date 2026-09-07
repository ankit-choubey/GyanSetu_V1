"""
ml_pipeline/tests/test_subskill_diagnostics.py — Unit tests for Sub-Skill Diagnostics & MMoE Recommender.
"""
from __future__ import annotations

from ml_pipeline.subskill_diagnostics import (
    SubSkillDiagnosticEngine,
    MMoERecommendationEngine,
    SubSkillProfile,
)


def test_spi_calculation_and_classification():
    """Verifies composite SPI formula and institutional diagnostic thresholds."""
    # 1. Mastered profile (Diagnostic 0.90, Lab 0.85, Adaptive 0.80)
    # SPI = 0.45*0.90 + 0.35*0.85 + 0.20*0.80 = 0.405 + 0.2975 + 0.16 = 0.8625
    prof_m = SubSkillDiagnosticEngine.classify_subskill(
        subskill_id="sub_stratified",
        subskill_name="Stratified Sampling",
        competency_id="comp_sampling",
        diagnostic_score=0.90,
        lab_score=0.85,
        adaptive_score=0.80,
    )
    assert prof_m.spi == 0.8625
    assert prof_m.status == "MASTERED"
    assert prof_m.visual_badge == "EMERALD"

    # 2. Remediation profile (Diagnostic 0.45, Lab 0.50, Adaptive 0.40)
    # SPI = 0.45*0.45 + 0.35*0.50 + 0.20*0.40 = 0.2025 + 0.175 + 0.08 = 0.4575
    prof_r = SubSkillDiagnosticEngine.classify_subskill(
        subskill_id="sub_bayesian",
        subskill_name="Bayesian Updating",
        competency_id="comp_bayes",
        diagnostic_score=0.45,
        lab_score=0.50,
        adaptive_score=0.40,
    )
    assert prof_r.spi == 0.4575
    assert prof_r.status == "REMEDIATION_REQUIRED"
    assert prof_r.visual_badge == "AMBER"


def test_mmoe_recommendation_utility_ranking():
    """Verifies that MMoE multi-objective ranking prioritizes courses matching gap and role."""
    failed_subskill = SubSkillProfile(
        subskill_id="sub_clt",
        subskill_name="Central Limit Theorem",
        competency_id="comp_prob",
        spi=0.45,
        status="REMEDIATION_REQUIRED",
        visual_badge="AMBER",
        prescribed_action="Trigger targeted micro-learning module",
    )

    candidate_courses = [
        {
            "id": "course_unrelated",
            "title": "Introduction to Python Basics",
            "subskill_id": "sub_python",
            "duration_minutes": 120,
            "target_role": "GENERAL",
            "modality": "COURSE",
        },
        {
            "id": "course_clt_perfect",
            "title": "MoSPI Practical Sampling & CLT Applications",
            "subskill_id": "sub_clt",
            "duration_minutes": 25,
            "target_role": "CORE",
            "modality": "COURSE",
        },
    ]

    ranked = MMoERecommendationEngine.rank_interventions(
        candidate_courses=candidate_courses,
        officer_cadre_role="CORE",
        officer_daily_budget_min=30.0,
        failed_subskill=failed_subskill,
        failed_tier="MEDIUM",
    )

    assert len(ranked) == 2
    # The CLT matching course with core role and 25 min duration must be ranked #1
    assert ranked[0]["id"] == "course_clt_perfect"
    assert ranked[0]["utility_score"] > ranked[1]["utility_score"]
