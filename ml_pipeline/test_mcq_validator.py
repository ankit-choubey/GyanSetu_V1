"""
Test for ML-004 (mcq_validator). Fully offline, deterministic — no Groq
or network dependency of any kind.

Run:
    python -m ml_pipeline.test_mcq_validator
"""
import sys

from ml_pipeline.mcq_validator import validate_mcqs

SOURCE = (
    "Stratified sampling divides the population into homogeneous subgroups "
    "(strata) before sampling independently within each stratum. This "
    "improves precision when subgroups differ meaningfully from each other."
)

VALID_MCQ = {
    "question": "What does stratified sampling do to the population?",
    "options": [
        "Divides it into homogeneous strata before sampling",
        "Selects every 10th individual at random",
        "Surveys every member of the population",
        "Ignores differences between subgroups",
    ],
    "correct_answer": "A",
    "explanation": "The source states strata are homogeneous subgroups sampled independently.",
    "competency": "Sampling Design",
    "difficulty": "medium",
}

MISSING_FIELD_MCQ = {
    "question": "Missing explanation and competency",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "A",
    "difficulty": "easy",
    # explanation, competency missing
}

WRONG_OPTION_COUNT_MCQ = {**VALID_MCQ, "options": VALID_MCQ["options"][:3]}

INVALID_ANSWER_LETTER_MCQ = {**VALID_MCQ, "correct_answer": "E"}

DUPLICATE_OPTIONS_MCQ = {
    **VALID_MCQ,
    "options": [
        "Divides it into homogeneous strata before sampling",
        "Divides it into homogeneous strata before sampling",  # duplicate of option A
        "Surveys every member of the population",
        "Ignores differences between subgroups",
    ],
}

UNGROUNDED_MCQ = {
    "question": "What is the capital of France?",
    "options": ["Paris", "Berlin", "Madrid", "Rome"],
    "correct_answer": "A",
    "explanation": "General knowledge, not from the source content.",
    "competency": "Sampling Design",
    "difficulty": "easy",
}

NEAR_DUPLICATE_QUESTION_MCQ = {
    **VALID_MCQ,
    "question": "What does stratified sampling do to a population?",  # near-identical wording
}


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []

    # 1. Valid MCQ passes
    r = validate_mcqs([VALID_MCQ], SOURCE)[0]
    results.append(_report("valid MCQ passes", r["valid"] is True and r["issues"] == []))

    # 2. Missing required field fails
    r = validate_mcqs([MISSING_FIELD_MCQ], SOURCE)[0]
    results.append(_report(
        "missing required field fails",
        r["valid"] is False and not r["checks"]["structural"]
    ))

    # 3. Wrong number of options fails
    r = validate_mcqs([WRONG_OPTION_COUNT_MCQ], SOURCE)[0]
    results.append(_report(
        "wrong number of options fails",
        r["valid"] is False and not r["checks"]["structural"]
    ))

    # 4. Invalid correct answer fails
    r = validate_mcqs([INVALID_ANSWER_LETTER_MCQ], SOURCE)[0]
    results.append(_report(
        "invalid correct_answer letter fails",
        r["valid"] is False and not r["checks"]["structural"]
    ))

    # 5. Duplicate options detected
    r = validate_mcqs([DUPLICATE_OPTIONS_MCQ], SOURCE)[0]
    results.append(_report(
        "duplicate options detected",
        r["valid"] is False and not r["checks"]["distractor"]
    ))

    # 6. Duplicate/near-duplicate questions detected (cross-item)
    batch = validate_mcqs([VALID_MCQ, NEAR_DUPLICATE_QUESTION_MCQ], SOURCE)
    results.append(_report(
        "near-duplicate questions detected across the batch",
        not batch[0]["checks"]["duplicate"] and not batch[1]["checks"]["duplicate"]
    ))

    # 7. Unsupported / poorly grounded question detected
    r = validate_mcqs([UNGROUNDED_MCQ], SOURCE)[0]
    results.append(_report(
        "poorly grounded answer detected",
        r["valid"] is False and not r["checks"]["grounding"]
    ))

    # 8. Mixed batch — one valid, several invalid, results independent per item
    mixed = validate_mcqs(
        [VALID_MCQ, MISSING_FIELD_MCQ, UNGROUNDED_MCQ],
        SOURCE,
    )
    results.append(_report(
        "mixed batch: valid/invalid results are independent per item",
        mixed[0]["valid"] is True
        and mixed[1]["valid"] is False
        and mixed[2]["valid"] is False
        and len(mixed) == 3
    ))

    # Sanity: validator must not mutate the input MCQ dicts
    original = dict(VALID_MCQ)
    validate_mcqs([VALID_MCQ], SOURCE)
    results.append(_report("validator does not mutate input MCQs", VALID_MCQ == original))

    return all(results)


if __name__ == "__main__":
    ok = run_tests()
    print("\nML-004 TEST SUITE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
