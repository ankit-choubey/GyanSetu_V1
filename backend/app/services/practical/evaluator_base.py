from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    score: float
    passed: bool
    feedback: str
    dimension_scores: dict[str, float] = field(default_factory=dict)
    evaluator_type: str = "DETERMINISTIC"
    evaluator_version: str = "v1.0"
    status: str = "EVALUATED"  # EVALUATED, REVIEW_REQUIRED, REJECTED
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "passed": self.passed,
            "feedback": self.feedback,
            "dimension_scores": {k: round(v, 4) for k, v in self.dimension_scores.items()},
            "evaluator_type": self.evaluator_type,
            "evaluator_version": self.evaluator_version,
            "status": self.status,
            "metadata": self.metadata,
        }


class PracticalEvaluator(ABC):
    @abstractmethod
    def evaluate(self, task: Any, submission: dict[str, Any]) -> EvaluationResult:
        """Evaluate learner submission against the practical task rubric."""
        pass
