"""
ml_pipeline/mcq_scorer.py — Multi-Metric MCQ Quality Scorer & Option Shuffler.

Implements the advanced evaluation and calibration layer per GyanSetu Build Guide §11:
- Continuous Quality Scoring: Evaluates grounding, distractor entropy, and option length variance.
- Cognitive Level Classification: Classifies items into Bloom's levels (Recall, Understanding, Application).
- Option Position Randomizer: Shuffles option keys to eliminate the 'Option A' answer position bias
  noted in handout.md §13.
"""
from __future__ import annotations

import random
import re
from typing import Any

from ml_pipeline.mcq_validator import _word_overlap_ratio

LETTERS = ["A", "B", "C", "D"]


def shuffle_mcq_options(mcq: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
    """
    Shuffles the options of an MCQ and re-maps the correct_answer letter,
    guaranteeing uniform distribution of answer keys and eliminating bias.

    Args:
        mcq: Dictionary with 'options' and 'correct_answer' (A-D).
        seed: Optional random seed for deterministic testing.

    Returns:
        New MCQ dictionary with shuffled options and updated correct_answer.
    """
    options = mcq.get("options", [])
    correct_letter = mcq.get("correct_answer", "A")

    if not isinstance(options, list) or len(options) != 4 or correct_letter not in LETTERS:
        return dict(mcq)

    correct_idx = ord(correct_letter) - ord("A")
    correct_text = options[correct_idx]

    # Pair options with flags
    items = [(opt, i == correct_idx) for i, opt in enumerate(options)]
    rng = random.Random(seed)
    rng.shuffle(items)

    shuffled_options = [opt for opt, _ in items]
    new_correct_idx = next(i for i, (_, is_c) in enumerate(items) if is_c)
    new_correct_letter = LETTERS[new_correct_idx]

    shuffled_mcq = dict(mcq)
    shuffled_mcq["options"] = shuffled_options
    shuffled_mcq["correct_answer"] = new_correct_letter
    shuffled_mcq["position_shuffled"] = True
    return shuffled_mcq


def classify_cognitive_level(question: str) -> str:
    """
    Infers Bloom's cognitive level from question stem keywords.
    """
    q = question.lower()
    if any(k in q for k in ["calculate", "compute", "estimate", "apply", "solve", "given"]):
        return "Application"
    elif any(k in q for k in ["compare", "distinguish", "contrast", "differentiate", "why"]):
        return "Analysis"
    elif any(k in q for k in ["explain", "describe", "interpret", "what does", "purpose"]):
        return "Understanding"
    return "Recall"


def compute_distractor_entropy(options: list[str]) -> float:
    """
    Calculates option length uniformity (0.0 to 1.0).
    A question where one option is 100 characters and others are 5 characters is flawed.
    """
    if len(options) != 4:
        return 0.0
    lengths = [len(str(o).strip()) for o in options]
    avg_len = sum(lengths) / len(lengths)
    if avg_len == 0:
        return 0.0

    # Variance from mean length
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    cv = std_dev / avg_len  # coefficient of variation
    # cv == 0 is perfect uniformity (score 1.0), cv >= 1.0 is highly skewed (score ~0.0)
    score = max(0.0, 1.0 - min(1.0, cv))
    return round(score, 4)


def score_mcq_quality(mcq: dict[str, Any], source_text: str) -> dict[str, Any]:
    """
    Calculates a multi-dimensional continuous quality score (0.0 to 1.0).

    Weights:
    - 0.40: Grounding overlap ratio
    - 0.30: Distractor length entropy / uniformity
    - 0.30: Structural integrity (clean fields, distinct options)
    """
    options = mcq.get("options", [])
    correct_letter = mcq.get("correct_answer", "A")

    # 1. Grounding score
    grounding = 0.0
    if isinstance(options, list) and correct_letter in LETTERS:
        idx = ord(correct_letter) - ord("A")
        if idx < len(options):
            grounding = _word_overlap_ratio(str(options[idx]), source_text)

    # 2. Distractor entropy score
    entropy = compute_distractor_entropy(options) if isinstance(options, list) else 0.0

    # 3. Structural score
    has_all_fields = all(k in mcq and mcq[k] for k in ["question", "options", "correct_answer", "explanation"])
    unique_options = len(set(str(o).strip().lower() for o in options)) == 4 if isinstance(options, list) else False
    structural = 1.0 if (has_all_fields and unique_options) else 0.4

    # Composite score
    overall_score = round(0.40 * min(1.0, grounding) + 0.30 * entropy + 0.30 * structural, 3)

    return {
        **mcq,
        "quality_score": overall_score,
        "metrics": {
            "grounding_overlap": round(grounding, 3),
            "distractor_entropy": entropy,
            "structural_score": structural,
        },
        "cognitive_level": classify_cognitive_level(str(mcq.get("question", ""))),
    }


def score_mcq(mcq: dict[str, Any], source_text: str = "") -> dict[str, Any]:
    """Convenience alias for score_mcq_quality."""
    return score_mcq_quality(mcq, source_text=source_text)
