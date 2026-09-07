"""
Unit tests for ml_pipeline/lab_task_generator.py
"""
import json
from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.lab_task_generator import (
    SUPPORTED_DIFFICULTIES,
    SUPPORTED_TASK_TYPES,
    generate_lab_task,
    parse_lab_task_response,
    validate_lab_task_shape,
)


@pytest.fixture
def valid_task_dict():
    return {
        "title": "Stratified Sampling Allocation Lab",
        "task_type": "sampling_exercise",
        "competency": "Sampling Design",
        "subskill": "Stratified Sampling",
        "difficulty": "medium",
        "context": "An NSSO team is designing the annual survey for informal sector enterprises across 4 states.",
        "dataset_description": {
            "name": "enterprise_strata_sizes.csv",
            "row_count": 400,
            "columns": [
                {"name": "state_code", "type": "string", "description": "State identifier"},
                {"name": "stratum_size", "type": "integer", "description": "Total registered units"},
                {"name": "stratum_variance", "type": "float", "description": "Prior survey variance"},
            ],
            "sample_rows": [
                {"state_code": "ST01", "stratum_size": 1200, "stratum_variance": 45.2}
            ],
        },
        "instructions": [
            "Calculate proportional allocation weights for each state stratum.",
            "Apply Neyman allocation assuming known stratum variances.",
            "Compare sample variances between simple random sampling and stratified sampling.",
        ],
        "deliverables": [
            "Table of sample allocation numbers (n_h) under both proportional and Neyman designs.",
            "One-page briefing note explaining efficiency gain.",
        ],
        "expected_outputs": {
            "calculations": {"total_n": 100, "neyman_gain_percent": 18.5},
            "key_interpretations": ["Neyman allocation yields lower variance for fixed sample size."],
        },
        "rubric": {
            "max_score": 20,
            "criteria": [
                {"criterion_id": "C1", "name": "Allocation Formula", "max_score": 10, "description": "Correct Neyman weights"},
                {"criterion_id": "C2", "name": "Variance Comparison", "max_score": 10, "description": "Accurate gain computation"},
            ],
        },
    }


def test_validate_lab_task_shape_valid(valid_task_dict):
    issues = validate_lab_task_shape(valid_task_dict)
    assert issues == []


def test_validate_lab_task_shape_missing_field(valid_task_dict):
    del valid_task_dict["rubric"]
    issues = validate_lab_task_shape(valid_task_dict)
    assert any("rubric" in iss for iss in issues)


def test_validate_lab_task_shape_invalid_task_type(valid_task_dict):
    valid_task_dict["task_type"] = "unsupported_type"
    issues = validate_lab_task_shape(valid_task_dict)
    assert any("task_type" in iss for iss in issues)


def test_validate_lab_task_shape_rubric_sum_mismatch(valid_task_dict):
    valid_task_dict["rubric"]["criteria"][0]["max_score"] = 5
    # Total criteria is 15, max_score is 20
    issues = validate_lab_task_shape(valid_task_dict)
    assert any("criteria max_score sum" in iss for iss in issues)


def test_parse_lab_task_response_with_fences(valid_task_dict):
    raw = f"```json\n{json.dumps(valid_task_dict)}\n```"
    parsed = parse_lab_task_response(raw)
    assert parsed["title"] == valid_task_dict["title"]
    assert parsed["task_type"] == "sampling_exercise"


def test_parse_lab_task_response_invalid_json_raises():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_lab_task_response("invalid non json string")


def test_generate_lab_task_with_mocked_llm(valid_task_dict):
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(valid_task_dict)
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    with patch("ml_pipeline.lab_task_generator.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.lab_task_generator._get_client", return_value=mock_client):
        task = generate_lab_task(
            content="Sample text on sampling allocation methodology.",
            competency="Sampling Design",
            subskill="Stratified Sampling",
            difficulty="medium",
            task_type="sampling_exercise",
            source_id="chapter_4_sampling.pdf",
        )
        assert task["title"] == valid_task_dict["title"]
        assert "task_id" in task
        assert task["source_metadata"]["source_id"] == "chapter_4_sampling.pdf"
        assert task["rubric"]["max_score"] == 20


def test_generate_lab_task_input_validation():
    with pytest.raises(ValueError, match="content must be a non-empty string"):
        generate_lab_task("", "Sampling Design", "Stratified Sampling")

    with pytest.raises(ValueError, match="Invalid difficulty"):
        generate_lab_task("Text", "Sampling", "Subskill", difficulty="impossible")

    with pytest.raises(ValueError, match="Invalid task_type"):
        generate_lab_task("Text", "Sampling", "Subskill", task_type="invalid_type")
