from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from models.bkt_model import BKTModel
from models.irt_model import IRT2PL


@dataclass(frozen=True)
class CompetencyEstimateResult:
    mastery: float | None
    confidence: float
    uncertainty: float
    status: str
    model_name: str
    metadata: dict[str, Any]


class CompetencyEstimator(ABC):
    """Replaceable interface for learner competency and ability estimation."""

    @abstractmethod
    def estimate(
        self,
        evidence_sequence: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> CompetencyEstimateResult:
        """Computes mastery, confidence, and uncertainty from an evidence sequence."""
        ...


class DeterministicBaselineEstimator(CompetencyEstimator):
    """
    Canonical system-of-record estimator.
    Uses multi-source weighted fusion, recency decay, and unassessed guarantees.
    """

    TYPE_WEIGHTS = {
        "APPLICATION_SCENARIO": 0.35,
        "PRACTICAL_TASK": 0.30,
        "KNOWLEDGE_ASSESSMENT": 0.20,
        "TRAINING_HISTORY": 0.10,
        "WORKPLACE_SIGNAL": 0.05,
        "SELF_REPORT": 0.02,
    }

    def estimate(
        self,
        evidence_sequence: Sequence[dict[str, Any]],
        now: datetime | None = None,
        **kwargs: Any,
    ) -> CompetencyEstimateResult:
        if not evidence_sequence:
            return CompetencyEstimateResult(
                mastery=None,
                confidence=0.0,
                uncertainty=1.0,
                status="UNASSESSED",
                model_name="DeterministicBaseline",
                metadata={"reason": "No evidence recorded."},
            )

        current_time = now or datetime.now(timezone.utc)
        weighted_scores: list[float] = []
        total_weight = 0.0
        by_type: dict[str, list[float]] = {}

        for item in evidence_sequence:
            score = item.get("score")
            if score is None:
                continue
            ev_type = str(item.get("evidence_type", "KNOWLEDGE_ASSESSMENT"))
            by_type.setdefault(ev_type, []).append(float(score))

            base_w = self.TYPE_WEIGHTS.get(ev_type, 0.10)
            obs = item.get("observed_at")
            if isinstance(obs, str):
                try:
                    obs = datetime.fromisoformat(obs)
                except Exception:
                    obs = current_time
            elif not isinstance(obs, datetime):
                obs = current_time

            if obs.tzinfo is None:
                obs = obs.replace(tzinfo=timezone.utc)

            age_days = max(0, (current_time - obs).days)
            recency = max(0.3, 1.0 - (age_days * 0.01))
            effective_w = base_w * recency
            weighted_scores.append(float(score) * effective_w)
            total_weight += effective_w

        mastery = round(sum(weighted_scores) / total_weight, 2) if total_weight > 0 else None
        confidence = round(min(0.95, len(evidence_sequence) / 5), 2)
        uncertainty = round(max(0.0, 1.0 - confidence), 2)

        # Check conflicting evidence
        knowledge = by_type.get("KNOWLEDGE_ASSESSMENT", [])
        application = by_type.get("APPLICATION_SCENARIO", []) + by_type.get("PRACTICAL_TASK", [])
        is_conflicting = bool(knowledge and application and max(knowledge) >= 0.95 and min(application) < 0.70)

        if mastery is None:
            status = "UNASSESSED"
        elif is_conflicting:
            status = "CONFLICTING_EVIDENCE"
        elif mastery >= 0.70 and confidence >= 0.60:
            status = "verified"
        else:
            status = "developing"

        return CompetencyEstimateResult(
            mastery=mastery,
            confidence=confidence,
            uncertainty=uncertainty,
            status=status,
            model_name="DeterministicBaseline",
            metadata={"evidence_count": len(evidence_sequence), "types": list(by_type.keys())},
        )


class BKTEstimator(CompetencyEstimator):
    """
    Bayesian Knowledge Tracing candidate model.
    Traces latent binary knowledge probability P(L_t) across sequential responses.
    """

    def __init__(
        self,
        p_init: float = 0.20,
        p_learn: float = 0.15,
        p_guess: float = 0.20,
        p_slip: float = 0.10,
    ) -> None:
        self.bkt = BKTModel(p_init=p_init, p_learn=p_learn, p_guess=p_guess, p_slip=p_slip)

    def estimate(
        self,
        evidence_sequence: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> CompetencyEstimateResult:
        binary_responses = []
        for ev in evidence_sequence:
            score = ev.get("score")
            if score is not None:
                binary_responses.append(bool(score >= 0.5))

        if not binary_responses:
            return CompetencyEstimateResult(
                mastery=None,
                confidence=0.0,
                uncertainty=1.0,
                status="UNASSESSED",
                model_name="BKT",
                metadata={"p_known": self.bkt.p_init},
            )

        trajectory = self.bkt.trace_responses(binary_responses)
        final_p = trajectory[-1]
        confidence = round(min(0.95, len(binary_responses) / 6), 2)
        uncertainty = round(max(0.0, 1.0 - confidence), 2)
        status = "verified" if final_p >= 0.80 and confidence >= 0.60 else "developing"

        return CompetencyEstimateResult(
            mastery=round(final_p, 2),
            confidence=confidence,
            uncertainty=uncertainty,
            status=status,
            model_name="BKT",
            metadata={"trajectory_length": len(trajectory), "final_p_known": final_p},
        )


class IRTEstimator(CompetencyEstimator):
    """
    Two-Parameter Logistic Item Response Theory candidate model.
    Estimates learner latent trait theta via maximum likelihood and Fisher information.
    """

    def __init__(self, default_discrimination: float = 1.0) -> None:
        self.default_discrimination = default_discrimination

    def estimate(
        self,
        evidence_sequence: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> CompetencyEstimateResult:
        items: list[tuple[float, float, int]] = []  # (a, b, response)
        for ev in evidence_sequence:
            score = ev.get("score")
            if score is None:
                continue
            resp = 1 if float(score) >= 0.5 else 0
            diff_str = str(ev.get("difficulty", "medium")).lower()
            diff_val = -1.0 if diff_str == "easy" else (1.0 if diff_str == "hard" else 0.0)
            disc = float(ev.get("discrimination", self.default_discrimination))
            items.append((disc, diff_val, resp))

        if not items:
            return CompetencyEstimateResult(
                mastery=None,
                confidence=0.0,
                uncertainty=1.0,
                status="UNASSESSED",
                model_name="IRT-2PL",
                metadata={"theta": 0.0},
            )

        # Numerical search for theta in [-3.0, 3.0]
        best_theta = 0.0
        best_ll = -1e9
        for step in range(-30, 31):
            theta = step * 0.1
            ll = 0.0
            for a, b, y in items:
                model = IRT2PL(discrimination=a, difficulty=b)
                p = model.probability(theta)
                p = max(1e-6, min(1.0 - 1e-6, p))
                ll += y * math.log(p) + (1 - y) * math.log(1 - p)
            if ll > best_ll:
                best_ll = ll
                best_theta = theta

        # Calculate Fisher information at best_theta
        total_info = 0.0
        for a, b, _ in items:
            model = IRT2PL(discrimination=a, difficulty=b)
            total_info += model.information(best_theta)

        # Map theta to [0, 1] mastery probability via sigmoid
        mastery = round(1.0 / (1.0 + math.exp(-best_theta)), 2)
        # Standard error SE(theta) = 1 / sqrt(total_info)
        se = 1.0 / math.sqrt(max(0.1, total_info))
        confidence = round(min(0.95, max(0.1, 1.0 - (se / 3.0))), 2)
        uncertainty = round(max(0.0, 1.0 - confidence), 2)
        status = "verified" if mastery >= 0.70 and confidence >= 0.60 else "developing"

        return CompetencyEstimateResult(
            mastery=mastery,
            confidence=confidence,
            uncertainty=uncertainty,
            status=status,
            model_name="IRT-2PL",
            metadata={"theta": round(best_theta, 2), "fisher_info": round(total_info, 2), "se": round(se, 2)},
        )
