import json
from unittest.mock import Mock, patch

import pytest

from ml_pipeline.scenario_evaluator import (
    evaluate_scenario,
    parse_evaluation_response,
)


def valid_evaluation():
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
                    "feedback": "The learner correctly identified the method.",
                },
                {
                    "criterion_id": "C2",
                    "score": 2,
                    "max_score": 3,
                    "result": "partially_met",
                    "feedback": "The explanation was incomplete.",
                },
                {
                    "criterion_id": "C3",
                    "score": 2,
                    "max_score": 3,
                    "result": "partially_met",
                    "feedback": "The justification was partly demonstrated.",
                },
            ],
            "overall_result": "partially_correct",
        },
        "feedback": {
            "summary": "The learner demonstrated most of the required reasoning.",
            "strengths": [
                "Correctly identified the method.",
            ],
            "areas_for_improvement": [
                "Provide a more complete justification.",
            ],
            "recommended_next_step": (
                "Review the reasoning behind the selected method."
            ),
        },
        "evidence": {
            "demonstrated_competency": True,
            "evidence_type": "scenario_assessment",
            "confidence": 0.86,
        },
    }


def test_valid_evaluation():
    result = parse_evaluation_response(
        json.dumps(valid_evaluation())
    )

    assert result["evaluation"]["score"] == 8
    assert result["evaluation"]["max_score"] == 10
    assert result["evaluation"]["percentage"] == 80
    assert result["evaluation"]["overall_result"] == "partially_correct"


def test_json_code_fence_is_accepted():
    raw = (
        "```json\n"
        + json.dumps(valid_evaluation())
        + "\n```"
    )

    result = parse_evaluation_response(raw)

    assert result["evaluation"]["score"] == 8


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_evaluation_response(
            '{"evaluation": invalid}'
        )


def test_non_object_is_rejected():
    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        parse_evaluation_response(
            json.dumps(["not", "an", "object"])
        )


def test_missing_top_level_field_is_rejected():
    data = valid_evaluation()
    del data["feedback"]

    with pytest.raises(
        ValueError,
        match="missing top-level field 'feedback'",
    ):
        parse_evaluation_response(json.dumps(data))


def test_wrong_evidence_type_is_rejected():
    data = valid_evaluation()
    data["evidence"]["evidence_type"] = "knowledge_assessment"

    with pytest.raises(
        ValueError,
        match="evidence_type",
    ):
        parse_evaluation_response(json.dumps(data))


def test_invalid_criterion_result_is_rejected():
    data = valid_evaluation()
    data["evaluation"]["criterion_results"][0]["result"] = "excellent"

    with pytest.raises(
        ValueError,
        match="invalid result",
    ):
        parse_evaluation_response(json.dumps(data))


def test_criterion_scores_must_sum_to_total_score():
    data = valid_evaluation()

    data["evaluation"]["criterion_results"][0]["score"] = 3

    with pytest.raises(
        ValueError,
        match="sum of criterion scores",
    ):
        parse_evaluation_response(json.dumps(data))


def test_criterion_score_cannot_exceed_max_score():
    data = valid_evaluation()

    data["evaluation"]["criterion_results"][0]["score"] = 5

    with pytest.raises(
        ValueError,
        match="cannot exceed max_score",
    ):
        parse_evaluation_response(json.dumps(data))


def test_score_must_be_between_zero_and_ten():
    data = valid_evaluation()
    data["evaluation"]["score"] = 11

    with pytest.raises(
        ValueError,
        match="between 0 and 10",
    ):
        parse_evaluation_response(json.dumps(data))


def test_invalid_overall_result_is_rejected():
    data = valid_evaluation()
    data["evaluation"]["overall_result"] = "maybe"

    with pytest.raises(
        ValueError,
        match="invalid value",
    ):
        parse_evaluation_response(json.dumps(data))


def test_confidence_must_be_between_zero_and_one():
    data = valid_evaluation()
    data["evidence"]["confidence"] = 1.5

    with pytest.raises(
        ValueError,
        match="confidence",
    ):
        parse_evaluation_response(json.dumps(data))


def test_score_cannot_be_negative():
    data = valid_evaluation()
    data["evaluation"]["score"] = -1

    with pytest.raises(ValueError, match="between 0 and 10"):
        parse_evaluation_response(json.dumps(data))


def test_invalid_max_score_is_rejected():
    data = valid_evaluation()
    data["evaluation"]["max_score"] = 9

    with pytest.raises(ValueError, match="max_score"):
        parse_evaluation_response(json.dumps(data))


def test_invalid_percentage_is_rejected():
    data = valid_evaluation()
    data["evaluation"]["percentage"] = 101

    with pytest.raises(ValueError, match="between 0 and 100"):
        parse_evaluation_response(json.dumps(data))


def test_inconsistent_percentage_is_rejected():
    data = valid_evaluation()
    data["evaluation"]["percentage"] = 79

    with pytest.raises(ValueError, match="score / max_score"):
        parse_evaluation_response(json.dumps(data))


def test_confidence_cannot_be_negative():
    data = valid_evaluation()
    data["evidence"]["confidence"] = -0.1

    with pytest.raises(ValueError, match="confidence"):
        parse_evaluation_response(json.dumps(data))


def test_demonstrated_competency_must_be_boolean():
    data = valid_evaluation()
    data["evidence"]["demonstrated_competency"] = "true"

    with pytest.raises(ValueError, match="demonstrated_competency"):
        parse_evaluation_response(json.dumps(data))


def test_evaluate_scenario_sends_exact_inputs_to_groq():
    scenario = {"title": "Exact scenario", "context": "Only supplied context"}
    task = {"question": "What should happen?", "response_type": "structured_text"}
    expected_reasoning = {"key_points": ["Use the supplied context"]}
    rubric = {
        "criteria": [
            {"criterion_id": "C1", "description": "Uses context", "max_score": 10}
        ],
        "max_score": 10,
    }
    learner_response = "The learner's exact response."
    create = Mock(
        return_value=Mock(
            choices=[Mock(message=Mock(content=json.dumps(valid_evaluation())))]
        )
    )
    fake_client = Mock()
    fake_client.chat.completions.create = create

    with patch("ml_pipeline.scenario_evaluator.GROQ_API_KEY", "test-key"), patch(
        "ml_pipeline.scenario_evaluator._get_client",
        return_value=fake_client,
    ):
        result = evaluate_scenario(
            scenario,
            task,
            expected_reasoning,
            rubric,
            learner_response,
        )

    sent_prompt = create.call_args.kwargs["messages"][0]["content"]
    assert result["evaluation"]["score"] == 8
    assert json.dumps(scenario, ensure_ascii=False) in sent_prompt
    assert json.dumps(task, ensure_ascii=False) in sent_prompt
    assert json.dumps(expected_reasoning, ensure_ascii=False) in sent_prompt
    assert json.dumps(rubric, ensure_ascii=False) in sent_prompt
    assert learner_response in sent_prompt