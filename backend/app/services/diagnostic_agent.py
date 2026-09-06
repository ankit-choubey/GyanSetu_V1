from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.competency_engine import CompetencyCalculation
from app.services.ml_interfaces import (
    ProposedQuestion,
    QuestionSelectionRequest,
    QuestionSelector,
    validate_proposed_question,
)


@dataclass(frozen=True)
class DiagnosticDecision:
    competency_id: int
    sufficient_evidence: bool
    stop_reason: str
    evidence_count: int
    evidence_diversity: int
    target_subskill_id: int | None = None
    target_subskill_name: str | None = None
    next_question: ProposedQuestion | None = None


class DiagnosticAgent:
    """Deterministic backend workflow around a future ML question selector."""

    def decide(
        self,
        competency_id: int,
        calculation: CompetencyCalculation,
        selector: QuestionSelector,
    ) -> DiagnosticDecision:
        target_gap = calculation.gaps[0] if calculation.gaps else {}
        target_subskill_id = target_gap.get("subskill_id")
        target_subskill_name = target_gap.get("subskill_name")

        if calculation.status == "verified":
            return DiagnosticDecision(
                competency_id=competency_id,
                sufficient_evidence=True,
                stop_reason="Sufficient evidence for the configured competency criteria.",
                evidence_count=calculation.evidence_count,
                evidence_diversity=calculation.evidence_diversity,
                target_subskill_id=target_subskill_id if isinstance(target_subskill_id, int) else None,
                target_subskill_name=target_subskill_name if isinstance(target_subskill_name, str) else None,
            )

        request = QuestionSelectionRequest(
            competency_id=competency_id,
            subskill_id=target_subskill_id if isinstance(target_subskill_id, int) else None,
            subskill_name=target_subskill_name if isinstance(target_subskill_name, str) else None,
            evidence_count=calculation.evidence_count,
            evidence_diversity=calculation.evidence_diversity,
            competency_status=calculation.status,
            gap_reason=target_gap.get("reason") if isinstance(target_gap.get("reason"), str) else None,
            constraints=("use a validated assessment-bank question", "do not repeat completed evidence unnecessarily"),
        )
        proposed = validate_proposed_question(selector.select_next_question(request), request)
        return DiagnosticDecision(
            competency_id=competency_id,
            sufficient_evidence=False,
            stop_reason="Additional evidence is required for the identified gap.",
            evidence_count=calculation.evidence_count,
            evidence_diversity=calculation.evidence_diversity,
            target_subskill_id=request.subskill_id,
            target_subskill_name=request.subskill_name,
            next_question=proposed,
        )
