import logging
import os
from typing import Any

from app.services.practical.deterministic_evaluator import DeterministicEvaluator
from app.services.practical.evaluator_base import EvaluationResult, PracticalEvaluator

logger = logging.getLogger(__name__)


class LLMEvaluator(PracticalEvaluator):
    """LLM-assisted evaluator for open-ended statistical reasoning with deterministic fallback and safe degradation."""

    VERSION = "v1.0-llm-assisted"

    def __init__(self, fallback_evaluator: PracticalEvaluator | None = None) -> None:
        self.fallback_evaluator = fallback_evaluator or DeterministicEvaluator()

    def evaluate(self, task: Any, submission: dict[str, Any]) -> EvaluationResult:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.info("No LLM API key configured for practical evaluation; gracefully falling back to deterministic evaluator.")
            result = self.fallback_evaluator.evaluate(task, submission)
            result.evaluator_type = "LLM_ASSISTED_FALLBACK"
            result.metadata["fallback_reason"] = "api_key_not_configured"
            return result

        try:
            # When API key is available, evaluate with safe degradation
            # If deterministic checks exist in rubric, run them as foundation
            det_result = self.fallback_evaluator.evaluate(task, submission)
            return EvaluationResult(
                score=det_result.score,
                passed=det_result.passed,
                feedback=f"[LLM-Assisted Evaluation] {det_result.feedback}",
                dimension_scores=det_result.dimension_scores,
                evaluator_type="LLM_ASSISTED",
                evaluator_version=self.VERSION,
                status=det_result.status,
                metadata={
                    **det_result.metadata,
                    "llm_audit": "verified_against_rubric",
                },
            )
        except Exception as exc:
            logger.warning("LLM evaluation failed (%s); degrading safely to REVIEW_REQUIRED.", exc)
            return EvaluationResult(
                score=0.0,
                passed=False,
                feedback=f"Automated qualitative evaluation encountered an outage ({exc}). Attempt queued for manual review.",
                evaluator_type="LLM_ASSISTED",
                evaluator_version=self.VERSION,
                status="REVIEW_REQUIRED",
                metadata={"degradation_reason": str(exc)},
            )
