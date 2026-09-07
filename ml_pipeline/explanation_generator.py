"""
ml_pipeline/explanation_generator.py — Pedagogical Assessment Feedback Engine.

Generates targeted learning explanations when an officer submits an assessment response:
- Highlights the exact misconception in the chosen distractor using Groq LLM.
- Provides why-wrong and why-right cognitive breakdowns.
- Points directly to verified source text for remediation.
- Seamlessly falls back to deterministic template feedback when offline or unconfigured.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from openai import OpenAI

from ml_pipeline.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_FAST,
)

LETTERS = ["A", "B", "C", "D"]

_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "feedback_prompt.txt",
)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Creates or returns singleton OpenAI client for Groq."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=GROQ_API_KEY or "dummy-key",
            base_url=GROQ_BASE_URL,
        )
    return _client


def _strip_code_fences(raw: str) -> str:
    """Strips markdown json fences from LLM responses."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _generate_template_feedback(
    mcq: dict[str, Any],
    selected_letter: str,
    source_context: str | None = None,
) -> dict[str, Any]:
    """Deterministic template fallback feedback."""
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
        why_wrong = None
        why_right = base_explanation
        misconception_hint = None
        remediation_steps = [action]
    else:
        feedback_text = (
            f"Incorrect. You selected ({selected_letter}): '{selected_text}', but the correct answer is "
            f"({correct_letter}): '{correct_text}'. {base_explanation}"
        )
        gap = subskill
        action = f"Review training material on '{subskill}' before attempting reassessment."
        why_wrong = f"Selection ({selected_letter}) does not satisfy the requirements for '{subskill}'."
        why_right = f"Option ({correct_letter}) accurately represents '{subskill}'."
        misconception_hint = f"Review the fundamental definition and operational rules for {subskill}."
        remediation_steps = [action]

    return {
        "is_correct": is_correct,
        "selected_letter": selected_letter,
        "correct_letter": correct_letter,
        "feedback": feedback_text,
        "subskill_gap": gap,
        "recommended_action": action,
        "why_wrong": why_wrong,
        "why_right": why_right,
        "misconception_hint": misconception_hint,
        "remediation_steps": remediation_steps,
        "source_citation": source_context,
    }


def _generate_llm_feedback(
    mcq: dict[str, Any],
    selected_letter: str,
    source_context: str | None = None,
) -> dict[str, Any]:
    """Generates personalized pedagogical feedback using Groq LLM."""
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
    question_text = mcq.get("question", "")

    if is_correct:
        return _generate_template_feedback(mcq, selected_letter, source_context)

    # Format options for prompt
    options_lines = []
    for idx, opt in enumerate(options):
        letter = LETTERS[idx] if idx < len(LETTERS) else str(idx + 1)
        options_lines.append(f"({letter}) {opt}")
    options_str = "\n".join(options_lines)

    if not os.path.exists(_PROMPT_PATH):
        return _generate_template_feedback(mcq, selected_letter, source_context)

    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        question_text=question_text,
        options_text=options_str,
        correct_letter=correct_letter,
        correct_text=correct_text,
        selected_letter=selected_letter,
        selected_text=selected_text,
        subskill=subskill,
        base_explanation=base_explanation,
        source_context=source_context or "Not provided.",
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
    )
    content = response.choices[0].message.content or ""
    cleaned = _strip_code_fences(content)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"Invalid JSON feedback from LLM: {cleaned[:150]}")

    why_wrong = str(data.get("why_wrong", "")).strip()
    why_right = str(data.get("why_right", "")).strip()
    misconception_hint = str(data.get("misconception_hint", "")).strip()
    remediation_steps = data.get("remediation_steps", [])
    if isinstance(remediation_steps, str):
        remediation_steps = [remediation_steps]
    synth_fb = str(data.get("synthesized_feedback", "")).strip()

    feedback_text = (
        f"Incorrect. You selected ({selected_letter}): '{selected_text}'. "
        f"{synth_fb or why_wrong} "
        f"The correct answer is ({correct_letter}): '{correct_text}'. {base_explanation}"
    )

    primary_action = (
        remediation_steps[0]
        if remediation_steps
        else f"Review training material on '{subskill}' before attempting reassessment."
    )

    return {
        "is_correct": False,
        "selected_letter": selected_letter,
        "correct_letter": correct_letter,
        "feedback": feedback_text,
        "subskill_gap": subskill,
        "recommended_action": primary_action,
        "why_wrong": why_wrong,
        "why_right": why_right,
        "misconception_hint": misconception_hint,
        "remediation_steps": remediation_steps,
        "source_citation": source_context,
    }


def generate_feedback(
    mcq: dict[str, Any],
    selected_letter: str,
    source_context: str | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    """
    Generates tailored pedagogical feedback for an answered MCQ.

    Args:
        mcq: Dictionary representing the MCQ.
        selected_letter: The officer's chosen option letter ('A', 'B', 'C', 'D').
        source_context: Optional source text excerpt for deep citation.
        use_llm: If True, uses Groq LLM for deep cognitive remediation with template fallback.

    Returns:
        Structured feedback dictionary matching backend protocol contract.
    """
    if not use_llm or not GROQ_API_KEY:
        return _generate_template_feedback(mcq, selected_letter, source_context)

    try:
        return _generate_llm_feedback(mcq, selected_letter, source_context)
    except Exception:
        return _generate_template_feedback(mcq, selected_letter, source_context)
