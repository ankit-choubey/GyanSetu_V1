"""
ml_pipeline/tests/test_psychometric_engine.py — Unit tests for Psychometric Engine & TriTierFSM.
"""
from __future__ import annotations

import math
from ml_pipeline.psychometric_engine import (
    ItemContext,
    InteractionTelemetry,
    PsychometricEngine,
    TriTierFSM,
)


def test_rapid_guessing_threshold_detection():
    """Verifies that responses faster than RGT (e.g. < 3.0s) are flagged as unreflective guesses."""
    item = ItemContext(
        item_id="item_001",
        competency_id="comp_stat",
        subskill_id="sub_sampling",
        difficulty=0.0,
        time_limit_sec=60.0,
        target_time_sec=30.0,
    )
    # Fast 1.5s guess
    fast_tel = InteractionTelemetry(
        learner_id="officer_1",
        item_id="item_001",
        selected_option="A",
        response_time_sec=1.5,
        is_correct=True,
    )
    res = PsychometricEngine.evaluate_response(item, fast_tel, current_theta=0.0)
    assert res["is_rapid_guess"] is True
    assert res["cognitive_fluency_index"] == 0.0  # Guessing earns 0 fluency
    assert res["posterior_theta"] == 0.0  # Rapid guess does not inflate ability


def test_signed_residual_time_and_fluency_scoring():
    """Tests SRT points reward for fast accurate answer and penalty for fast incorrect answer."""
    item = ItemContext(
        item_id="item_002",
        competency_id="comp_stat",
        subskill_id="sub_sampling",
        difficulty=0.0,
        time_limit_sec=60.0,
        target_time_sec=30.0,
    )

    # 1. Fast accurate answer (t=15s <= target 30s)
    good_tel = InteractionTelemetry(
        learner_id="officer_1",
        item_id="item_002",
        selected_option="B",
        response_time_sec=15.0,
        is_correct=True,
    )
    res_good = PsychometricEngine.evaluate_response(item, good_tel, current_theta=0.0)
    assert res_good["is_rapid_guess"] is False
    assert res_good["signed_residual_score"] == 45.0  # 60 - 15 = +45
    assert res_good["cognitive_fluency_index"] == 1.0  # Within target time
    assert res_good["posterior_theta"] > 0.0  # Theta increases

    # 2. Fast incorrect answer (t=15s)
    bad_tel = InteractionTelemetry(
        learner_id="officer_1",
        item_id="item_002",
        selected_option="C",
        response_time_sec=15.0,
        is_correct=False,
    )
    res_bad = PsychometricEngine.evaluate_response(item, bad_tel, current_theta=0.0)
    assert res_bad["signed_residual_score"] == -45.0  # Severe penalty -45
    assert res_bad["cognitive_fluency_index"] == 0.0
    assert res_bad["posterior_theta"] < 0.0  # Theta decreases


def test_tritier_fsm_gating_and_transitions():
    """Verifies that progression requires 2 consecutive correct items AND high CFI."""
    # Streak 1: Stays EASY
    tier, streak = TriTierFSM.transition("EASY", consecutive_correct=0, is_correct=True, cfi=0.90)
    assert tier == "EASY"
    assert streak == 1

    # Streak 2 with high CFI: Advances to MEDIUM
    tier, streak = TriTierFSM.transition("EASY", consecutive_correct=1, is_correct=True, cfi=0.85)
    assert tier == "MEDIUM"
    assert streak == 0

    # Streak 2 with LOW CFI (<0.50): Blocked from advancing to HARD
    tier, streak = TriTierFSM.transition("MEDIUM", consecutive_correct=1, is_correct=True, cfi=0.30)
    assert tier == "MEDIUM"
    assert streak == 2

    # Failure at MEDIUM: Drops back to EASY
    tier, streak = TriTierFSM.transition("MEDIUM", consecutive_correct=2, is_correct=False, cfi=0.0)
    assert tier == "EASY"
    assert streak == 0


def test_fisher_information_item_selection():
    """Verifies that item selection picks the candidate maximizing Fisher Information at theta."""
    candidates = [
        {"id": "easy_item", "difficulty": -1.5, "time_limit_sec": 40.0},
        {"id": "matched_item", "difficulty": 0.1, "time_limit_sec": 60.0},
        {"id": "tough_item", "difficulty": 2.0, "time_limit_sec": 90.0},
    ]
    # At ability theta = 0.0, matched_item (difficulty 0.1) has maximum Fisher information
    chosen = TriTierFSM.select_item_by_fisher_info(candidates, theta=0.0)
    assert chosen["id"] == "matched_item"
