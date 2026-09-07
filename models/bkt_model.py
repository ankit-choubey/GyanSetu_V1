"""
Bayesian Knowledge Tracing (BKT) Model
GyanSetu - Phase 3.1
"""

from __future__ import annotations

from typing import List, Sequence


class BKTModel:
    """Standard 4-parameter Bayesian Knowledge Tracing model."""

    def __init__(
        self,
        p_init: float = 0.20,
        p_learn: float = 0.15,
        p_guess: float = 0.20,
        p_slip: float = 0.10,
    ) -> None:
        for name, val in [
            ("p_init", p_init),
            ("p_learn", p_learn),
            ("p_guess", p_guess),
            ("p_slip", p_slip),
        ]:
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be a float or int, got {type(val).__name__}")
            if not (0.0 <= float(val) <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

        self.p_init = float(p_init)
        self.p_learn = float(p_learn)
        self.p_guess = float(p_guess)
        self.p_slip = float(p_slip)

    def initialize_knowledge(self) -> float:
        """Return initial probability of knowing the skill."""
        return self.p_init

    def predict_response_probability(self, p_known: float) -> float:
        """P(Correct) = P(Known) * (1 - P(Slip)) + (1 - P(Known)) * P(Guess)"""
        if isinstance(p_known, bool) or not isinstance(p_known, (int, float)):
            raise TypeError("p_known must be numeric")
        p = float(p_known)
        return p * (1.0 - self.p_slip) + (1.0 - p) * self.p_guess

    def update_after_response(self, p_known: float, correct: bool) -> float:
        """Update P(Known) given observed response correctness."""
        if not isinstance(correct, bool):
            raise TypeError("correct must be a boolean")
        if isinstance(p_known, bool) or not isinstance(p_known, (int, float)):
            raise TypeError("p_known must be numeric")

        p = max(0.0, min(1.0, float(p_known)))

        # Posterior calculation: P(L_t | observation)
        if correct:
            p_obs = self.predict_response_probability(p)
            p_posterior = (p * (1.0 - self.p_slip)) / p_obs if p_obs > 0 else p
        else:
            p_obs = 1.0 - self.predict_response_probability(p)
            p_posterior = (p * self.p_slip) / p_obs if p_obs > 0 else p

        # Learning transition: P(L_{t+1}) = P(L_t|obs) + (1 - P(L_t|obs)) * P(Learn)
        p_next = p_posterior + (1.0 - p_posterior) * self.p_learn
        return max(0.0, min(1.0, p_next))

    def trace_responses(self, responses: Sequence[bool]) -> List[float]:
        """Compute knowledge probabilities after a sequence of responses."""
        knowledge = self.initialize_knowledge()
        trajectory: List[float] = []
        for r in responses:
            knowledge = self.update_after_response(knowledge, r)
            trajectory.append(knowledge)
        return trajectory
