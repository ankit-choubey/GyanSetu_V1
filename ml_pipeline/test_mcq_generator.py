"""
Test for ML-003 (mcq_generator).

Default run (no API key needed):
    python -m ml_pipeline.test_mcq_generator

Live integration test (needs GROQ_API_KEY, hits the real API, costs a
real request — run it deliberately, never as part of the normal suite):
    python -m ml_pipeline.test_mcq_generator --live
"""
import json
import sys

from ml_pipeline.mcq_generator import parse_mcq_response

VALID_RESPONSE = json.dumps([
    {
        "question": "What does stratified sampling do to the population?",
        "options": [
            "Divides it into homogeneous subgroups before sampling",
            "Selects every 10th individual",
            "Surveys the entire population",
            "Ignores subgroup differences",
        ],
        "correct_answer": "A",
        "explanation": "The content states strata are homogeneous subgroups sampled independently.",
        "competency": "Sampling Design",
        "difficulty": "medium",
    }
])

MALFORMED_NOT_JSON = "Sure! Here are some questions: 1. What is sampling?"

MALFORMED_NOT_ARRAY = json.dumps({"question": "not wrapped in a list"})

MALFORMED_MISSING_FIELD = json.dumps([
    {
        "question": "Missing explanation and competency",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "difficulty": "easy",
    }
])

MALFORMED_WRONG_OPTION_COUNT = json.dumps([
    {
        "question": "Only 3 options",
        "options": ["A", "B", "C"],
        "correct_answer": "A",
        "explanation": "x",
        "competency": "Sampling Design",
        "difficulty": "easy",
    }
])

MALFORMED_BAD_ANSWER_LETTER = json.dumps([
    {
        "question": "correct_answer is not A-D",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "E",
        "explanation": "x",
        "competency": "Sampling Design",
        "difficulty": "easy",
    }
])

MARKDOWN_WRAPPED_VALID = "```json\n" + VALID_RESPONSE + "\n```"


def _expect_success(name: str, raw: str) -> bool:
    try:
        mcqs = parse_mcq_response(raw)
    except ValueError as e:
        print(f"[FAIL] {name}: expected success, raised ValueError: {e}")
        return False

    ok = (
        isinstance(mcqs, list)
        and len(mcqs) == 1
        and len(mcqs[0]["options"]) == 4
        and mcqs[0]["correct_answer"] in ("A", "B", "C", "D")
        and all(k in mcqs[0] for k in ("question", "options", "correct_answer", "explanation", "competency", "difficulty"))
    )
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    return ok


def _expect_failure(name: str, raw: str) -> bool:
    try:
        parse_mcq_response(raw)
        print(f"[FAIL] {name}: expected ValueError, but no exception was raised")
        return False
    except ValueError:
        print(f"[PASS] {name}")
        return True


def run_offline_tests() -> bool:
    results = [
        _expect_success("valid response parses with correct schema", VALID_RESPONSE),
        _expect_success("markdown-fenced valid response still parses", MARKDOWN_WRAPPED_VALID),
        _expect_failure("non-JSON model output raises ValueError", MALFORMED_NOT_JSON),
        _expect_failure("JSON object instead of array raises ValueError", MALFORMED_NOT_ARRAY),
        _expect_failure("missing required field raises ValueError", MALFORMED_MISSING_FIELD),
        _expect_failure("wrong option count raises ValueError", MALFORMED_WRONG_OPTION_COUNT),
        _expect_failure("invalid correct_answer letter raises ValueError", MALFORMED_BAD_ANSWER_LETTER),
    ]
    return all(results)


def run_live_test() -> bool:
    """Only called with --live. Imports generate_mcqs (and therefore
    config/GROQ_API_KEY) lazily so the offline suite never needs a key."""
    from ml_pipeline.config import GROQ_API_KEY
    from ml_pipeline.mcq_generator import generate_mcqs

    if not GROQ_API_KEY:
        print("[SKIP] live test: GROQ_API_KEY not set — this is not a failure, just not run.")
        return True

    sample_text = (
        "Stratified sampling divides the population into homogeneous "
        "subgroups (strata) before sampling independently within each stratum."
    )
    try:
        mcqs = generate_mcqs(sample_text, "Sampling Design", 3, "medium")
    except Exception as e:
        print(f"[FAIL] live test: generate_mcqs raised: {e}")
        return False

    ok = len(mcqs) == 3
    print(f"[{'PASS' if ok else 'FAIL'}] live test: got {len(mcqs)} MCQs back from Groq")
    for mcq in mcqs:
        print(f"  - {mcq['question']} (correct: {mcq['correct_answer']})")
    return ok


if __name__ == "__main__":
    offline_ok = run_offline_tests()
    print("\nOFFLINE TEST SUITE:", "PASS" if offline_ok else "FAIL")

    if "--live" in sys.argv:
        print("\nRunning live Groq integration test...")
        live_ok = run_live_test()
        print("LIVE TEST:", "PASS" if live_ok else "FAIL")
        sys.exit(0 if (offline_ok and live_ok) else 1)

    sys.exit(0 if offline_ok else 1)
