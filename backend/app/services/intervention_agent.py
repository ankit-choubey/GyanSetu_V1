from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.intervention import Intervention


@dataclass(frozen=True)
class RankedIntervention:
    intervention_id: int
    title: str
    description: str | None
    intervention_type: str
    priority: int
    relevance: float
    reason: str


@dataclass(frozen=True)
class NextBestAction:
    competency_id: int
    target_subskill_id: int | None
    gap_reason: str | None
    selected: RankedIntervention | None
    ranked_options: tuple[RankedIntervention, ...]
    explanation: str
    uncertainty: str | None = None


class InterventionAgent:
    """Ranks existing learning interventions without recalculating competency."""

    def rank(
        self,
        db: Session,
        user_id: int,
        competency_id: int,
        gap: Mapping[str, object],
    ) -> NextBestAction:
        target_subskill_id = gap.get("subskill_id")
        target_subskill_id = target_subskill_id if isinstance(target_subskill_id, int) else None
        gap_reason = gap.get("reason") if isinstance(gap.get("reason"), str) else None

        interventions = db.execute(
            select(Intervention).where(
                or_(Intervention.user_id.is_(None), Intervention.user_id == user_id),
                or_(Intervention.competency_id.is_(None), Intervention.competency_id == competency_id),
            )
        ).scalars().all()

        ranked: list[tuple[tuple[int, int, int], RankedIntervention]] = []
        for intervention in interventions:
            if intervention.subskill_id == target_subskill_id and target_subskill_id is not None:
                relevance = 1.0
                reason = "Directly targets the identified subskill gap."
                match_rank = 2
            elif intervention.competency_id == competency_id:
                relevance = 0.75
                reason = "Targets the learner's competency and supports the identified gap."
                match_rank = 1
            elif intervention.competency_id is None and intervention.subskill_id is None:
                relevance = 0.5
                reason = "Provides a general development action while targeted evidence is limited."
                match_rank = 0
            else:
                continue
            candidate = RankedIntervention(
                intervention_id=intervention.id,
                title=intervention.title,
                description=intervention.description,
                intervention_type=intervention.intervention_type,
                priority=intervention.priority,
                relevance=relevance,
                reason=reason,
            )
            ranked.append(((match_rank, -intervention.priority, -(intervention.id or 0)), candidate))

        ranked_options = tuple(candidate for _, candidate in sorted(ranked, key=lambda item: item[0], reverse=True))
        selected = ranked_options[0] if ranked_options else None
        if selected is None:
            return NextBestAction(
                competency_id=competency_id,
                target_subskill_id=target_subskill_id,
                gap_reason=gap_reason,
                selected=None,
                ranked_options=(),
                explanation="No suitable stored intervention matches the identified gap.",
                uncertainty="An intervention catalogue entry is required before recommending an action.",
            )
        return NextBestAction(
            competency_id=competency_id,
            target_subskill_id=target_subskill_id,
            gap_reason=gap_reason,
            selected=selected,
            ranked_options=ranked_options,
            explanation=selected.reason,
        )
