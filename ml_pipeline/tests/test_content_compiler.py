from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.content_compiler import (
    compile_content_to_assessments,
    ContentCompilerResult,
)


@pytest.fixture
def sample_text():
    return (
        "Stratified sampling divides a target population into homogeneous subgroups "
        "called strata before drawing random samples independently within each stratum."
    )


def test_content_compiler_empty_source_raises():
    with pytest.raises(ValueError, match="No extractable textual content"):
        compile_content_to_assessments("   ")


@patch("ml_pipeline.content_compiler.extract_concepts")
@patch("ml_pipeline.content_compiler.map_competencies")
@patch("ml_pipeline.content_compiler.generate_mcqs")
@patch("ml_pipeline.content_compiler.validate_mcqs")
@patch("ml_pipeline.content_compiler.score_mcq_quality")
def test_content_compiler_e2e_pipeline(
    mock_score,
    mock_validate,
    mock_generate,
    mock_map,
    mock_extract,
    sample_text,
):
    mock_extract.return_value = ["Stratified sampling", "Strata"]
    mock_map.return_value = [
        {
            "competency": "Survey Sampling",
            "subskills": ["Stratified Sampling"],
            "confidence": 0.95,
        }
    ]
    mock_mcq = {
        "question": "What is stratified sampling?",
        "options": ["A method of sampling", "A census", "An index", "A mean"],
        "correct_answer": "A",
        "explanation": "Divides into strata.",
    }
    mock_generate.return_value = [mock_mcq]
    mock_validate.return_value = [{"valid": True, "issues": []}]
    mock_score.return_value = {
        **mock_mcq,
        "quality_score": 0.88,
        "cognitive_level": "Recall",
    }

    result = compile_content_to_assessments(sample_text, num_questions_per_competency=1)

    assert isinstance(result, ContentCompilerResult)
    assert len(result.concepts) == 2
    assert len(result.competency_mappings) == 1
    assert len(result.generated_mcqs) == 1
    assert len(result.valid_mcqs) == 1
    assert len(result.quality_scored_mcqs) == 1
    assert result.quality_scored_mcqs[0]["quality_score"] == 0.88
    assert result.rejection_count == 0


@patch("ml_pipeline.content_compiler.extract_concepts")
@patch("ml_pipeline.content_compiler.map_competencies")
@patch("ml_pipeline.content_compiler.generate_mcqs")
@patch("ml_pipeline.content_compiler.validate_mcqs")
@patch("ml_pipeline.content_compiler.score_mcq_quality")
def test_content_compiler_rejects_bad_mcqs(
    mock_score,
    mock_validate,
    mock_generate,
    mock_map,
    mock_extract,
    sample_text,
):
    mock_extract.return_value = ["Sampling"]
    mock_map.return_value = [{"competency": "Survey Sampling", "subskills": ["Sampling"], "confidence": 0.9}]
    bad_mcq = {"question": "Bad question", "options": ["A", "B"], "correct_answer": "A"}
    mock_generate.return_value = [bad_mcq]
    mock_validate.return_value = [{"valid": False, "issues": ["Only 2 options"]}]

    result = compile_content_to_assessments(sample_text)

    assert len(result.valid_mcqs) == 0
    assert len(result.quality_scored_mcqs) == 0
    assert result.rejection_count == 1


@patch("ml_pipeline.content_compiler.extract_concepts")
def test_content_compiler_no_concepts_returns_clean_empty(mock_extract, sample_text):
    mock_extract.return_value = []
    result = compile_content_to_assessments(sample_text)
    assert len(result.concepts) == 0
    assert len(result.quality_scored_mcqs) == 0
