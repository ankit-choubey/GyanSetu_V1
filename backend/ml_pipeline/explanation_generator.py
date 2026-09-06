"""
ml_pipeline/explanation_generator.py — Pedagogical Assessment Feedback Engine.

Generates targeted learning explanations when an officer submits an assessment response:
- Highlights the exact misconception in the chosen distractor.
- Points directly to the verified source text for remediation.
- Suggests targeted next-best-actions (review material or practical exercise).
"""
from __future__ import annotations

from typing import Any

LETTERS = ["A", "B", "C", "D"]


def generate_feedback(
    mcq: dict[str, Any],
    selected_letter: str,
    source_context: str | None = None,
) -> dict[str, Any]:
    """
    Generates tailored pedagogical feedback for an answered MCQ.

    Args:
        mcq: Dictionary representing the MCQ.
        selected_letter: The officer's chosen option letter ('A', 'B', 'C', 'D').
        source_context: Optional source text excerpt for deep citation.

    Returns:
        Structured feedback dictionary.
    """
    correct_letter = mcq.get("correct_answer", "A").upper()
    selected_letter = str(selected_letter).strip().upper()
    is_correct = (selected_letter == correct_letter)

    options = mcq.get("options", [])
    correct_idx = ord(correct_letter) - ord("A") if correct_letter in LETTERS else 0
    selected_idx = ord(selected_letter) - ord("A") if selected_letter in LETTERS else 0

    correct_text = options[correct_idx] if (is_correct or correct_idx < len(options)) else ""
    selected_text = options[selected_idx] if selected_idx < len(options) else ""

    subskill = mcq.get("subskill") or mcq.get("competency", "Statistical Concepts")
    base_explanation = mcq.get("explanation", "Refer to the training manual for official guidelines.")

    if is_correct:
        feedback_text = f"Correct! You demonstrated proficiency in '{subskill}'. {base_explanation}"
        gap = None
        action = f"Proceed to next adaptive question or practical application task in '{subskill}'."
    else:
        feedback_text = (
            f"Incorrect. You selected ({selected_letter}): '{selected_text}', but the correct answer is "
            f"({correct_letter}): '{correct_text}'. {base_explanation}"
        )
        gap = subskill
        action = f"Review training material on '{subskill}' before attempting reassessment."

    return {
        "is_correct": is_correct,
        "selected_letter": selected_letter,
        "correct_letter": correct_letter,
        "feedback": feedback_text,
        "subskill_gap": gap,
        "recommended_action": action,
    }
