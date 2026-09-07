"""
ml_pipeline/adaptive_selector.py — Adaptive Question Selection Engine.

Implements the dynamic assessment selector per GyanSetu Build Guide §11:
- 3-tier difficulty state machine: 'easy' -> 'medium' -> 'hard'.
- Progression rule: Increases difficulty after successful answer.
- Remediation rule: Decreases difficulty after failure and targets the specific weak subskill.
- Anti-repetition guard: Never repeats an already answered question within the same session.
- Pool exhaustion handling: Returns fallback item or terminates assessment gracefully.
"""
from __future__ import annotations

from typing import Any

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


def select_next_question(
    item_bank: list[dict[str, Any]],
    session_history: list[dict[str, Any]],
    competency: str | None = None,
    current_theta: float = 0.0,
) -> dict[str, Any]:
    """
    Determines and returns the next adaptive MCQ based on learner performance history.

    Args:
        item_bank: Available validated question pool.
        session_history: List of previously attempted item responses:
                         [{"question_id": "...", "subskill": "...", "difficulty": "...", "is_correct": bool}]
        competency: Optional filter to restrict questions to a specific competency.

    Returns:
        Dict: {"next_question": dict | None, "target_difficulty": str, "target_subskill": str | None, "is_complete": bool}
    """
    if not item_bank:
        return {
            "next_question": None,
            "target_difficulty": "easy",
            "target_subskill": None,
            "is_complete": True,
            "reason": "Item bank is empty.",
        }

    # Extract already answered question identifiers
    answered_ids = {
        h.get("question_id") or h.get("question")
        for h in session_history
        if h.get("question_id") or h.get("question")
    }

    # Filter available candidates
    available = [
        q for q in item_bank
        if (q.get("question_id") or q.get("question")) not in answered_ids
        and (competency is None or q.get("competency") == competency)
    ]

    if not available:
        return {
            "next_question": None,
            "target_difficulty": "medium",
            "target_subskill": None,
            "is_complete": True,
            "reason": "All available questions in this competency have been completed.",
        }

    # Determine next target difficulty and subskill
    if not session_history:
        target_diff = "easy"
        target_subskill = None
    else:
        last_attempt = session_history[-1]
        last_diff = last_attempt.get("difficulty", "easy").lower()
        last_correct = bool(last_attempt.get("is_correct", False))
        last_subskill = last_attempt.get("subskill")

        if last_correct:
            # Step up difficulty
            if last_diff == "easy":
                target_diff = "medium"
            else:
                target_diff = "hard"
            target_subskill = None
        else:
            # Step down difficulty and isolate weak subskill
            if last_diff == "hard":
                target_diff = "medium"
            else:
                target_diff = "easy"
            target_subskill = last_subskill

    # 1. Best match: both target difficulty and weak subskill match
    if target_subskill:
        subskill_matches = [
            q for q in available
            if q.get("subskill") == target_subskill and q.get("difficulty", "medium").lower() == target_diff
        ]
        if subskill_matches:
            return {
                "next_question": subskill_matches[0],
                "target_difficulty": target_diff,
                "target_subskill": target_subskill,
                "is_complete": False,
                "reason": "Targeted remediation for weak subskill.",
            }

    # 2. Match target difficulty with Fisher Information optimization
    diff_matches = [
        q for q in available
        if q.get("difficulty", "medium").lower() == target_diff
    ]
    if diff_matches:
        from ml_pipeline.psychometric_engine import TriTierFSM
        best_candidate = TriTierFSM.select_item_by_fisher_info(diff_matches, theta=current_theta)
        return {
            "next_question": best_candidate,
            "target_difficulty": target_diff,
            "target_subskill": target_subskill,
            "is_complete": False,
            "reason": f"Selected question matching target difficulty '{target_diff}' via Fisher information.",
        }

    # 3. Fallback: Any available question
    from ml_pipeline.psychometric_engine import TriTierFSM
    best_fallback = TriTierFSM.select_item_by_fisher_info(available, theta=current_theta)
    return {
        "next_question": best_fallback,
        "target_difficulty": best_fallback.get("difficulty", "medium").lower(),
        "target_subskill": target_subskill,
        "is_complete": False,
        "reason": "Fallback item selected as exact difficulty was exhausted.",
    }
