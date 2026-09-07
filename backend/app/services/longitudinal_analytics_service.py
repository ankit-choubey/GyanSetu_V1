from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence


class LongitudinalAnalyticsService:
    """Longitudinal competency evolution, uncertainty tracking, and evidence accumulation analytics."""

    RETENTION_WINDOW_DAYS = 90

    @classmethod
    def get_competency_history(
        cls,
        db: Session,
        user_id: int,
        competency_id: int,
    ) -> dict[str, Any]:
        """Returns detailed chronological trajectory and analytics for a specific competency."""
        comp = db.execute(select(Competency).where(Competency.id == competency_id)).scalar_one_or_none()
        if not comp:
            return {"error": f"Competency {competency_id} not found."}

        current_state = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == user_id,
                CompetencyState.competency_id == competency_id,
            )
        ).scalar_one_or_none()

        history_records = db.execute(
            select(CompetencyHistory)
            .where(
                CompetencyHistory.user_id == user_id,
                CompetencyHistory.competency_id == competency_id,
            )
            .order_by(CompetencyHistory.timestamp.asc(), CompetencyHistory.state_version.asc())
        ).scalars().all()

        timeline: list[dict[str, Any]] = []
        for h in history_records:
            timeline.append({
                "version": h.state_version,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None,
                "previous_mastery": h.previous_mastery,
                "new_mastery": h.new_mastery,
                "confidence": h.new_confidence,
                "uncertainty": round(1.0 - h.new_confidence, 4) if h.new_confidence is not None else 1.0,
                "status": h.new_status,
                "triggering_evidence_id": h.triggering_evidence_id,
                "calculation_version": h.calculation_version,
            })

        # Calculate trajectory metrics
        initial_mastery = timeline[0]["new_mastery"] if timeline else (current_state.mastery if current_state else None)
        current_mastery = current_state.mastery if current_state else None
        observed_gain = None
        if initial_mastery is not None and current_mastery is not None:
            observed_gain = round(current_mastery - initial_mastery, 4)

        # Evidence breakdown
        evidences = db.execute(
            select(Evidence).where(
                Evidence.user_id == user_id,
                Evidence.competency_id == competency_id,
            )
        ).scalars().all()

        source_counts: dict[str, int] = {}
        for ev in evidences:
            src = ev.source.value if hasattr(ev.source, "value") else str(ev.source)
            source_counts[src] = source_counts.get(src, 0) + 1

        # Retention check
        now = datetime.now(timezone.utc)
        last_assessed = current_state.last_assessed_at if current_state else None
        days_since_assessment = None
        refresher_needed = False
        if last_assessed:
            la_dt = last_assessed if last_assessed.tzinfo else last_assessed.replace(tzinfo=timezone.utc)
            days_since_assessment = (now - la_dt).days
            refresher_needed = days_since_assessment > cls.RETENTION_WINDOW_DAYS

        return {
            "competency_id": comp.id,
            "competency_name": comp.name,
            "user_id": user_id,
            "current_mastery": current_mastery,
            "current_confidence": current_state.confidence if current_state else 0.0,
            "current_uncertainty": round(current_state.uncertainty, 4) if current_state else 1.0,
            "current_status": current_state.status if current_state else "UNASSESSED",
            "initial_mastery": initial_mastery,
            "observed_competency_gain": observed_gain,
            "interpretation": (
                "Observed positive competency progression following intervention/assessment."
                if (observed_gain and observed_gain > 0)
                else "Competency trajectory stable or awaiting additional observational evidence."
            ),
            "total_state_transitions": len(timeline),
            "evidence_count_by_source": source_counts,
            "total_evidence_count": len(evidences),
            "last_assessed_at": last_assessed.isoformat() if last_assessed else None,
            "days_since_last_assessment": days_since_assessment,
            "retention_refresher_recommended": refresher_needed,
            "trajectory_timeline": timeline,
            "provenance": "[LONGITUDINAL_ANALYTICS:STATE_HISTORY]",
        }

    @classmethod
    def get_learner_timeline(cls, db: Session, user_id: int) -> dict[str, Any]:
        """Returns overall multi-competency longitudinal overview for a learner."""
        states = db.execute(
            select(CompetencyState).where(CompetencyState.user_id == user_id)
        ).scalars().all()

        competency_summaries: list[dict[str, Any]] = []
        for st in states:
            res = cls.get_competency_history(db, user_id=user_id, competency_id=st.competency_id)
            if "error" not in res:
                competency_summaries.append({
                    "competency_id": res["competency_id"],
                    "competency_name": res["competency_name"],
                    "current_mastery": res["current_mastery"],
                    "current_confidence": res["current_confidence"],
                    "status": res["current_status"],
                    "observed_gain": res["observed_competency_gain"],
                    "retention_refresher_recommended": res["retention_refresher_recommended"],
                    "total_evidence_count": res["total_evidence_count"],
                })

        return {
            "user_id": user_id,
            "total_tracked_competencies": len(competency_summaries),
            "competencies": competency_summaries,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "provenance": "[LONGITUDINAL_ANALYTICS:LEARNER_OVERVIEW]",
        }
