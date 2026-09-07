from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.governance import CompetencyGovernance, ReviewStatus
from app.models.intervention_outcome import InterventionOutcome


class DataQualityService:
    """Audits data health, evidence freshness, conflicting signals, and mapping governance."""

    @classmethod
    def audit_data_quality(cls, db: Session) -> dict[str, Any]:
        warnings: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(days=180)

        # 1. Stale Evidence Check (> 180 days)
        all_evidence = db.execute(select(Evidence)).scalars().all()
        stale_evidence_count = 0
        for ev in all_evidence:
            obs_at = ev.observed_at
            if obs_at.tzinfo is None:
                obs_at = obs_at.replace(tzinfo=timezone.utc)
            if obs_at < stale_cutoff:
                stale_evidence_count += 1

        if stale_evidence_count > 0:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "STALE_EVIDENCE",
                "severity": "MEDIUM",
                "affected_count": stale_evidence_count,
                "description": f"{stale_evidence_count} evidence records were observed more than 180 days ago without recent verification.",
                "remediation": "Trigger automated spaced reassessment via MonitoringAgent or prompt learner for refresher.",
                "provenance": "[DATA_QUALITY_AUDIT:EVIDENCE_LEDGER]",
            })

        # 2. Conflicting Evidence Check
        conflicting_states = db.execute(
            select(CompetencyState).where(CompetencyState.status == "CONFLICTING_EVIDENCE")
        ).scalars().all()

        if conflicting_states:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "CONFLICTING_EVIDENCE",
                "severity": "HIGH",
                "affected_count": len(conflicting_states),
                "description": f"{len(conflicting_states)} competency states exhibit conflicting evidence (e.g. high assessment score with failing practical demonstration).",
                "remediation": "Schedule supervised practical verification or diagnostic interview.",
                "provenance": "[DATA_QUALITY_AUDIT:COMPETENCY_STATE]",
            })

        # 3. Insufficient Evidence / High Uncertainty on Assessed States
        insufficient_evidence_states = db.execute(
            select(CompetencyState).where(
                CompetencyState.status == "ASSESSED",
                (CompetencyState.evidence_count < 2) | (CompetencyState.confidence < 0.35)
            )
        ).scalars().all()

        if insufficient_evidence_states:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "INSUFFICIENT_EVIDENCE",
                "severity": "LOW",
                "affected_count": len(insufficient_evidence_states),
                "description": f"{len(insufficient_evidence_states)} states have ASSESSED status with low confidence (< 0.35) or minimal evidence (< 2 items).",
                "remediation": "Administer targeted multi-modal diagnostic assessment to build confidence.",
                "provenance": "[DATA_QUALITY_AUDIT:COMPETENCY_STATE]",
            })

        # 4. Under-Review or Deprecated Competency Mappings
        gov_records = db.execute(select(CompetencyGovernance)).scalars().all()
        under_review = [g for g in gov_records if g.review_status == ReviewStatus.UNDER_REVIEW.value]
        deprecated = [g for g in gov_records if g.is_deprecated]

        if under_review:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "UNVERIFIED_COMPETENCY_MAPPING",
                "severity": "MEDIUM",
                "affected_count": len(under_review),
                "competency_ids": [g.competency_id for g in under_review],
                "description": f"{len(under_review)} competencies are currently marked UNDER_REVIEW by domain governance.",
                "remediation": "Fast-track expert psychometric validation panel review.",
                "provenance": "[DATA_QUALITY_AUDIT:GOVERNANCE_REGISTRY]",
            })

        if deprecated:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "DEPRECATED_COMPETENCY_MAPPING",
                "severity": "HIGH",
                "affected_count": len(deprecated),
                "competency_ids": [g.competency_id for g in deprecated],
                "description": f"{len(deprecated)} competencies are flagged as DEPRECATED.",
                "remediation": "Migrate learner evidence records to successor competencies.",
                "provenance": "[DATA_QUALITY_AUDIT:GOVERNANCE_REGISTRY]",
            })

        # 5. Orphaned Intervention Outcomes Check
        outcomes = db.execute(select(InterventionOutcome)).scalars().all()
        orphaned_count = sum(1 for o in outcomes if o.user_id is None or o.intervention_id is None)
        if orphaned_count > 0:
            warnings.append({
                "warning_type": "DATA_QUALITY_WARNING",
                "category": "ORPHANED_OUTCOMES",
                "severity": "HIGH",
                "affected_count": orphaned_count,
                "description": f"{orphaned_count} intervention outcome records lack valid foreign key associations.",
                "remediation": "Run database integrity cleanup script.",
                "provenance": "[DATA_QUALITY_AUDIT:INTERVENTIONS]",
            })

        # Overall Health Score (100 - penalties)
        penalty = min(60, len(warnings) * 12 + (15 if conflicting_states else 0))
        health_score = round((100 - penalty) / 100.0, 2)

        return {
            "audit_timestamp": now.isoformat(),
            "overall_data_health_score": health_score,
            "status": "HEALTHY" if health_score >= 0.80 else "ATTENTION_REQUIRED",
            "warnings_count": len(warnings),
            "warnings": warnings,
            "stale_evidence_count": stale_evidence_count,
            "conflicting_evidence_count": len(conflicting_states),
            "under_review_competency_count": len(under_review),
            "provenance": "[DATA_QUALITY_DIAGNOSTICS:LIVE_DB]",
        }
