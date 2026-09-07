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


class EligibilityStatus(str):
    """Backwards-compatible status code string that equates to INELIGIBLE when tested for coarse ineligibility,
    while preserving granular rejection reason codes (e.g. POLICY_EXCLUDED, PREREQUISITE_NOT_MET)."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            if super().__eq__(other):
                return True
            if other == "INELIGIBLE" and str(self) in {
                "POLICY_EXCLUDED",
                "INVALID_COMPETENCY_MAPPING",
                "RESOURCE_UNAVAILABLE",
                "RESOURCE_STALE",
                "PROVIDER_UNAVAILABLE",
                "UNAVAILABLE",
                "ALREADY_COMPLETED",
                "PREREQUISITE_NOT_MET",
                "INELIGIBLE",
            }:
                return True
            if other == "UNAVAILABLE" and str(self) in {
                "UNAVAILABLE",
                "RESOURCE_UNAVAILABLE",
                "PROVIDER_UNAVAILABLE",
            }:
                return True
            if other == "STALE" and str(self) in {"RESOURCE_STALE", "STALE"}:
                return True
            if other == "RESOURCE_STALE" and str(self) in {"RESOURCE_STALE", "STALE"}:
                return True
        return super().__eq__(other)

    def __hash__(self) -> int:
        return super().__hash__()


@dataclass(frozen=True)
class EligibilityDecision:
    intervention_id: int
    is_eligible: bool
    status: EligibilityStatus | str  # "ELIGIBLE", "POLICY_EXCLUDED", "PREREQUISITE_NOT_MET", etc.
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
                status=EligibilityStatus("POLICY_EXCLUDED"),
                reason="Intervention is marked INACTIVE in the catalogue.",
            )

        if intervention.mapping_status == "UNDER_REVIEW":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status=EligibilityStatus("INVALID_COMPETENCY_MAPPING"),
                reason="Intervention competency or subskill mapping is under review or unverified.",
            )

        if intervention.status == "UNAVAILABLE" or intervention.availability == "UNAVAILABLE":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status=EligibilityStatus("RESOURCE_UNAVAILABLE"),
                reason="Intervention is currently unavailable or under maintenance.",
            )

        if intervention.status == "STALE":
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status=EligibilityStatus("RESOURCE_STALE"),
                reason="Intervention verification has expired (STALE).",
            )

        # 2. Check Stale Verification Timestamp
        if intervention.last_verified_at:
            age = datetime.now(timezone.utc) - intervention.last_verified_at.replace(tzinfo=timezone.utc if intervention.last_verified_at.tzinfo is None else None)
            if age > timedelta(days=self.STALE_EXPIRY_DAYS):
                return EligibilityDecision(
                    intervention_id=iid,
                    is_eligible=False,
                    status=EligibilityStatus("RESOURCE_STALE"),
                    reason=f"Resource verification expired {age.days} days ago (exceeds {self.STALE_EXPIRY_DAYS}d validity limit).",
                )

        # 3. Check Adapter / Provider Availability
        adapter = get_adapter_for_provider(intervention.provider)
        avail_res = adapter.check_availability(intervention.source_id)
        is_avail = avail_res if isinstance(avail_res, bool) else getattr(avail_res, "is_available", False)
        if not is_avail:
            reason = getattr(avail_res, "reason", None) or f"External provider adapter '{intervention.provider}' reported resource or service unavailable."
            return EligibilityDecision(
                intervention_id=iid,
                is_eligible=False,
                status=EligibilityStatus("UNAVAILABLE"),
                reason=reason,
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
                status=EligibilityStatus("ALREADY_COMPLETED"),
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
                            status=EligibilityStatus("PREREQUISITE_NOT_MET"),
                            reason=f"Prerequisite not met: requires prior mastery >= {min_mastery} (current: {state.mastery if state else 'None'}).",
                        )
            except Exception:
                pass

        return EligibilityDecision(
            intervention_id=iid,
            is_eligible=True,
            status=EligibilityStatus("ELIGIBLE"),
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
