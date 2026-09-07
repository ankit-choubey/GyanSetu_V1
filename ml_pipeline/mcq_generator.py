"""
ML-003 — MCQ generation via Groq.

Scope: generate MCQs from supplied content only. Structural validation
here is limited to shape correctness (required fields, exactly 4 options,
correct_answer is A-D). Deeper quality checks — grounding/similarity,
duplicate detection, distractor plausibility — belong to ML-004
(mcq_validator.py), not here.
"""
from __future__ import annotations

import json
import os

from openai import OpenAI

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_PRIMARY

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "mcq_prompt.txt")
_REQUIRED_FIELDS = ("question", "options", "correct_answer", "explanation", "competency", "difficulty")
_VALID_ANSWER_LETTERS = ("A", "B", "C", "D")

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    return _client


def _load_prompt_template() -> str:
    with open(_PROMPT_PATH, "r") as f:
        return f.read()


def _strip_code_fences(raw: str) -> str:
    """Model is instructed to output raw JSON, but strip fences defensively
    in case it wraps the response in ```json ... ``` anyway."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def _validate_mcq_shape(mcq: dict, index: int) -> list[str]:
    """Returns a list of human-readable issue strings; empty list = valid shape."""
    issues = []

    if not isinstance(mcq, dict):
        return [f"item {index}: not a JSON object"]

    for field in _REQUIRED_FIELDS:
        if field not in mcq:
            issues.append(f"item {index}: missing field '{field}'")

    options = mcq.get("options")
    if not isinstance(options, list) or len(options) != 4:
        issues.append(f"item {index}: 'options' must be a list of exactly 4 items")

    if mcq.get("correct_answer") not in _VALID_ANSWER_LETTERS:
        issues.append(f"item {index}: 'correct_answer' must be one of A/B/C/D")

    return issues


def parse_mcq_response(raw_text: str) -> list[dict]:
    """
    Parses and shape-validates a raw LLM response string into a list of
    MCQ dicts. Separated from generate_mcqs() so it can be unit-tested
    with fixture strings, with no network call involved.

    Raises:
        ValueError: if the text isn't valid JSON, isn't a JSON array, or
        any element fails shape validation (missing fields, wrong option
        count, invalid correct_answer letter).
    """
    cleaned = _strip_code_fences(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"MCQ response is not valid JSON: {e}\nRaw (truncated): {cleaned[:300]!r}")

    if not isinstance(parsed, list):
        raise ValueError(f"MCQ response must be a JSON array, got {type(parsed).__name__}")

    all_issues = []
    for i, mcq in enumerate(parsed):
        all_issues.extend(_validate_mcq_shape(mcq, i))

    if all_issues:
        raise ValueError("MCQ response failed shape validation:\n" + "\n".join(all_issues))

    return parsed


from ml_pipeline.semantic_cache import get_semantic_cache


def generate_mcqs(
    content: str,
    competency: str,
    num_questions: int,
    difficulty: str,
    use_cache: bool = True,
) -> list[dict]:
    """
    THE CONTRACT WITH BACKEND — do not change this signature without
    telling Utkarsh/Mounya first.

    Args:
        content: source text the questions must be grounded in (e.g. from
            document_processor.process_document()).
        competency: the competency being tested, e.g. "Sampling Design".
        num_questions: how many MCQs to generate.
        difficulty: "easy" | "medium" | "hard".
        use_cache: whether to utilize Redis/in-memory semantic caching (default True).

    Returns:
        list of dicts: {question, options (4 items), correct_answer (A-D),
        explanation, competency, difficulty}. Shape-validated, but NOT
        grounding/quality-validated — that's ML-004's job.

    Raises:
        ValueError: if GROQ_API_KEY is unset, or the model's response
        can't be parsed into valid-shaped MCQs.
    """
    cache = get_semantic_cache()
    if use_cache:
        cache_key = cache.compute_mcq_key(content, competency, difficulty, num_questions)
        cached_val = cache.get(cache_key)
        if cached_val is not None and isinstance(cached_val, list):
            return cached_val

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set — see ENVIRONMENT_SETUP.md §3 / ml_pipeline/.env.example")

    prompt = _load_prompt_template().format(
        num_questions=num_questions,
        competency=competency,
        difficulty=difficulty,
        content=content,
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content
    parsed = parse_mcq_response(raw)

    if use_cache and parsed:
        cache_key = cache.compute_mcq_key(content, competency, difficulty, num_questions)
        cache.set(cache_key, parsed)

    return parsed


if __name__ == "__main__":
    sample_text = (
        "Stratified sampling divides the population into homogeneous "
        "subgroups (strata) before sampling independently within each stratum."
    )
    result = generate_mcqs(sample_text, "Sampling Design", 3, "medium")
    print(json.dumps(result, indent=2))
