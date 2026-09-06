"""
ml_pipeline/test_mcq_scorer.py — Automated Unit Tests for MCQ Quality Scorer (3 Tests).

Run:
    python -m ml_pipeline.test_mcq_scorer
"""
import sys

from ml_pipeline.mcq_scorer import (
    shuffle_mcq_options,
    classify_cognitive_level,
    score_mcq_quality,
)


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []

    mcq = {
        "question": "Calculate the sample variance given stratum weights.",
        "options": [
            "0.1425 variance estimate",
            "0.8200 variance estimate",
            "0.3150 variance estimate",
            "0.5500 variance estimate",
        ],
        "correct_answer": "A",
        "explanation": "Calculated using the Neyman formula.",
        "competency": "Sampling Design",
        "difficulty": "hard",
    }
    source = "The Neyman formula yields 0.1425 variance estimate for the sample."

    # 1. Option shuffling maps correct text accurately
    shuffled = shuffle_mcq_options(mcq, seed=42)
    new_letter = shuffled["correct_answer"]
    new_idx = ord(new_letter) - ord("A")
    correct_preserved = shuffled["options"][new_idx] == mcq["options"][0]
    results.append(_report(
        "shuffling preserves correct answer text mapping",
        correct_preserved and shuffled["position_shuffled"] is True
    ))

    # 2. Cognitive level classification
    cog_app = classify_cognitive_level("Calculate the stratified mean")
    cog_ana = classify_cognitive_level("Compare Paasche and Laspeyres price indices")
    cog_rec = classify_cognitive_level("What is the definition of NSS?")
    cog_ok = cog_app == "Application" and cog_ana == "Analysis" and cog_rec == "Recall"
    results.append(_report("cognitive level classifies Bloom taxonomy accurately", cog_ok))

    # 3. Continuous quality score computation
    scored = score_mcq_quality(mcq, source)
    score_val = scored.get("quality_score", 0.0)
    score_ok = 0.6 <= score_val <= 1.0 and "metrics" in scored and scored["cognitive_level"] == "Application"
    results.append(_report("multi-metric quality score computes properly", score_ok))

    all_ok = all(results)
    print(f"\nMCQ SCORER TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
