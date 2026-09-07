"""
Bayesian Knowledge Tracing (BKT) Model
GyanSetu - Phase 3.1
"""

from typing import List


class BKTModel:
    """
    Standard Bayesian Knowledge Tracing model.
    Tracks latent knowledge probability P(L_t) across learning opportunities.
    """

    def __init__(
        self,
        p_init: float = 0.20,
        p_learn: float = 0.15,
        p_guess: float = 0.20,
        p_slip: float = 0.10,
    ):
        for param_name, param_val in [
            ("p_init", p_init),
            ("p_learn", p_learn),
            ("p_guess", p_guess),
            ("p_slip", p_slip),
        ]:
            if isinstance(param_val, bool) or not isinstance(param_val, (int, float)):
                raise TypeError(f"{param_name} must be a float or int, got {type(param_val).__name__}")
            if not (0.0 <= param_val <= 1.0):
                raise ValueError(f"{param_name} must be between 0.0 and 1.0, got {param_val}")

        self.p_init = float(p_init)
        self.p_learn = float(p_learn)
        self.p_guess = float(p_guess)
        self.p_slip = float(p_slip)

    def initialize_knowledge(self) -> float:
        """Returns the initial knowledge probability P(L_0)."""
        return self.p_init

    def predict_response_probability(self, p_known: float) -> float:
        """
        P(correct) = P(known) * (1 - p_slip) + (1 - P(known)) * p_guess
        """
        if isinstance(p_known, bool) or not isinstance(p_known, (int, float)):
            raise TypeError("p_known must be a float or int")
        if not (0.0 <= p_known <= 1.0):
            raise ValueError("p_known must be between 0.0 and 1.0")

        p_known_float = float(p_known)
        return p_known_float * (1.0 - self.p_slip) + (1.0 - p_known_float) * self.p_guess

    def update_after_response(self, p_known: float, correct: bool) -> float:
        """
        Updates P(known) given a response accuracy using standard BKT update equations.
        1. Posterior step:
           If correct: P(L|C) = P(L)*(1 - p_slip) / P(C)
           If incorrect: P(L|~C) = P(L)*p_slip / (1 - P(C))
        2. Transition step:
           P(L_t) = P(L|resp) + (1 - P(L|resp)) * p_learn
        """
        if isinstance(p_known, bool) or not isinstance(p_known, (int, float)):
            raise TypeError("p_known must be a float or int")
        if not (0.0 <= p_known <= 1.0):
            raise ValueError("p_known must be between 0.0 and 1.0")
        if type(correct) is not bool:
            raise TypeError(f"correct must be of type bool, got {type(correct).__name__}")

        p_k = float(p_known)
        p_correct = self.predict_response_probability(p_k)

        if correct:
            if p_correct <= 1e-12:
                p_posterior = 0.0
            else:
                p_posterior = (p_k * (1.0 - self.p_slip)) / p_correct
        else:
            p_incorrect = 1.0 - p_correct
            if p_incorrect <= 1e-12:
                p_posterior = 0.0
            else:
                p_posterior = (p_k * self.p_slip) / p_incorrect

        p_posterior = max(0.0, min(1.0, p_posterior))
        p_updated = p_posterior + (1.0 - p_posterior) * self.p_learn
        return max(0.0, min(1.0, p_updated))

    def trace_responses(self, responses: List[bool]) -> List[float]:
        """
        Traces a sequence of responses and returns the knowledge trajectory.
        """
        current_k = self.initialize_knowledge()
        trajectory = []
        for resp in responses:
            current_k = self.update_after_response(current_k, resp)
            trajectory.append(current_k)
        return trajectory
