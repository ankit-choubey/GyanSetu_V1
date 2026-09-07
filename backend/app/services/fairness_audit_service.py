from __future__ import annotations

from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.competency import Role
from app.models.competency_state import CompetencyState
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord
from app.models.user import User


class FairnessAuditService:
    """Evaluates fairness and cohort parity across authorized non-sensitive operational cohorts."""

    @classmethod
    def audit_operational_fairness(cls, db: Session) -> dict[str, Any]:
        """Audits outcome rates, acceptance rates, and competency disparities across operational roles."""
        roles = db.execute(select(Role).order_by(Role.id)).scalars().all()
        role_map = {r.id: r.name for r in roles}

        cohort_metrics: dict[str, dict[str, Any]] = {}
        disparity_flags: list[dict[str, Any]] = []

        # 1. Competency Mastery & Assessment Rates by Role
        for role_id, role_name in role_map.items():
            users_in_role = db.execute(select(User.id).where(User.role_id == role_id)).scalars().all()
            user_count = len(users_in_role)

            if user_count == 0:
                continue

            # Small cohort guard
            if user_count < 5:
                cohort_metrics[role_name] = {
                    "role_id": role_id,
                    "user_count": user_count,
                    "audit_status": "SUPPRESSED_SMALL_COHORT",
                    "reason": "Cohort size below statistical privacy threshold (N < 5)",
                }
                continue

            # Competency States
            states = db.execute(
                select(CompetencyState).where(CompetencyState.user_id.in_(users_in_role))
            ).scalars().all()

            mastery_vals = [s.mastery for s in states if s.mastery is not None]
            mean_mastery = round(sum(mastery_vals) / len(mastery_vals), 4) if mastery_vals else 0.0
            passing_states = [s for s in states if s.mastery is not None and s.mastery >= 0.70]
            passing_rate = round(len(passing_states) / len(mastery_vals), 4) if mastery_vals else 0.0

            # Recommendation Acceptance by Role
            recs = db.execute(
                select(RecommendationRecord).where(RecommendationRecord.user_id.in_(users_in_role))
            ).scalars().all()
            rec_count = len(recs)
            accepted_recs = [r for r in recs if r.status in ("ACCEPTED", "COMPLETED")]
            acceptance_rate = round(len(accepted_recs) / rec_count, 4) if rec_count > 0 else 0.0

            # Intervention Completion by Role
            outcomes = db.execute(
                select(InterventionOutcome).where(InterventionOutcome.user_id.in_(users_in_role))
            ).scalars().all()
            completed_outcomes = [o for o in outcomes if o.status == "COMPLETED"]
            completion_rate = round(len(completed_outcomes) / len(outcomes), 4) if outcomes else 0.0

            cohort_metrics[role_name] = {
                "role_id": role_id,
                "user_count": user_count,
                "audit_status": "EVALUATED",
                "mean_mastery": mean_mastery,
                "passing_rate": passing_rate,
                "acceptance_rate": acceptance_rate,
                "completion_rate": completion_rate,
                "evaluations_count": len(mastery_vals),
            }

        # 2. Evaluate Parity (Four-Fifths / 80% Rule across Evaluated Cohorts)
        evaluated = {k: v for k, v in cohort_metrics.items() if v.get("audit_status") == "EVALUATED"}

        if len(evaluated) >= 2:
            passing_rates = [v["passing_rate"] for v in evaluated.values() if v["evaluations_count"] > 0]
            if passing_rates and max(passing_rates) > 0:
                min_pass = min(passing_rates)
                max_pass = max(passing_rates)
                ratio = round(min_pass / max_pass, 4)
                if ratio < 0.80:
                    disparity_flags.append({
                        "metric": "passing_rate",
                        "disparity_ratio": ratio,
                        "benchmark": 0.80,
                        "classification": "POTENTIAL_DISPARITY",
                        "decision": "REQUIRES_REVIEW",
                        "interpretation": (
                            f"Passing rate disparity ratio between lowest and highest cohort is {ratio} (< 0.80). "
                            "This indicates differential learning progress across operational roles, requiring curriculum review. "
                            "Notice: This is an analytical disparity indicator, not confirmed psychometric bias."
                        ),
                    })
                else:
                    disparity_flags.append({
                        "metric": "passing_rate",
                        "disparity_ratio": ratio,
                        "benchmark": 0.80,
                        "classification": "NO_MATERIAL_DIFFERENCE_DETECTED",
                        "decision": "ACCEPTABLE",
                        "interpretation": f"Passing rate disparity ratio {ratio} is within acceptable parity threshold (>= 0.80).",
                    })

        overall_finding = "NO_MATERIAL_DIFFERENCE_DETECTED"
        if any(f["classification"] == "POTENTIAL_DISPARITY" for f in disparity_flags):
            overall_finding = "POTENTIAL_DISPARITY"
        elif not evaluated:
            overall_finding = "INSUFFICIENT_DATA"

        return {
            "fairness_framework": "OPERATIONAL_COHORT_PARITY_AUDIT",
            "overall_classification": overall_finding,
            "decision": "REQUIRES_REVIEW" if overall_finding == "POTENTIAL_DISPARITY" else "ACCEPTABLE",
            "sensitive_attribute_status": "FAIRNESS_ANALYSIS_LIMITED_BY_AVAILABLE_DATA",
            "demographic_data_disclosure": (
                "Protected demographic characteristics (e.g. gender, caste, age, ethnicity) are strictly NOT "
                "collected or stored within GyanSetu in accordance with civil service privacy policies. "
                "Fairness auditing is conducted exclusively on authorized operational cohorts (professional roles)."
            ),
            "evaluated_cohorts_count": len(evaluated),
            "suppressed_small_cohorts_count": sum(1 for v in cohort_metrics.values() if v.get("audit_status") == "SUPPRESSED_SMALL_COHORT"),
            "cohort_metrics": cohort_metrics,
            "disparity_evaluations": disparity_flags,
            "provenance": "[OPERATIONAL_AUDIT:NON_SENSITIVE]",
        }
