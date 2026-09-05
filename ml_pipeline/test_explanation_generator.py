"""
ml_pipeline/test_explanation_generator.py — Automated Unit Tests for Explanation Generator (2 Tests).

Run:
    python -m ml_pipeline.test_explanation_generator
"""
import sys

from ml_pipeline.explanation_generator import generate_feedback


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []

    mcq = {
        "question": "What is the primary benefit of Stratified Random Sampling?",
        "options": [
            "Guarantees representation of key subgroups and reduces variance",
            "Eliminates all non-sampling errors completely",
            "Requires no prior knowledge of the population frame",
            "Ensures the sample size equals the population size",
        ],
        "correct_answer": "A",
        "explanation": "Stratification partitions heterogeneous populations into homogeneous strata, reducing standard error.",
        "competency": "Sampling Design",
        "subskill": "Stratum Variance Reduction",
    }

    # 1. Correct selection returns positive mastery feedback
    r1 = generate_feedback(mcq, "A")
    r1_ok = r1["is_correct"] is True and r1["subskill_gap"] is None and "Correct!" in r1["feedback"]
    results.append(_report("correct answer generates positive mastery confirmation", r1_ok))

    # 2. Incorrect selection identifies distractor and subskill gap
    r2 = generate_feedback(mcq, "B")
    r2_ok = (
        r2["is_correct"] is False
        and r2["subskill_gap"] == "Stratum Variance Reduction"
        and "Incorrect." in r2["feedback"]
        and "(B)" in r2["feedback"]
    )
    results.append(_report("incorrect answer isolates chosen distractor and identifies gap", r2_ok))

    all_ok = all(results)
    print(f"\nEXPLANATION GENERATOR TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
