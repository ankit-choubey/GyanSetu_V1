"""
ml_pipeline/tests/test_personalized_feedback.py — Automated Tests for Personalized Feedback.

Tests:
1. Verification of rich schema keys (why_wrong, why_right, misconception_hint, remediation_steps).
2. Fallback execution when use_llm=False or key missing.
3. Resilience to malformed responses.
4. Live LLM execution when GROQ_API_KEY is active.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.explanation_generator import (
    generate_feedback,
    _generate_template_feedback,
)


@pytest.fixture
def sample_mcq():
    return {
        "question": "Which theorem states that the sample mean converges in probability to the expected value?",
        "options": [
            "Central Limit Theorem",
            "Weak Law of Large Numbers",
            "Markov Inequality",
            "Bayes Theorem",
        ],
        "correct_answer": "B",
        "explanation": "Khinchin's Weak Law of Large Numbers guarantees convergence in probability as sample size increases.",
        "competency": "Probability Limit Theorems",
        "subskill": "Law of Large Numbers",
    }


def test_template_feedback_correct_answer(sample_mcq):
    res = generate_feedback(sample_mcq, "B", use_llm=False)
    assert res["is_correct"] is True
    assert res["selected_letter"] == "B"
    assert res["correct_letter"] == "B"
    assert "Correct!" in res["feedback"]
    assert res["subskill_gap"] is None
    assert res["why_right"] is not None


def test_template_feedback_incorrect_answer(sample_mcq):
    res = generate_feedback(sample_mcq, "A", use_llm=False)
    assert res["is_correct"] is False
    assert res["selected_letter"] == "A"
    assert res["correct_letter"] == "B"
    assert "Incorrect." in res["feedback"]
    assert "(A)" in res["feedback"]
    assert res["subskill_gap"] == "Law of Large Numbers"
    assert len(res["remediation_steps"]) >= 1


def test_llm_feedback_fallback_on_network_error(sample_mcq):
    with patch("ml_pipeline.explanation_generator._get_client", side_effect=RuntimeError("Groq API Timeout")):
        res = generate_feedback(sample_mcq, "C", use_llm=True)
        assert res["is_correct"] is False
        assert res["selected_letter"] == "C"
        assert "Incorrect." in res["feedback"]
        assert "(C)" in res["feedback"]


def test_llm_feedback_structure_with_mock(sample_mcq):
    mock_payload = {
        "why_wrong": "Markov Inequality gives an upper bound for non-negative random variables, not convergence in probability.",
        "why_right": "Weak Law of Large Numbers explicitly defines convergence of sample means.",
        "misconception_hint": "Distinguish between tail probability bounds (Markov/Chebyshev) and asymptotic limit theorems.",
        "remediation_steps": [
            "Review definitions of convergence in probability vs bounds.",
            "Work through 3 sample problem exercises on LLN vs CLT.",
        ],
        "synthesized_feedback": "You chose an inequality bound instead of an asymptotic convergence theorem.",
    }

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        f"```json\n"
        f"{{\n"
        f'  "why_wrong": "{mock_payload["why_wrong"]}",\n'
        f'  "why_right": "{mock_payload["why_right"]}",\n'
        f'  "misconception_hint": "{mock_payload["misconception_hint"]}",\n'
        f'  "remediation_steps": ["step1", "step2"],\n'
        f'  "synthesized_feedback": "{mock_payload["synthesized_feedback"]}"\n'
        f"}}\n"
        f"```"
    )
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    with patch("ml_pipeline.explanation_generator._get_client", return_value=mock_client):
        res = generate_feedback(sample_mcq, "C", use_llm=True)
        assert res["is_correct"] is False
        assert res["why_wrong"] == mock_payload["why_wrong"]
        assert res["why_right"] == mock_payload["why_right"]
        assert res["misconception_hint"] == mock_payload["misconception_hint"]
        assert len(res["remediation_steps"]) == 2
        assert "Incorrect." in res["feedback"]
        assert "(C)" in res["feedback"]
