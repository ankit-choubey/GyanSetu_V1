import json
from unittest.mock import MagicMock, patch

import pytest

from ml_pipeline.scenario_generator import parse_scenario_response


def valid_scenario():
    return {
        "scenario": {
            "title": "Sampling Design Scenario",
            "context": (
                "A population is divided into homogeneous subgroups "
                "before sampling."
            ),
            "context_data": {},
            "task": {
                "question": (
                    "Explain how stratified sampling can be applied."
                ),
                "response_type": "structured_text",
                "instructions": "Justify your answer.",
            },
        },
        "expected_reasoning": {
            "key_points": [
                "Identify homogeneous subgroups.",
                "Apply sampling within the subgroups.",
            ],
            "reference_answer": (
                "The population is divided into homogeneous "
                "subgroups before sampling."
            ),
        },
        "rubric": {
            "criteria": [
                {
                    "criterion_id": "C1",
                    "description": "Identifies the sampling approach.",
                    "max_score": 4,
                },
                {
                    "criterion_id": "C2",
                    "description": "Explains subgroup formation.",
                    "max_score": 3,
                },
                {
                    "criterion_id": "C3",
                    "description": "Justifies the application.",
                    "max_score": 3,
                },
            ],
            "max_score": 10,
        },
        "difficulty": "medium",
        "cognitive_level": "application",
        "source": {
            "content_reference": "training material supplied to the model"
        },
    }


def test_valid_scenario():
    result = parse_scenario_response(
        json.dumps(valid_scenario()),
        difficulty="medium",
        cognitive_level="application",
    )

    assert result["difficulty"] == "medium"
    assert result["cognitive_level"] == "application"
    assert result["rubric"]["max_score"] == 10


def test_json_code_fence_is_accepted():
    raw = (
        "```json\n"
        + json.dumps(valid_scenario())
        + "\n```"
    )

    result = parse_scenario_response(
        raw,
        difficulty="medium",
        cognitive_level="application",
    )

    assert result["scenario"]["title"] == "Sampling Design Scenario"


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_scenario_response(
            '{"scenario": invalid}',
            difficulty="medium",
            cognitive_level="application",
        )


def test_non_object_is_rejected():
    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        parse_scenario_response(
            json.dumps(["not", "an", "object"]),
            difficulty="medium",
            cognitive_level="application",
        )


def test_missing_top_level_field_is_rejected():
    data = valid_scenario()
    del data["rubric"]

    with pytest.raises(
        ValueError,
        match="missing top-level field 'rubric'",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_wrong_response_type_is_rejected():
    data = valid_scenario()

    data["scenario"]["task"]["response_type"] = "multiple_choice"

    with pytest.raises(
        ValueError,
        match="response_type",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_wrong_difficulty_is_rejected():
    data = valid_scenario()

    data["difficulty"] = "hard"

    with pytest.raises(
        ValueError,
        match="does not match requested value",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_invalid_cognitive_level_is_rejected():
    data = valid_scenario()

    data["cognitive_level"] = "recall"

    with pytest.raises(
        ValueError,
        match="must be one of",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_wrong_rubric_total_is_rejected():
    data = valid_scenario()

    data["rubric"]["max_score"] = 9

    with pytest.raises(
        ValueError,
        match="max_score",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_too_few_rubric_criteria_are_rejected():
    data = valid_scenario()

    data["rubric"]["criteria"] = [
        {
            "criterion_id": "C1",
            "description": "Only one criterion.",
            "max_score": 10,
        }
    ]

    with pytest.raises(
        ValueError,
        match="between 2 and 4 criteria",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_missing_reference_answer_is_rejected():
    data = valid_scenario()

    del data["expected_reasoning"]["reference_answer"]

    with pytest.raises(
        ValueError,
        match="reference_answer",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


def test_invalid_empty_scenario_structure_is_rejected():
    data = valid_scenario()

    data["expected_reasoning"]["key_points"] = []

    with pytest.raises(
        ValueError,
        match="key_points",
    ):
        parse_scenario_response(
            json.dumps(data),
            difficulty="medium",
            cognitive_level="application",
        )


# -------------------------------------------------------------------
# Grounding integration tests
# -------------------------------------------------------------------


def test_generate_scenario_rejects_unsupported_grounding_claim():
    fake_response = MagicMock()

    fake_response.choices[0].message.content = json.dumps({
        "scenario": {
            "title": "Sampling Scenario",
            "context": (
                "The survey achieved a 95% response rate."
            ),
            "context_data": {},
            "task": {
                "question": (
                    "Explain how the sampling method should be selected."
                ),
                "response_type": "structured_text",
                "instructions": "Justify your answer.",
            },
        },
        "expected_reasoning": {
            "key_points": [
                "Identify the sampling method."
            ],
            "reference_answer": (
                "The sampling method should be selected "
                "using the supplied training material."
            ),
        },
        "rubric": {
            "criteria": [
                {
                    "criterion_id": "C1",
                    "description": "Identifies the method.",
                    "max_score": 4,
                },
                {
                    "criterion_id": "C2",
                    "description": "Explains the reasoning.",
                    "max_score": 3,
                },
                {
                    "criterion_id": "C3",
                    "description": "Justifies the decision.",
                    "max_score": 3,
                },
            ],
            "max_score": 10,
        },
        "difficulty": "medium",
        "cognitive_level": "application",
        "source": {
            "content_reference": "training material supplied to the model"
        },
    })

    mock_client = MagicMock()

    mock_client.chat.completions.create.return_value = (
        fake_response
    )

    with patch(
        "ml_pipeline.scenario_generator._get_client",
        return_value=mock_client,
    ):
        with patch(
            "ml_pipeline.scenario_generator.GROQ_API_KEY",
            "test-key",
        ):
            from ml_pipeline.scenario_generator import (
                generate_scenario,
            )

            with pytest.raises(
                ValueError,
                match="failed grounding validation",
            ):
                generate_scenario(
                    content=(
                        "Stratified sampling divides a population "
                        "into homogeneous subgroups before sampling."
                    ),
                    competency="Sampling Design",
                    subskill=(
                        "Select appropriate sampling methods"
                    ),
                    difficulty="medium",
                    cognitive_level="application",
                )


def test_generate_scenario_accepts_grounded_response():
    fake_response = MagicMock()

    fake_response.choices[0].message.content = json.dumps({
        "scenario": {
            "title": "Sampling Design Scenario",
            "context": (
                "Stratified sampling divides a population into "
                "homogeneous subgroups before sampling."
            ),
            "context_data": {},
            "task": {
                "question": (
                    "Explain how stratified sampling can be applied."
                ),
                "response_type": "structured_text",
                "instructions": "Justify your answer.",
            },
        },
        "expected_reasoning": {
            "key_points": [
                "Identify homogeneous subgroups.",
                "Apply sampling within the subgroups.",
            ],
            "reference_answer": (
                "The population is divided into homogeneous "
                "subgroups before sampling."
            ),
        },
        "rubric": {
            "criteria": [
                {
                    "criterion_id": "C1",
                    "description": "Identifies the sampling approach.",
                    "max_score": 4,
                },
                {
                    "criterion_id": "C2",
                    "description": "Explains subgroup formation.",
                    "max_score": 3,
                },
                {
                    "criterion_id": "C3",
                    "description": "Justifies the application.",
                    "max_score": 3,
                },
            ],
            "max_score": 10,
        },
        "difficulty": "medium",
        "cognitive_level": "application",
        "source": {
            "content_reference": "training material supplied to the model"
        },
    })

    mock_client = MagicMock()

    mock_client.chat.completions.create.return_value = (
        fake_response
    )

    with patch(
        "ml_pipeline.scenario_generator._get_client",
        return_value=mock_client,
    ):
        with patch(
            "ml_pipeline.scenario_generator.GROQ_API_KEY",
            "test-key",
        ):
            from ml_pipeline.scenario_generator import (
                generate_scenario,
            )

            result = generate_scenario(
                content=(
                    "Stratified sampling divides a population "
                    "into homogeneous subgroups before sampling."
                ),
                competency="Sampling Design",
                subskill=(
                    "Select appropriate sampling methods"
                ),
                difficulty="medium",
                cognitive_level="application",
            )

    assert result["difficulty"] == "medium"
    assert result["cognitive_level"] == "application"
    assert result["rubric"]["max_score"] == 10