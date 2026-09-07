from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.competency_state import CompetencyState
from app.models.intervention import Intervention
from app.models.misconception import Misconception
from app.services.eligibility_engine import EligibilityDecision


@dataclass(frozen=True)
class ScoredIntervention:
    intervention: Intervention
    total_score: float
    relevance: float
    positive_factors: list[str]
    negative_factors: list[str]
    caution_notes: list[str]
    primary_reason: str


@dataclass(frozen=True)
class RankingResult:
    selected: ScoredIntervention | None
    ranked_options: list[ScoredIntervention]
    rejected_candidates: list[dict[str, Any]]
    policy_version: str = "v1.0-deterministic-baseline"


class RecommendationRanker:
    """Deterministic, transparent, multi-factor ranking policy for eligible intervention candidates."""

    POLICY_VERSION = "v1.0-deterministic-baseline"

    # Engineering heuristic weights (auditable & configurable)
    WEIGHTS = {
        "misconception_match": 0.35,
        "subskill_match": 0.30,
        "competency_match": 0.15,
        "gap_severity": 0.10,
        "modality_fit": 0.05,
        "priority": 0.05,
    }

    def rank(
        self,
        eligible_candidates: list[Intervention],
        ineligible_decisions: list[EligibilityDecision],
        target_competency_id: int | None,
        target_subskill_id: int | None,
        target_subskill_name: str | None,
        active_misconceptions: list[Misconception] | None,
        competency_state: CompetencyState | None,
        gap_severity: str = "MEDIUM",
    ) -> RankingResult:
        active_patterns = {m.pattern_key for m in (active_misconceptions or []) if not m.resolved and m.pattern_key}
        current_confidence = competency_state.confidence if competency_state else 0.0
        current_mastery = competency_state.mastery if competency_state else None

        scored: list[ScoredIntervention] = []

        for item in eligible_candidates:
            score = 0.0
            pos: list[str] = []
            neg: list[str] = []
            cautions: list[str] = []

            # 1. Misconception match (Top priority for concept repair)
            if item.target_misconception_pattern and item.target_misconception_pattern in active_patterns:
                score += self.WEIGHTS["misconception_match"]
                pos.append(f"+ Directly addresses active misconception: '{item.target_misconception_pattern}'")
            elif item.intervention_type == "remediation" and active_patterns:
                score += self.WEIGHTS["misconception_match"] * 0.3
                pos.append("+ General concept remediation activity")

            # 2. Subskill alignment
            if target_subskill_id is not None and item.subskill_id == target_subskill_id:
                score += self.WEIGHTS["subskill_match"]
                sub_label = target_subskill_name or f"ID #{target_subskill_id}"
                pos.append(f"+ High alignment: specifically targets subskill '{sub_label}'")
            elif item.subskill_id is not None:
                neg.append("- Lower subskill specificity: targets adjacent subskill")

            # 3. Competency alignment
            if target_competency_id is not None and item.competency_id == target_competency_id:
                score += self.WEIGHTS["competency_match"]
                pos.append("+ Directly aligns with target competency requirements")
            elif item.competency_id is None:
                pos.append("+ General workforce development resource")

            # 4. Gap severity factor
            if gap_severity == "HIGH":
                # For high gaps, prefer structured scenarios and labs
                if item.modality in {"PRACTICE_SCENARIO", "VIRTUAL_LAB"}:
                    score += self.WEIGHTS["gap_severity"]
                    pos.append("+ High gap severity: interactive modality prioritized")
                else:
                    score += self.WEIGHTS["gap_severity"] * 0.5
            else:
                score += self.WEIGHTS["gap_severity"] * 0.7

            # 5. Modality fit
            if item.modality in {"PRACTICE_SCENARIO", "ASSESSMENT", "VIRTUAL_LAB"}:
                score += self.WEIGHTS["modality_fit"]
                pos.append(f"+ Active practical modality: {item.modality}")
            else:
                score += self.WEIGHTS["modality_fit"] * 0.5

            # 6. Priority boost from catalogue (1 = top priority)
            priority_factor = max(0.0, 1.0 - ((item.priority - 1) * 0.2))
            score += self.WEIGHTS["priority"] * priority_factor

            # Caution notes based on uncertainty and evidence confidence
            if current_confidence < 0.50:
                cautions.append(f"Underlying competency estimate has moderate confidence ({current_confidence:.2f}).")
            if current_mastery is not None and current_mastery < 0.30:
                cautions.append("Learner has significant foundational gaps in this area.")

            # Formulate primary reason
            if item.target_misconception_pattern and item.target_misconception_pattern in active_patterns:
                primary_reason = f"Prioritized for contrastive remediation addressing misconception '{item.target_misconception_pattern}'."
            elif target_subskill_id is not None and item.subskill_id == target_subskill_id:
                primary_reason = f"High alignment directly targeting identified subskill gap."
            elif target_competency_id is not None and item.competency_id == target_competency_id:
                primary_reason = "Strong competency alignment supporting development goals."
            else:
                primary_reason = "General foundational capability development."

            relevance = min(1.0, round(score / sum(self.WEIGHTS.values()), 4))
            scored.append(
                ScoredIntervention(
                    intervention=item,
                    total_score=round(score, 4),
                    relevance=relevance,
                    positive_factors=pos,
                    negative_factors=neg,
                    caution_notes=cautions,
                    primary_reason=primary_reason,
                )
            )

        # Sort ranked options by total score descending, then priority ascending, then ID ascending
        ranked = sorted(
            scored,
            key=lambda x: (x.total_score, -x.intervention.priority, -(x.intervention.id or 0)),
            reverse=True,
        )

        selected = ranked[0] if ranked else None

        # Build rejection audit log
        rejected: list[dict[str, Any]] = []

        # 1. Disqualified by eligibility engine
        for dec in ineligible_decisions:
            if not dec.is_eligible:
                rejected.append({
                    "intervention_id": dec.intervention_id,
                    "status": dec.status,
                    "reason": dec.reason or "Failed eligibility criteria",
                })

        # 2. Eligible but not selected (lower ranked)
        if len(ranked) > 1:
            for other in ranked[1:]:
                oid = other.intervention.id or 0
                rejected.append({
                    "intervention_id": oid,
                    "status": "LOWER_RANKED",
                    "reason": f"Lower composite score ({other.total_score:.3f} vs {selected.total_score:.3f} for top candidate)",
                })

        return RankingResult(
            selected=selected,
            ranked_options=ranked,
            rejected_candidates=rejected,
            policy_version=self.POLICY_VERSION,
        )
