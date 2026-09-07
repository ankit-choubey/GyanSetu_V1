"""
Unit tests for ml_pipeline/misconception_classifier.py
"""
import json
from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.misconception_classifier import (
    DEFAULT_FALLBACK_TYPE,
    LLMMisconceptionClassifier,
    MisconceptionClassificationResult,
    VALID_MISCONCEPTION_TYPES,
    classify_misconception,
    parse_classification_response,
)


def test_parse_classification_valid_json():
    raw = json.dumps({
        "misconception_type": "formula_misapplication",
        "description": "Learner used sample size instead of population size in denominator.",
        "remediation_focus": "Finite Population Correction Factor",
        "confidence": 0.88,
    })
    res = parse_classification_response(raw)
    assert isinstance(res, MisconceptionClassificationResult)
    assert res.misconception_type == "formula_misapplication"
    assert "denominator" in res.description
    assert res.remediation_focus == "Finite Population Correction Factor"
    assert res.confidence == 0.88


def test_parse_classification_with_markdown_fences():
    raw = """```json
    {
        "misconception_type": "conceptual_confusion",
        "description": "Confused stratified sampling with cluster sampling.",
        "remediation_focus": "Stratification vs Clustering",
        "confidence": 0.92
    }
    ```"""
    res = parse_classification_response(raw)
    assert res.misconception_type == "conceptual_confusion"
    assert res.confidence == 0.92


def test_parse_classification_unknown_type_defaults_to_conceptual():
    raw = json.dumps({
        "misconception_type": "random_unseen_type",
        "description": "Unknown issue.",
        "confidence": 0.6,
    })
    res = parse_classification_response(raw)
    assert res.misconception_type == "conceptual_confusion"


def test_parse_classification_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_classification_response("Not a JSON string at all")


def test_classify_misconception_fallback_when_no_api_key():
    with patch("ml_pipeline.misconception_classifier.GROQ_API_KEY", None):
        res = classify_misconception(
            question_text="What is standard error?",
            correct_answer="Standard deviation of sampling distribution",
            selected_answer="Standard deviation of population",
        )
        assert res.misconception_type == DEFAULT_FALLBACK_TYPE


def test_classify_misconception_with_mocked_groq():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "misconception_type": "terminology_confusion",
        "description": "Confused CPI-Rural with CPI-Urban index baskets.",
        "remediation_focus": "Consumer Price Index Series",
        "confidence": 0.85,
    })
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    with patch("ml_pipeline.misconception_classifier.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.misconception_classifier._get_client", return_value=mock_client):
        res = classify_misconception(
            question_text="Which index reflects rural consumption?",
            correct_answer="CPI-Rural",
            selected_answer="CPI-Urban",
            options={"A": "CPI-Urban", "B": "CPI-Rural"},
            explanation="CPI-Rural is specifically computed for rural households.",
        )
        assert res.misconception_type == "terminology_confusion"
        assert res.confidence == 0.85
        assert "CPI-Rural" in res.description


def test_llm_classifier_protocol_compatibility():
    classifier = LLMMisconceptionClassifier()

    # Mock AssessmentResponse with AssessmentItem
    mock_item = MagicMock()
    mock_item.question_text = "What is the primary formula for Laspeyres price index?"
    mock_item.correct_option = "A"
    mock_item.options_json = json.dumps({
        "A": "Base period weighted",
        "B": "Current period weighted",
    })

    mock_response = MagicMock()
    mock_response.assessment_item = mock_item
    mock_response.assessment_item_id = 42
    mock_response.selected_option = "B"
    mock_response.is_correct = False

    # Mock classifier output
    with patch("ml_pipeline.misconception_classifier.classify_misconception") as mock_classify:
        mock_classify.return_value = MisconceptionClassificationResult(
            misconception_type="formula_misapplication",
            description="Learner chose Paasche index instead of Laspeyres index weighting.",
            confidence=0.9,
        )
        result = classifier.classify(mock_response)
        assert result.misconception_type == "formula_misapplication"
        assert "Laspeyres" in result.description


def test_llm_classifier_graceful_fallback_on_exception():
    classifier = LLMMisconceptionClassifier(fallback_on_error=True)
    mock_response = MagicMock()
    mock_response.assessment_item = None
    mock_response.selected_option = "C"

    with patch("ml_pipeline.misconception_classifier.classify_misconception", side_effect=RuntimeError("Groq timeout")):
        result = classifier.classify(mock_response)
        # Should return fallback without raising
        assert result is not None
