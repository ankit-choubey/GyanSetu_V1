from __future__ import annotations

from ml_pipeline import scenario_evaluator


def evaluate_scenario_response(
    scenario: dict,
    task: dict,
    expected_reasoning: dict,
    rubric: dict,
    learner_response: str,
) -> dict:
    """Evaluate a prepared scenario response through the ML boundary."""
    return scenario_evaluator.evaluate_scenario(
        scenario,
        task,
        expected_reasoning,
        rubric,
        learner_response,
    )