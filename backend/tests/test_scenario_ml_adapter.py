import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.services.scenario_ml_adapter import evaluate_scenario_response


def evaluation_result():
    return {
        "evaluation": {
            "score": 8,
            "max_score": 10,
            "percentage": 80,
            "criterion_results": [
                {
                    "criterion_id": "C1",
                    "score": 4,
                    "max_score": 4,
                    "result": "met",
                    "feedback": "The method was correctly identified.",
                },
                {
                    "criterion_id": "C2",
                    "score": 4,
                    "max_score": 6,
                    "result": "partially_met",
                    "feedback": "The justification was incomplete.",
                },
            ],
            "overall_result": "partially_correct",
        },
        "feedback": {
            "summary": "Most required reasoning was demonstrated.",
            "strengths": ["Correct method selection."],
            "areas_for_improvement": ["Expand the justification."],
            "recommended_next_step": "Review the supporting rationale.",
        },
        "evidence": {
            "demonstrated_competency": True,
            "evidence_type": "scenario_assessment",
            "confidence": 0.8,
        },
    }


def test_adapter_passes_exact_inputs_and_returns_result_unchanged():
    scenario = {"title": "Stored scenario", "context": "Stored context"}
    task = {"question": "Choose and justify.", "response_type": "structured_text"}
    expected_reasoning = {"key_points": ["Use the stored concept"]}
    rubric = {"criteria": [{"criterion_id": "C1", "max_score": 10}]}
    learner_response = "The learner's response"
    result = evaluation_result()

    with patch(
        "ml_pipeline.scenario_evaluator.evaluate_scenario",
        return_value=result,
    ) as evaluator:
        returned = evaluate_scenario_response(
            scenario,
            task,
            expected_reasoning,
            rubric,
            learner_response,
        )

    evaluator.assert_called_once_with(
        scenario,
        task,
        expected_reasoning,
        rubric,
        learner_response,
    )
    assert returned is result
    assert returned["evidence"]["evidence_type"] == "scenario_assessment"


def test_adapter_does_not_require_database():
    with patch(
        "ml_pipeline.scenario_evaluator.evaluate_scenario",
        return_value=evaluation_result(),
    ):
        result = evaluate_scenario_response(
            {"title": "Scenario"},
            {"question": "Question"},
            {"key_points": ["Point"]},
            {"criteria": []},
            "Response",
        )

    assert result["evaluation"]["score"] == 8


def test_adapter_propagates_evaluator_exception():
    failure = RuntimeError("ML evaluator failed")

    with patch(
        "ml_pipeline.scenario_evaluator.evaluate_scenario",
        side_effect=failure,
    ):
        with pytest.raises(RuntimeError, match="ML evaluator failed"):
            evaluate_scenario_response(
                {},
                {},
                {},
                {},
                "Response",
            )