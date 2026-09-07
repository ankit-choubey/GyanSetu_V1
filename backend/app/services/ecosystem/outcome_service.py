from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.user import User
from app.services.adapters import (
    InterventionAdapter,
    LaunchResult,
    get_adapter_for_provider,
)
from app.services.orchestrator import recalculate_competency_state


class EcosystemOutcomeService:
    """Service to handle external provider launches, tracking, and outcome propagation into GyanSetu."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def launch_intervention(
        self, intervention_id: int, current_user: User
    ) -> LaunchResult:
        intervention = self.db.get(Intervention, intervention_id)
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        adapter: InterventionAdapter = get_adapter_for_provider(intervention.provider)
        res_id = intervention.source_id or str(intervention.id)
        result = adapter.launch_resource(res_id, current_user.id)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=503,
                detail=f"Provider {intervention.provider} is currently unable to launch resource {res_id}",
            )

        return result

    def record_external_outcome(
        self,
        intervention_id: int,
        current_user: User,
        status: str = "COMPLETED",
        completion_score: float | None = None,
        has_post_assessment_evidence: bool = False,
        provider_activity_id: str | None = None,
        idempotency_key: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        intervention = self.db.get(Intervention, intervention_id)
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        # 1. Idempotency Protection
        if idempotency_key:
            existing = self.db.execute(
                select(InterventionOutcome).where(
                    InterventionOutcome.idempotency_key == idempotency_key
                )
            ).scalar_one_or_none()
            if existing:
                if existing.user_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Access forbidden: Idempotency key conflict")
                return {
                    "outcome_id": existing.id,
                    "status": existing.status,
                    "evidence_id": existing.evidence_id,
                    "pre_competency_mastery": existing.pre_competency_mastery,
                    "post_competency_mastery": existing.post_competency_mastery,
                    "competency_updated": existing.has_post_assessment_evidence,
                    "idempotent_replay": True,
                    "message": "Idempotent response: outcome previously recorded",
                }

        # 2. Capture Pre-Competency Mastery
        from app.models.competency_state import CompetencyState

        comp_state = None
        pre_mastery = None
        if intervention.competency_id:
            comp_state = self.db.execute(
                select(CompetencyState).where(
                    CompetencyState.user_id == current_user.id,
                    CompetencyState.competency_id == intervention.competency_id,
                )
            ).scalar_one_or_none()
            if comp_state:
                pre_mastery = comp_state.mastery

        evidence_id = None
        post_mastery = pre_mastery

        # 3. Scientific Non-Mastery Enforcement:
        # Activity completion alone does NOT grant competency mastery.
        # Only verified post-assessment evidence permits competency recalculation.
        if has_post_assessment_evidence and completion_score is not None and intervention.competency_id:
            evidence_type = EvidenceType.PRACTICAL_TASK
            if intervention.modality in ("ASSESSMENT", "DIAGNOSTIC"):
                evidence_type = EvidenceType.ASSESSMENT
            elif intervention.modality == "VIRTUAL_LAB":
                evidence_type = EvidenceType.PRACTICAL_TASK

            provenance = (
                "[SANDBOX DATA]"
                if intervention.integration_mode == "SANDBOX"
                else "[LIVE INTEGRATION]"
            )

            evidence_record = Evidence(
                user_id=current_user.id,
                competency_id=intervention.competency_id,
                title=f"Ecosystem Outcome: {intervention.provider} — {intervention.title}",
                evidence_type=evidence_type,
                score=completion_score,
                weight=1.0,
                source=f"ECOSYSTEM_{intervention.provider.upper()}",
                provenance=provenance,
                version=1,
                reliability_status="VERIFIED",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(evidence_record)
            self.db.flush()
            evidence_id = evidence_record.id

            # Trigger atomic recalculation
            orch_result = recalculate_competency_state(
                db=self.db,
                user_id=current_user.id,
                competency_id=intervention.competency_id,
                triggering_evidence_id=evidence_id,
            )
            if orch_result and orch_result.state:
                post_mastery = orch_result.state.mastery
        else:
            if not notes:
                notes = "Activity completed without post-assessment evidence; competency state unchanged per scientific honesty standard."

        # 4. Persist Outcome Record
        outcome = InterventionOutcome(
            user_id=current_user.id,
            intervention_id=intervention.id,
            provider=intervention.provider,
            provider_resource_id=intervention.source_id,
            provider_activity_id=provider_activity_id,
            integration_mode=intervention.integration_mode,
            status=status,
            completion_score=completion_score,
            has_post_assessment_evidence=has_post_assessment_evidence,
            evidence_id=evidence_id,
            pre_competency_mastery=pre_mastery,
            post_competency_mastery=post_mastery,
            idempotency_key=idempotency_key,
            notes=notes,
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(outcome)
        self.db.commit()
        self.db.refresh(outcome)

        return {
            "outcome_id": outcome.id,
            "status": outcome.status,
            "evidence_id": outcome.evidence_id,
            "pre_competency_mastery": outcome.pre_competency_mastery,
            "post_competency_mastery": outcome.post_competency_mastery,
            "competency_updated": outcome.has_post_assessment_evidence,
            "idempotent_replay": False,
            "message": "Outcome recorded successfully",
        }
