"""
ml_pipeline/misconception_classifier.py — LLM-based Misconception Classification Engine.
GyanSetu - Phase 4.2b

Diagnoses wrong-answer patterns in statistical assessments using Groq LLM.
Classifies errors into cognitive taxonomy types (conceptual_confusion, formula_misapplication,
procedural_error, terminology_confusion, calculation_error, interpretation_bias).
Provides seamless fallback to deterministic UNCLASSIFIED_WRONG_ANSWER_PATTERN when offline.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

from ml_pipeline.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_FAST,
)

_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "misconception_prompt.txt",
)

_client: Optional[OpenAI] = None

VALID_MISCONCEPTION_TYPES = {
    "conceptual_confusion",
    "formula_misapplication",
    "procedural_error",
    "terminology_confusion",
    "calculation_error",
    "interpretation_bias",
}

DEFAULT_FALLBACK_TYPE = "UNCLASSIFIED_WRONG_ANSWER_PATTERN"
DEFAULT_FALLBACK_DESCRIPTION = "Semantic classification unavailable; deterministic wrong-answer pattern only."


@dataclass(frozen=True)
class MisconceptionClassificationResult:
    """Standardized classification result matching backend Protocol contract."""
    misconception_type: str
    description: str
    remediation_focus: str = ""
    confidence: float = 0.5


def _get_client() -> OpenAI:
    """Create or return existing Groq client."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=GROQ_API_KEY or "dummy-key",
            base_url=GROQ_BASE_URL,
        )
    return _client


def _load_prompt_template() -> str:
    """Load the prompt template."""
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _strip_code_fences(raw: str) -> str:
    """Strip markdown backticks and whitespace."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
def parse_classification_response(raw_text: str) -> MisconceptionClassificationResult:
    """
    Parses and validates LLM response JSON into a MisconceptionClassificationResult.
    Performs safe validation and normalizes taxonomy types.
    """
    import re
    cleaned = _strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON from classifier: {exc}\nRaw: {cleaned[:200]!r}") from exc
        else:
            raise ValueError(f"Invalid JSON from classifier: {exc}\nRaw: {cleaned[:200]!r}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object, got {type(data).__name__}")

    raw_type = str(data.get("misconception_type", "")).strip().lower()
    description = str(data.get("description", "")).strip()
    remediation = str(data.get("remediation_focus", "")).strip()

    try:
        confidence = float(data.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5

    # Match or map to known taxonomy types
    m_type = raw_type if raw_type in VALID_MISCONCEPTION_TYPES else "conceptual_confusion"
    if not description:
        description = f"Learner displayed {m_type.replace('_', ' ')} on this item."

    return MisconceptionClassificationResult(
        misconception_type=m_type,
        description=description,
        remediation_focus=remediation,
        confidence=confidence,
    )


def classify_misconception(
    question_text: str,
    correct_answer: str,
    selected_answer: str,
    *,
    options: Union[Dict[str, Any], List[Any], str, None] = None,
    explanation: str = "",
    use_fallback_on_error: bool = True,
) -> MisconceptionClassificationResult:
    """
    Classifies an incorrect response using Groq LLM.

    Args:
        question_text: The assessment question text.
        correct_answer: The correct answer text or option.
        selected_answer: The learner's chosen wrong answer.
        options: Optional choices (dict, list, or JSON string).
        explanation: Optional reference explanation from item metadata.
        use_fallback_on_error: If True, returns safe fallback instead of raising.

    Returns:
        MisconceptionClassificationResult
    """
    if not question_text or not str(question_text).strip():
        if use_fallback_on_error:
            return MisconceptionClassificationResult(
                misconception_type=DEFAULT_FALLBACK_TYPE,
                description=DEFAULT_FALLBACK_DESCRIPTION,
            )
        raise ValueError("question_text must not be empty")

    if not GROQ_API_KEY:
        return MisconceptionClassificationResult(
            misconception_type=DEFAULT_FALLBACK_TYPE,
            description="LLM key not configured; using deterministic pattern.",
        )

    options_str = ""
    if isinstance(options, (dict, list)):
        options_str = json.dumps(options, ensure_ascii=False)
    elif isinstance(options, str):
        options_str = options

    prompt_template = _load_prompt_template()
    prompt = prompt_template.format(
        question_text=question_text,
        options_text=options_str or "Not specified",
        correct_answer=correct_answer or "Not specified",
        selected_answer=selected_answer or "Incorrect choice",
        explanation=explanation or "No explanation provided",
    )

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        content = response.choices[0].message.content or ""
        return parse_classification_response(content)
    except Exception as exc:
        if use_fallback_on_error:
            return MisconceptionClassificationResult(
                misconception_type=DEFAULT_FALLBACK_TYPE,
                description=f"Automated classification fallback: {str(exc)[:100]}",
                confidence=0.0,
            )
        raise


class LLMMisconceptionClassifier:
    """
    Adapter implementing the backend MisconceptionClassifier Protocol:
        def classify(self, response: AssessmentResponse) -> ClassifierResult
    """

    def __init__(self, fallback_on_error: bool = True):
        self.fallback_on_error = fallback_on_error

    def classify(self, response: Any) -> Any:
        """
        Extracts question and chosen distractor from response and returns a ClassifierResult.
        """
        # Read from assessment_item relationship if available
        item = getattr(response, "assessment_item", None)
        selected_option = getattr(response, "selected_option", "")

        question_text = getattr(item, "question_text", "") if item else ""
        correct_option = getattr(item, "correct_option", "") if item else ""
        options_json = getattr(item, "options_json", None) if item else None

        # Resolve selected text if possible
        options = None
        selected_text = selected_option
        correct_text = correct_option
        if options_json:
            try:
                opts = json.loads(options_json) if isinstance(options_json, str) else options_json
                options = opts
                if isinstance(opts, dict):
                    selected_text = f"Option {selected_option}: {opts.get(selected_option, selected_option)}"
                    correct_text = f"Option {correct_option}: {opts.get(correct_option, correct_option)}"
                elif isinstance(opts, list):
                    # Options is list of strings A, B, C, D
                    idx = ord(selected_option.upper()) - ord("A") if len(selected_option) == 1 else -1
                    if 0 <= idx < len(opts):
                        selected_text = f"Option {selected_option}: {opts[idx]}"
                    c_idx = ord(correct_option.upper()) - ord("A") if len(correct_option) == 1 else -1
                    if 0 <= c_idx < len(opts):
                        correct_text = f"Option {correct_option}: {opts[c_idx]}"
            except Exception:
                pass

        try:
            res = classify_misconception(
                question_text=question_text or f"Assessment item #{getattr(response, 'assessment_item_id', 'unknown')}",
                correct_answer=correct_text,
                selected_answer=selected_text,
                options=options,
                use_fallback_on_error=self.fallback_on_error,
            )
        except Exception as exc:
            if not self.fallback_on_error:
                raise
            res = MisconceptionClassificationResult(
                misconception_type=DEFAULT_FALLBACK_TYPE,
                description=DEFAULT_FALLBACK_DESCRIPTION,
            )

        # Import backend ClassifierResult for 100% protocol fidelity
        try:
            from app.services.misconception_tracker import ClassifierResult
            return ClassifierResult(
                misconception_type=res.misconception_type,
                description=res.description,
            )
        except ImportError:
            return res
