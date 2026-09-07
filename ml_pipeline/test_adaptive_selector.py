"""
ml_pipeline/test_adaptive_selector.py — Automated Unit Tests for Adaptive Selector (4 Tests).

Run:
    python -m ml_pipeline.test_adaptive_selector
"""
import sys

from ml_pipeline.adaptive_selector import select_next_question


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []

    bank = [
        {"question_id": "q1", "question": "Easy Q1", "difficulty": "easy", "subskill": "definitions"},
        {"question_id": "q2", "question": "Medium Q2", "difficulty": "medium", "subskill": "variance_formula"},
        {"question_id": "q3", "question": "Hard Q3", "difficulty": "hard", "subskill": "variance_formula"},
        {"question_id": "q4", "question": "Easy Q4 Remediation", "difficulty": "easy", "subskill": "variance_formula"},
    ]

    # 1. Initial selection starts at easy
    r1 = select_next_question(bank, [])
    results.append(_report(
        "initial selection starts at easy difficulty",
        r1["target_difficulty"] == "easy" and r1["next_question"]["question_id"] == "q1"
    ))

    # 2. Success steps up difficulty
    history_success = [
        {"question_id": "q1", "difficulty": "easy", "subskill": "definitions", "is_correct": True}
    ]
    r2 = select_next_question(bank, history_success)
    results.append(_report(
        "success on easy steps up to medium",
        r2["target_difficulty"] == "medium" and r2["next_question"]["question_id"] == "q2"
    ))

    # 3. Failure steps down and isolates weak subskill
    history_fail = [
        {"question_id": "q1", "difficulty": "easy", "subskill": "definitions", "is_correct": True},
        {"question_id": "q2", "difficulty": "medium", "subskill": "variance_formula", "is_correct": False},
    ]
    r3 = select_next_question(bank, history_fail)
    results.append(_report(
        "failure steps down and targets weak subskill",
        r3["target_difficulty"] == "easy"
        and r3["target_subskill"] == "variance_formula"
        and r3["next_question"]["question_id"] == "q4"
    ))

    # 4. Pool exhaustion sets is_complete True
    history_full = [
        {"question_id": "q1", "is_correct": True},
        {"question_id": "q2", "is_correct": True},
        {"question_id": "q3", "is_correct": True},
        {"question_id": "q4", "is_correct": True},
    ]
    r4 = select_next_question(bank, history_full)
    results.append(_report(
        "exhausted pool terminates assessment cleanly",
        r4["is_complete"] is True and r4["next_question"] is None
    ))

    all_ok = all(results)
    print(f"\nADAPTIVE SELECTOR TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
