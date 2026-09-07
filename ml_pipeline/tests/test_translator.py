"""
Unit tests for ml_pipeline/translator.py
"""
from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.translator import (
    SUPPORTED_LANGUAGES,
    StatisticalTranslator,
    translate,
    translate_mcq,
    translate_scenario,
)


def test_glossary_loading():
    translator = StatisticalTranslator()
    assert len(translator.glossary) > 0
    assert "Sampling Design" in translator.glossary
    guidance = translator.get_glossary_guidance("hi")
    assert "Sampling Design" in guidance
    assert "प्रतिचयन" in guidance


def test_supported_languages():
    assert "hi" in SUPPORTED_LANGUAGES
    assert "ta" in SUPPORTED_LANGUAGES
    assert "te" in SUPPORTED_LANGUAGES
    assert "bn" in SUPPORTED_LANGUAGES
    assert "mr" in SUPPORTED_LANGUAGES


def test_unsupported_language_raises():
    translator = StatisticalTranslator()
    with pytest.raises(ValueError, match="Unsupported target language"):
        translator.translate_text("Test sentence", target_language="klingon")


def test_same_language_returns_original():
    translator = StatisticalTranslator()
    assert translator.translate_text("Test statistical concept", target_language="en", source_language="en") == "Test statistical concept"


def test_empty_text_returns_empty():
    translator = StatisticalTranslator()
    assert translator.translate_text("") == ""
    assert translator.translate_text("   ") == "   "


def test_fallback_when_api_key_none():
    with patch("ml_pipeline.translator.GROQ_API_KEY", None):
        translator = StatisticalTranslator()
        res = translator.translate_text("Consumer Price Index calculation", target_language="hi")
        assert res == "Consumer Price Index calculation"


def test_translate_text_with_mocked_llm():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "प्रतिचयन अभिकल्प सांख्यिकीय सर्वेक्षण का एक मुख्य घटक है।"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    with patch("ml_pipeline.translator.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.translator._get_client", return_value=mock_client):
        translator = StatisticalTranslator()
        res = translator.translate_text("Sampling design is a core component of statistical surveys.", target_language="hi")
        assert "प्रतिचयन अभिकल्प" in res
        assert mock_client.chat.completions.create.called


def test_translate_mcq_structure_preserved():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "अनुवादित पाठ"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    mcq = {
        "item_id": "mcq_101",
        "question": "What is the primary formula for standard deviation?",
        "options": [
            "Square root of variance",
            "Variance squared",
            "Mean divided by standard error",
            "Sum of squared residuals",
        ],
        "correct_answer": "A",
        "explanation": "Standard deviation is defined as the square root of the variance.",
        "difficulty": "medium",
    }

    with patch("ml_pipeline.translator.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.translator._get_client", return_value=mock_client):
        translated = translate_mcq(mcq, target_language="hi")

        assert translated["item_id"] == "mcq_101"
        assert translated["correct_answer"] == "A"
        assert translated["difficulty"] == "medium"
        assert len(translated["options"]) == 4
        assert translated["target_language"] == "hi"


def test_translate_mcq_with_dict_options():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "विकल्प अनुवाद"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    mcq = {
        "question": "Choose the correct term.",
        "options": {"A": "Option A text", "B": "Option B text"},
        "correct_answer": "B",
    }

    with patch("ml_pipeline.translator.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.translator._get_client", return_value=mock_client):
        translated = translate_mcq(mcq, target_language="hi")
        assert "A" in translated["options"]
        assert "B" in translated["options"]
        assert translated["correct_answer"] == "B"


def test_translate_scenario_structure_preserved():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "परिदृश्य संदर्भ अनुवादित"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    scenario = {
        "title": "Industrial Production Index",
        "context": "The ministry is updating the base year weights.",
        "task_question": "Explain how substitution bias should be addressed.",
        "instructions": "Cite Laspeyres index methodology.",
        "rubric": {"max_score": 10, "criteria": []},
        "difficulty": "hard",
    }

    with patch("ml_pipeline.translator.GROQ_API_KEY", "mock-key"), \
         patch("ml_pipeline.translator._get_client", return_value=mock_client):
        res = translate_scenario(scenario, target_language="hi")
        assert res["rubric"] == scenario["rubric"]
        assert res["difficulty"] == "hard"
        assert res["target_language"] == "hi"
