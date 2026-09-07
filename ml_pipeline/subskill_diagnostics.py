"""
ml_pipeline/subskill_diagnostics.py — Sub-Skill Diagnostic Classification & MMoE Recommender.

Implements the institutional diagnostic specifications from 'kpi sih.docx':
1. Multi-Source Sub-Skill Proficiency Index (SPI):
   SPI = 0.45 * Diagnostic + 0.35 * Lab + 0.20 * Adaptive
2. Sub-Skill Diagnostic Classification (Mastered, Developing, Remediation Required, Critical Gap).
3. Two-Stage Next-Best-Action Recommender utilizing Multi-Objective Utility Ranking (MMoE)
   across 5,600+ iGOT Karmayogi and NSSTA course modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid

DiagnosticStatus = Literal["MASTERED", "DEVELOPING", "REMEDIATION_REQUIRED", "CRITICAL_GAP"]


@dataclass
class SubSkillProfile:
    """Diagnostic profile for an individual sub-skill competency."""
    subskill_id: str
    subskill_name: str
    competency_id: str
    spi: float
    status: DiagnosticStatus
    visual_badge: str  # "EMERALD", "SLATE_BLUE", "AMBER", "ROSE"
    prescribed_action: str
    component_scores: Dict[str, float] = field(default_factory=dict)


class SubSkillDiagnosticEngine:
    """Computes composite SPI and classifies sub-skill mastery levels."""

    @staticmethod
    def calculate_spi(
        diagnostic_score: float,
        lab_score: float,
        adaptive_score: float,
        weights: Tuple[float, float, float] = (0.45, 0.35, 0.20),
    ) -> float:
        """
        Computes the weighted composite Sub-Skill Proficiency Index (SPI).
        """
        w_diag, w_lab, w_adapt = weights
        raw_spi = (w_diag * diagnostic_score) + (w_lab * lab_score) + (w_adapt * adaptive_score)
        return round(float(max(0.0, min(1.0, raw_spi))), 4)

    @classmethod
    def classify_subskill(
        cls,
        subskill_id: str,
        subskill_name: str,
        competency_id: str,
        diagnostic_score: float,
        lab_score: float,
        adaptive_score: float,
    ) -> SubSkillProfile:
        """
        Evaluates component scores, calculates SPI, and assigns institutional classification.
        """
        spi = cls.calculate_spi(diagnostic_score, lab_score, adaptive_score)

        if spi >= 0.75:
            status: DiagnosticStatus = "MASTERED"
            badge = "EMERALD"
            action = "Verified Competency. Advance to progressive competencies."
        elif spi >= 0.60:
            status = "DEVELOPING"
            badge = "SLATE_BLUE"
            action = "Functional Competency. Schedule 30-day retention verification check."
        elif spi >= 0.40:
            status = "REMEDIATION_REQUIRED"
            badge = "AMBER"
            action = "Sub-Skill Deficit. Trigger targeted micro-learning module (15-30 mins)."
        else:
            status = "CRITICAL_GAP"
            badge = "ROSE"
            action = "Foundational Failure. Trigger mandatory courseware and practical lab."

        return SubSkillProfile(
            subskill_id=subskill_id,
            subskill_name=subskill_name,
            competency_id=competency_id,
            spi=spi,
            status=status,
            visual_badge=badge,
            prescribed_action=action,
            component_scores={
                "diagnostic": round(diagnostic_score, 4),
                "lab": round(lab_score, 4),
                "adaptive": round(adaptive_score, 4),
            },
        )


class MMoERecommendationEngine:
    """
    Two-stage Next-Best-Action recommendation engine:
    1. Candidate Nomination (filtering sub-skill gaps).
    2. Multi-Objective Utility Ranking (MMoE) across remediation gain,
       time budget, cadre role criticality, and pedagogical modality match.
    """

    @staticmethod
    def compute_utility(
        remediation_gain: float,
        time_budget_fit: float,
        role_criticality: float,
        modality_match: float,
        weights: Tuple[float, float, float, float] = (0.40, 0.25, 0.20, 0.15),
    ) -> float:
        w_rem, w_time, w_role, w_mod = weights
        score = (
            (w_rem * remediation_gain)
            + (w_time * time_budget_fit)
            + (w_role * role_criticality)
            + (w_mod * modality_match)
        )
        return round(float(score), 4)

    @classmethod
    def rank_interventions(
        cls,
        candidate_courses: List[Dict[str, Any]],
        officer_cadre_role: str,
        officer_daily_budget_min: float,
        failed_subskill: SubSkillProfile,
        failed_tier: str = "MEDIUM",
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate courses and formats the explainable Next-Best-Action payload.
        """
        ranked = []
        for course in candidate_courses:
            # 1. Remediation Gain: sub-skill coverage (1 - SPI)
            gap = 1.0 - failed_subskill.spi
            remediation_gain = 1.0 if course.get("subskill_id") == failed_subskill.subskill_id else 0.5

            # 2. Time-Budget Fit
            duration = float(course.get("duration_minutes", 30))
            if duration <= officer_daily_budget_min:
                time_fit = 1.0 - (duration / (2.0 * officer_daily_budget_min))
            else:
                time_fit = max(0.10, 1.0 - ((duration - officer_daily_budget_min) / officer_daily_budget_min))

            # 3. Role Criticality (1.0 Core Cadre, 0.70 Secondary, 0.40 General)
            course_role = course.get("target_role", "CORE")
            if course_role == officer_cadre_role or course_role == "CORE":
                role_crit = 1.0
            elif course_role == "SECONDARY":
                role_crit = 0.70
            else:
                role_crit = 0.40

            # 4. Modality Match:
            # Failure on Hard -> Interactive Lab (1.0)
            # Failure on Medium -> Structured Video / Course (1.0)
            # Failure on Easy -> Micro-Reading Brief (1.0)
            modality = course.get("modality", "COURSE").upper()
            tier_upper = failed_tier.upper()
            if tier_upper == "HARD" and modality in ("LAB", "INTERACTIVE"):
                mod_match = 1.0
            elif tier_upper == "MEDIUM" and modality in ("COURSE", "VIDEO"):
                mod_match = 1.0
            elif tier_upper == "EASY" and modality in ("READING", "BRIEF"):
                mod_match = 1.0
            else:
                mod_match = 0.60

            utility = cls.compute_utility(remediation_gain, time_fit, role_crit, mod_match)
            ranked.append({
                **course,
                "utility_score": utility,
                "utility_breakdown": {
                    "remediation_gain": round(remediation_gain, 3),
                    "time_budget_fit": round(time_fit, 3),
                    "role_criticality": round(role_crit, 3),
                    "modality_match": round(mod_match, 3),
                },
            })

        ranked.sort(key=lambda x: x["utility_score"], reverse=True)
        return ranked
