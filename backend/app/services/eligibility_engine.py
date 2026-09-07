from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency_state import CompetencyState
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.user import User
from app.services.adapters.provider_adapters import get_adapter_for_provider


@dataclass(frozen=True)
class EligibilityDecision:
    intervention_id: int
    is_eligible: bool
    status: str  # "ELIGIBLE", "INELIGIBLE", "UNAVAILABLE", "STALE"
    reason: str | None = None


class EligibilityEngine:
    """Evaluates candidate interventions against learner prerequisites, status, and adapter availability."""

    STALE_EXPIRY_DAYS = 180  # Resources unverified for >180 days are considered stale

    def evaluate_candidate(
        self,
        db: Session,
        learner: User,
        intervention: Intervention,
        completed_intervention_ids: set[int] | None = None,
    ) -> EligibilityDecision:
        iid = intervention.id or 0

        # 1. Check Intervention Status
        if intervention.status == "INACTIVE":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status="INELIGIBLE",
                reason="Intervention is marked INACTIVE in the catalogue.",
            )

        if intervention.status == "UNAVAILABLE" or intervention.availability == "UNAVAILABLE":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status="UNAVAILABLE",
                reason="Intervention is currently unavailable or under maintenance.",
            )

        if intervention.status == "STALE":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status="STALE",
                reason="Intervention verification has expired (STALE).",
            )

        # 2. Check Stale Verification Timestamp
        if intervention.last_verified_at:
            age = datetime.now(timezone.utc) - intervention.last_verified_at.replace(tzinfo=timezone.utc if intervention.last_verified_at.tzinfo is None else None)
            if age > timedelta(days=self.STALE_EXPIRY_DAYS):
                return EligibilityDecision(
                    intervention_id=iid,
                    is_eligible=False,
                    status="STALE",
                    reason=f"Resource verification expired {age.days} days ago (exceeds {self.STALE_EXPIRY_DAYS}d validity limit).",
                )

        # 3. Check Adapter / Provider Availability
        adapter = get_adapter_for_provider(intervention.provider)
        if not adapter.check_availability(intervention.source_id):
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status="UNAVAILABLE",
                reason=f"External provider adapter '{intervention.provider}' reported resource or service unavailable.",
            )

        # 4. Check Prior Completion (Avoid repeating already mastered interventions unless practice)
        if completed_intervention_ids is None:
            completed_outcomes = db.execute(
                select(InterventionOutcome.intervention_id).where(
                    InterventionOutcome.user_id == learner.id,
                    InterventionOutcome.status == "COMPLETED",
                )
            ).scalars().all()
            completed_intervention_ids = set(completed_outcomes)

        if iid in completed_intervention_ids and intervention.intervention_type not in {"retrieval_practice", "scenario_practice"}:
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status="INELIGIBLE",
                reason="Learner has already successfully completed this intervention.",
            )

        # 5. Check Prerequisites
        if intervention.prerequisites_json:
            try:
                prereqs = json.loads(intervention.prerequisites_json)
                required_subskills = prereqs.get("required_subskills", [])
                min_mastery = prereqs.get("min_mastery", 0.60)

                # Query learner's competency state for required subskills / competencies
                if required_subskills:
                    # Check if learner has required competency state
                    # For simplicity and strictness: check if competency state exists and meets min_mastery
                    state = db.execute(
                        select(CompetencyState).where(
                            CompetencyState.user_id == learner.id,
                            CompetencyState.competency_id == intervention.competency_id,
                        )
                    ).scalar_one_or_none()

                    if not state or state.mastery is None or state.mastery < min_mastery:
                        return EligibilityDecision(
                            intervention_id=iid,
                            is_eligible=False,
                            status="INELIGIBLE",
                            reason=f"Prerequisite not met: requires prior mastery >= {min_mastery} (current: {state.mastery if state else 'None'}).",
                        )
            except Exception:
                pass

        return EligibilityDecision(
            intervention_id=iid,
            is_eligible=True,
            status="ELIGIBLE",
            reason=None,
        )

    def filter_candidates(
        self,
        db: Session,
        learner: User,
        candidates: list[Intervention],
    ) -> tuple[list[Intervention], list[EligibilityDecision]]:
        """Filter a list of candidates into eligible candidates and rejection decisions."""
        completed_outcomes = set(
            db.execute(
                select(InterventionOutcome.intervention_id).where(
                    InterventionOutcome.user_id == learner.id,
                    InterventionOutcome.status == "COMPLETED",
                )
            ).scalars().all()
        )

        eligible: list[Intervention] = []
        decisions: list[EligibilityDecision] = []

        for candidate in candidates:
            decision = self.evaluate_candidate(db, learner, candidate, completed_outcomes)
            decisions.append(decision)
            if decision.is_eligible:
                eligible.append(candidate)

        return eligible, decisions
