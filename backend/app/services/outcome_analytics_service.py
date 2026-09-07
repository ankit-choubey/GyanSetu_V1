from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord


class OutcomeAnalyticsService:
    """Intervention and recommendation outcome analytics with non-causal association metrics."""

    @classmethod
    def get_recommendation_funnel_analytics(cls, db: Session) -> dict[str, Any]:
        """Calculates the end-to-end recommendation funnel metrics."""
        records = db.execute(select(RecommendationRecord)).scalars().all()
        total_recs = len(records)

        status_counts: dict[str, int] = {}
        for r in records:
            st = r.status.upper() if r.status else "UNKNOWN"
            status_counts[st] = status_counts.get(st, 0) + 1

        proposed = total_recs
        accepted = status_counts.get("ACCEPTED", 0) + status_counts.get("STARTED", 0) + status_counts.get("COMPLETED", 0)
        rejected = status_counts.get("REJECTED", 0)
        skipped = status_counts.get("SKIPPED", 0)
        started = status_counts.get("STARTED", 0) + status_counts.get("COMPLETED", 0)
        completed = status_counts.get("COMPLETED", 0)

        acceptance_rate = round(accepted / proposed, 4) if proposed > 0 else 0.0
        completion_rate = round(completed / started, 4) if started > 0 else 0.0
        rejection_rate = round(rejected / proposed, 4) if proposed > 0 else 0.0

        return {
            "total_recommendations_generated": proposed,
            "status_distribution": status_counts,
            "funnel": {
                "generated": proposed,
                "accepted": accepted,
                "started": started,
                "completed": completed,
                "skipped": skipped,
                "rejected": rejected,
            },
            "acceptance_rate": acceptance_rate,
            "completion_rate": completion_rate,
            "rejection_rate": rejection_rate,
            "data_mode": "OBSERVATIONAL",
            "provenance": "[RECOMMENDATION_ANALYTICS:FUNNEL]",
        }

    @classmethod
    def get_intervention_outcome_analytics(
        cls,
        db: Session,
        provider: str | None = None,
        competency_id: int | None = None,
    ) -> dict[str, Any]:
        """Analyzes intervention outcomes, observed post-intervention gains, and provider metrics."""
        stmt = select(InterventionOutcome)
        if provider:
            stmt = stmt.join(Intervention).where(Intervention.provider == provider)
        if competency_id is not None:
            stmt = stmt.join(Intervention).where(Intervention.competency_id == competency_id)

        outcomes = db.execute(stmt).scalars().all()
        total_outcomes = len(outcomes)

        if total_outcomes == 0:
            return {
                "total_outcomes_recorded": 0,
                "status": "INSUFFICIENT_DATA",
                "completed_count": 0,
                "completion_rate": 0.0,
                "average_score": None,
                "observed_gains": {
                    "count": 0,
                    "mean_gain": None,
                    "median_gain": None,
                    "positive_outcome_rate": 0.0,
                },
                "provider_breakdown": {},
                "provenance": "[OUTCOME_ANALYTICS:EMPTY_POOL]",
            }

        completed = [o for o in outcomes if (o.status and o.status.upper() == "COMPLETED")]
        completed_count = len(completed)
        scores = [o.completion_score for o in completed if o.completion_score is not None]
        avg_score = round(sum(scores) / len(scores), 4) if scores else None

        # Calculate observed gains where pre and post mastery exist
        gains: list[float] = []
        for o in completed:
            if o.pre_competency_mastery is not None and o.post_competency_mastery is not None:
                delta = o.post_competency_mastery - o.pre_competency_mastery
                gains.append(round(delta, 4))

        mean_gain = round(sum(gains) / len(gains), 4) if gains else None
        median_gain = round(statistics.median(gains), 4) if gains else None
        positive_gain_count = sum(1 for g in gains if g > 0)
        positive_rate = round(positive_gain_count / len(gains), 4) if gains else 0.0

        # Provider breakdown
        all_interventions = {i.id: i for i in db.execute(select(Intervention)).scalars().all()}
        provider_counts: dict[str, dict[str, Any]] = {}
        for o in outcomes:
            it = all_interventions.get(o.intervention_id)
            prov = o.provider or (it.provider if it else "UNKNOWN")
            if prov not in provider_counts:
                provider_counts[prov] = {
                    "total": 0,
                    "completed": 0,
                    "scores": [],
                    "mode": o.integration_mode or (getattr(it, "integration_mode", "SANDBOX") if it else "SANDBOX"),
                }
            provider_counts[prov]["total"] += 1
            if o.status and o.status.upper() == "COMPLETED":
                provider_counts[prov]["completed"] += 1
                if o.completion_score is not None:
                    provider_counts[prov]["scores"].append(o.completion_score)

        for p_data in provider_counts.values():
            s_list = p_data.pop("scores")
            p_data["avg_score"] = round(sum(s_list) / len(s_list), 4) if s_list else None
            p_data["completion_rate"] = round(p_data["completed"] / p_data["total"], 4) if p_data["total"] > 0 else 0.0

        return {
            "total_outcomes_recorded": total_outcomes,
            "completed_count": completed_count,
            "completion_rate": round(completed_count / total_outcomes, 4) if total_outcomes > 0 else 0.0,
            "average_score": avg_score,
            "observed_gains": {
                "sample_size": len(gains),
                "mean_gain": mean_gain,
                "median_gain": median_gain,
                "positive_outcome_rate": positive_rate,
                "causal_disclaimer": "Metrics represent observational associative changes; no causal claim of direct effect is asserted.",
            },
            "provider_breakdown": provider_counts,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "provenance": "[OUTCOME_ANALYTICS:OBSERVED_DELTAS]",
        }
