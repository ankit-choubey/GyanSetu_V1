from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.orchestrator import recalculate_competency_state


class InterventionLifecycleService:
    """Manages intervention recommendation lifecycle, feedback, completion, and outcome evidence feedback loop."""

    def __init__(self) -> None:
        pass

    def record_feedback(
        self,
        db: Session,
        user: User,
        recommendation_id: str,
        action: str,  # "ACCEPTED", "REJECTED", "SKIPPED"
        notes: str | None = None,
    ) -> RecommendationRecord:
        rec = db.execute(
            select(RecommendationRecord).where(
                RecommendationRecord.recommendation_id == recommendation_id,
                RecommendationRecord.user_id == user.id,
            )
        ).scalar_one_or_none()

        if not rec:
            raise ValueError(f"Recommendation '{recommendation_id}' not found for user {user.id}")

        action_map = {
            "ACCEPT": "ACCEPTED",
            "ACCEPTED": "ACCEPTED",
            "REJECT": "REJECTED",
            "REJECTED": "REJECTED",
            "SKIP": "SKIPPED",
            "SKIPPED": "SKIPPED",
            "COMPLETE": "COMPLETED",
            "COMPLETED": "COMPLETED",
            "START": "STARTED",
            "STARTED": "STARTED",
        }
        normalized = action.strip().upper()
        if normalized not in action_map:
            raise ValueError(f"Invalid feedback action '{action}'. Must be one of {set(action_map.keys())}")

        rec.status = action_map[normalized]
        if notes:
            rec.feedback_notes = notes
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    def start_intervention(
        self,
        db: Session,
        user: User,
        recommendation_id: str,
    ) -> RecommendationRecord:
        rec = db.execute(
            select(RecommendationRecord).where(
                RecommendationRecord.recommendation_id == recommendation_id,
                RecommendationRecord.user_id == user.id,
            )
        ).scalar_one_or_none()

        if not rec:
            raise ValueError(f"Recommendation '{recommendation_id}' not found for user {user.id}")

        rec.status = "STARTED"
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    def record_outcome(
        self,
        db: Session,
        user: User,
        intervention_id: int,
        status: str = "COMPLETED",  # COMPLETED or ABANDONED
        completion_score: float | None = None,
        has_post_assessment_evidence: bool = False,
        recommendation_id: str | None = None,
        idempotency_key: str | None = None,
        notes: str | None = None,
    ) -> InterventionOutcome:
        # 1. Check IDEMPOTENCY
        if idempotency_key:
            existing = db.execute(
                select(InterventionOutcome).where(
                    InterventionOutcome.idempotency_key == idempotency_key
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        intervention = db.get(Intervention, intervention_id)
        if not intervention:
            raise ValueError(f"Intervention #{intervention_id} not found")

        # Fetch current pre-mastery
        cid = intervention.competency_id
        pre_state = None
        if cid:
            pre_state = db.execute(
                select(CompetencyState).where(
                    CompetencyState.user_id == user.id,
                    CompetencyState.competency_id == cid,
                )
            ).scalar_one_or_none()

        pre_mastery = pre_state.mastery if pre_state else None
        post_mastery = pre_mastery
        created_evidence_id = None

        # 2. Enforce: Completion Alone != Mastery
        if status == "COMPLETED" and has_post_assessment_evidence and completion_score is not None and cid is not None:
            # Generate valid new evidence record in ledger
            new_evidence = Evidence(
                user_id=user.id,
                competency_id=cid,
                subskill_id=intervention.subskill_id,
                evidence_type=EvidenceType.PRACTICAL_TASK,
                title=f"Post-Intervention Outcome: {intervention.title}",
                description=f"Evidence generated from completing intervention #{intervention.id} ({intervention.title}).",
                score=completion_score,
                weight=1.0,
                source="INTERVENTION_POST_ASSESSMENT",
                provenance="[LIVE INTEGRATION]",
                reliability_status="VERIFIED",
                version=1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(new_evidence)
            db.flush()
            created_evidence_id = new_evidence.id

            # Trigger Phase 2 Competency Engine State Recalculation
            orch = recalculate_competency_state(
                db,
                user_id=user.id,
                competency_id=cid,
                triggering_evidence_id=new_evidence.id,
            )
            post_mastery = orch.state.mastery

            # If intervention targeted an active misconception and learner succeeded, resolve it!
            if intervention.target_misconception_pattern and completion_score >= 0.70:
                active_misc = db.execute(
                    select(Misconception).where(
                        Misconception.learner_id == user.id,
                        Misconception.pattern_key == intervention.target_misconception_pattern,
                        Misconception.resolved.is_(False),
                    )
                ).scalars().all()
                for m in active_misc:
                    m.resolved = True
                    m.resolution_evidence_id = created_evidence_id
        elif status == "COMPLETED" and not has_post_assessment_evidence:
            # Activity completion without evidence: competency remains unchanged!
            if notes:
                notes = f"{notes} | completion recorded; competency unchanged (insufficient evidence)"
            else:
                notes = "completion recorded; competency unchanged (insufficient evidence)"

        outcome = InterventionOutcome(
            user_id=user.id,
            intervention_id=intervention_id,
            recommendation_id=recommendation_id,
            status=status,
            completion_score=completion_score,
            has_post_assessment_evidence=has_post_assessment_evidence,
            evidence_id=created_evidence_id,
            pre_competency_mastery=pre_mastery,
            post_competency_mastery=post_mastery,
            idempotency_key=idempotency_key,
            notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        db.add(outcome)

        # Update recommendation status if recommendation_id was provided
        if recommendation_id:
            rec = db.execute(
                select(RecommendationRecord).where(
                    RecommendationRecord.recommendation_id == recommendation_id,
                    RecommendationRecord.user_id == user.id,
                )
            ).scalar_one_or_none()
            if rec:
                rec.status = status
                rec.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(outcome)
        return outcome
