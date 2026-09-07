"""
ML-004 — MCQ validation.

Evaluates MCQs produced by mcq_generator.generate_mcqs() and reports
pass/fail per check. Does NOT modify, regenerate, or repair MCQs —
validation and generation stay strictly separate.

Uses only stdlib (difflib) for grounding/duplicate similarity — no new
dependency added, since a simple explainable approach is what the MVP
calls for, not a "fancy model."

Known limitation, stated plainly rather than glossed over: word-overlap
and difflib ratio are crude proxies for "grounded" and "duplicate."
They will produce false positives/negatives on paraphrased or reworded
text. This is intentional for an explainable MVP-scope validator, not a
claim of semantic correctness.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

_REQUIRED_FIELDS = ("question", "options", "correct_answer", "explanation", "competency", "difficulty")
_VALID_ANSWER_LETTERS = ("A", "B", "C", "D")

# Thresholds — explicit and tunable, not hidden magic numbers.
GROUNDING_OVERLAP_THRESHOLD = 0.3   # fraction of correct-answer words found in source_content
DUPLICATE_QUESTION_THRESHOLD = 0.85  # difflib ratio above which two questions count as near-duplicate


def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric word tokens, length > 2 (drops stopword-ish noise)."""
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


def _word_overlap_ratio(text: str, source: str) -> float:
    """Fraction of text's tokens that also appear in source. 1.0 if text has no tokens."""
    text_tokens = _tokenize(text)
    if not text_tokens:
        return 1.0
    source_tokens = _tokenize(source)
    return len(text_tokens & source_tokens) / len(text_tokens)


def _check_structural(mcq: dict) -> tuple[bool, list[str]]:
    """Returns (passed, issues). Also the gatekeeper for whether grounding/
    distractor checks can even run meaningfully on this item."""
    issues = []

    if not isinstance(mcq, dict):
        return False, ["MCQ is not a dict"]

    for field in _REQUIRED_FIELDS:
        if field not in mcq or mcq.get(field) in (None, ""):
            issues.append(f"missing or empty required field: '{field}'")

    if "question" in mcq and not str(mcq.get("question", "")).strip():
        issues.append("question text is empty")

    options = mcq.get("options")
    if not isinstance(options, list) or len(options) != 4:
        issues.append(f"'options' must be a list of exactly 4 items (got {options!r})")
    elif any(not str(opt).strip() for opt in options):
        issues.append("one or more options are empty")

    correct_answer = mcq.get("correct_answer")
    if correct_answer not in _VALID_ANSWER_LETTERS:
        issues.append(f"'correct_answer' must be one of A/B/C/D (got {correct_answer!r})")
    elif isinstance(options, list) and (ord(correct_answer) - ord("A")) >= len(options):
        issues.append("'correct_answer' does not refer to a valid option index")

    if not str(mcq.get("competency", "")).strip():
        issues.append("'competency' is missing or empty")
    if not str(mcq.get("difficulty", "")).strip():
        issues.append("'difficulty' is missing or empty")

    return (len(issues) == 0), issues


def _check_grounding(mcq: dict, source_content: str) -> tuple[bool, list[str]]:
    """Simple word-overlap check on the correct answer's text against
    source_content. Not semantic similarity — see module docstring."""
    options = mcq.get("options") or []
    correct_answer = mcq.get("correct_answer")
    if correct_answer not in _VALID_ANSWER_LETTERS:
        return False, ["cannot check grounding — correct_answer is invalid"]

    idx = ord(correct_answer) - ord("A")
    if idx >= len(options):
        return False, ["cannot check grounding — correct_answer index out of range"]

    answer_text = str(options[idx])
    ratio = _word_overlap_ratio(answer_text, source_content)
    if ratio < GROUNDING_OVERLAP_THRESHOLD:
        return False, [
            f"correct answer may not be grounded in source content "
            f"(word overlap {ratio:.2f} < {GROUNDING_OVERLAP_THRESHOLD})"
        ]
    return True, []


def _check_distractors(mcq: dict) -> tuple[bool, list[str]]:
    """Flags duplicate options, including the correct answer's text being
    duplicated among the distractors."""
    options = mcq.get("options")
    if not isinstance(options, list) or len(options) < 2:
        return False, ["cannot check distractors — options missing or too few"]

    issues = []
    normalized = [str(opt).strip().lower() for opt in options]
    correct_answer = mcq.get("correct_answer")
    correct_idx = ord(correct_answer) - ord("A") if correct_answer in _VALID_ANSWER_LETTERS else None

    seen = {}
    for i, opt in enumerate(normalized):
        if opt in seen:
            j = seen[opt]
            if correct_idx in (i, j):
                issues.append(f"correct answer's text is duplicated among options ({j} and {i})")
            else:
                issues.append(f"duplicate options detected (index {j} and {i})")
        else:
            seen[opt] = i

    return (len(issues) == 0), issues


def _check_duplicate_questions(mcqs: list[dict]) -> dict[int, list[str]]:
    """Cross-item check. Returns {index: [issue, ...]} only for indices
    that have at least one near-duplicate elsewhere in the list."""
    issues_by_index: dict[int, list[str]] = {}
    questions = [str(mcq.get("question", "")) for mcq in mcqs]

    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            if not questions[i].strip() or not questions[j].strip():
                continue  # empty question already flagged by structural check
            ratio = SequenceMatcher(None, questions[i].lower(), questions[j].lower()).ratio()
            if ratio >= DUPLICATE_QUESTION_THRESHOLD:
                msg_i = f"near-duplicate of question at index {j} (similarity {ratio:.2f})"
                msg_j = f"near-duplicate of question at index {i} (similarity {ratio:.2f})"
                issues_by_index.setdefault(i, []).append(msg_i)
                issues_by_index.setdefault(j, []).append(msg_j)

    return issues_by_index


def validate_mcqs(mcqs: list[dict], source_content: str) -> list[dict]:
    """
    Validates a batch of MCQs. Does not modify the input MCQs.

    Returns:
        A list of validation result dicts, same order/length as `mcqs`:
        {
            "index": int,
            "valid": bool,
            "issues": [str, ...],
            "checks": {
                "structural": bool,
                "grounding": bool,
                "duplicate": bool,
                "distractor": bool,
            },
        }
        "checks" values are True (passed) / False (failed). If a check
        couldn't run meaningfully (e.g. grounding check when options are
        malformed), it's marked False with an explanatory issue rather
        than silently skipped.
    """
    duplicate_issues = _check_duplicate_questions(mcqs)

    results = []
    for i, mcq in enumerate(mcqs):
        structural_ok, structural_issues = _check_structural(mcq)

        if structural_ok:
            grounding_ok, grounding_issues = _check_grounding(mcq, source_content)
            distractor_ok, distractor_issues = _check_distractors(mcq)
        else:
            # Don't attempt grounding/distractor checks on a structurally
            # broken MCQ — the required fields to check them may not exist.
            grounding_ok, grounding_issues = False, ["skipped — structural check failed first"]
            distractor_ok, distractor_issues = False, ["skipped — structural check failed first"]

        this_duplicate_issues = duplicate_issues.get(i, [])
        duplicate_ok = len(this_duplicate_issues) == 0

        all_issues = structural_issues + grounding_issues + distractor_issues + this_duplicate_issues

        results.append({
            "index": i,
            "valid": structural_ok and grounding_ok and distractor_ok and duplicate_ok,
            "issues": all_issues,
            "checks": {
                "structural": structural_ok,
                "grounding": grounding_ok,
                "duplicate": duplicate_ok,
                "distractor": distractor_ok,
            },
        })

    return results


if __name__ == "__main__":
    sample_source = (
        "Stratified sampling divides the population into homogeneous "
        "subgroups (strata) before sampling independently within each stratum."
    )
    sample_mcqs = [{
        "question": "What does stratified sampling do?",
        "options": [
            "Divides the population into homogeneous strata",
            "Selects every 10th individual",
            "Surveys the entire population",
            "Ignores subgroup differences",
        ],
        "correct_answer": "A",
        "explanation": "Per the source content.",
        "competency": "Sampling Design",
        "difficulty": "medium",
    }]
    for result in validate_mcqs(sample_mcqs, sample_source):
        print(result)
