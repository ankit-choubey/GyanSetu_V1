"""
ml_pipeline/psychometric_engine.py — MoSPI Time-Augmented Psychometric Engine & TriTierFSM.

Implements the mathematical specifications from 'kpi sih.docx' for the Ministry of
Statistics and Programme Implementation (MoSPI) capacity-building platform:
1. Signed Residual Time (SRT) Model (Maris & van der Maas, 2012).
2. Cognitive Fluency Index (CFI) with exponential latency dispersion.
3. Normative Rapid Guessing Threshold (RGT) (Wise & Kong, 2005).
4. Dynamic Educational Elo Parameter Calibration with decaying learning rates.
5. Tri-Tier Adaptive State Machine (TriTierFSM) with fluency threshold gating.
6. Fisher Information Item Selection for Computerized Adaptive Testing (CAT).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

DifficultyTier = Literal["EASY", "MEDIUM", "HARD"]


class ItemContext(BaseModel):
    """Contextual and psychometric parameters for an assessment item."""
    item_id: str
    competency_id: str
    subskill_id: str
    difficulty: float = 0.0  # IRT b_i parameter
    time_limit_sec: float = 60.0  # d_i hard deadline
    target_time_sec: float = 30.0  # t_target reading/solving duration
    q_attributes: List[int] = Field(default_factory=list)  # DINA Q-matrix vector


class InteractionTelemetry(BaseModel):
    """Client-reported response telemetry for an individual item interaction."""
    learner_id: str
    item_id: str
    selected_option: str
    response_time_sec: float
    is_correct: bool


class PsychometricEngine:
    """
    Core psychometric calculation engine evaluating speed, accuracy,
    latent ability trait theta, and item difficulty.
    """
    D_SCALE: float = 1.702
    K0_LEARNER: float = 24.0
    K0_ITEM: float = 8.0
    GAMMA: float = 0.05

    @classmethod
    def evaluate_response(
        cls,
        item: ItemContext,
        telemetry: InteractionTelemetry,
        current_theta: float,
        learner_interactions: int = 1,
        item_interactions: int = 1,
    ) -> Dict[str, Any]:
        """
        Processes a single item interaction and computes all time-augmented KPIs.
        """
        # 1. Normative Rapid Guessing Threshold (RGT) (Wise & Kong, 2005)
        rgt_sec = min(3.0, 0.15 * item.target_time_sec)
        is_rapid_guess = bool(telemetry.response_time_sec < rgt_sec)

        # 2. Signed Residual Time (SRT) (Maris & van der Maas, 2012)
        clamped_time = min(telemetry.response_time_sec, item.time_limit_sec)
        if telemetry.is_correct:
            raw_srt = item.time_limit_sec - clamped_time
        else:
            raw_srt = -(item.time_limit_sec - clamped_time)

        # Normalize SRT to [0.0, 1.0] interval
        norm_srt = (raw_srt + item.time_limit_sec) / (2.0 * item.time_limit_sec)
        norm_srt = float(np.clip(norm_srt, 0.0, 1.0))

        # 3. Cognitive Fluency Index (CFI)
        if telemetry.is_correct and not is_rapid_guess:
            if telemetry.response_time_sec <= item.target_time_sec:
                cfi = 1.0
            else:
                sigma_t = 0.50 * item.target_time_sec
                excess_time = telemetry.response_time_sec - item.target_time_sec
                cfi = float(np.exp(-excess_time / sigma_t))
        else:
            cfi = 0.0

        # 4. Dynamic Educational Elo Parameter Calibration
        k_learner = cls.K0_LEARNER / (1.0 + cls.GAMMA * max(1, learner_interactions))
        k_item = cls.K0_ITEM / (1.0 + cls.GAMMA * max(1, item_interactions))

        if not is_rapid_guess:
            logit = np.clip(cls.D_SCALE * (current_theta - item.difficulty), -15.0, 15.0)
            expected_outcome = float(1.0 / (1.0 + np.exp(-logit)))
            delta_theta = k_learner * (norm_srt - expected_outcome)
            delta_diff = k_item * (expected_outcome - norm_srt)
            new_theta = float(current_theta + delta_theta)
            new_difficulty = float(item.difficulty + delta_diff)
        else:
            # Rapid guesses provide no psychometric information about ability
            new_theta = float(current_theta)
            new_difficulty = float(item.difficulty)

        return {
            "is_rapid_guess": is_rapid_guess,
            "rapid_guess_threshold_sec": round(rgt_sec, 2),
            "signed_residual_score": round(float(raw_srt), 3),
            "normalized_srt": round(norm_srt, 4),
            "cognitive_fluency_index": round(cfi, 4),
            "prior_theta": round(float(current_theta), 4),
            "posterior_theta": round(new_theta, 4),
            "prior_difficulty": round(float(item.difficulty), 4),
            "posterior_difficulty": round(new_difficulty, 4),
        }


class TriTierFSM:
    """
    Finite State Machine managing adaptive progression across Easy, Medium,
    and Hard tiers with Cognitive Fluency gating.
    """

    @staticmethod
    def transition(
        current_tier: DifficultyTier,
        consecutive_correct: int,
        is_correct: bool,
        cfi: float,
    ) -> Tuple[DifficultyTier, int]:
        """
        Determines next tier and updated consecutive correct streak.
        Requires high cognitive fluency to advance to prevent lucky guess promotions.
        """
        cur = current_tier.upper()
        if is_correct:
            new_streak = consecutive_correct + 1
            if cur == "EASY" and new_streak >= 2 and cfi >= 0.60:
                return "MEDIUM", 0
            elif cur == "MEDIUM" and new_streak >= 2 and cfi >= 0.50:
                return "HARD", 0
            return current_tier, new_streak
        else:
            if cur == "HARD":
                return "MEDIUM", 0
            elif cur == "MEDIUM":
                return "EASY", 0
            return "EASY", 0

    @staticmethod
    def select_item_by_fisher_info(candidate_items: List[Dict[str, Any]], theta: float) -> Dict[str, Any]:
        """
        Selects candidate item from active tier maximizing Fisher Information at theta.
        """
        if not candidate_items:
            raise ValueError("Candidate item list cannot be empty for Fisher Information selection")

        best_item = candidate_items[0]
        max_info = -1.0
        d_scale = 1.702

        for item in candidate_items:
            deadline = float(item.get("time_limit_sec", 60.0))
            diff_raw = item.get("difficulty", 0.0)
            if isinstance(diff_raw, (int, float)):
                difficulty = float(diff_raw)
            elif isinstance(diff_raw, str):
                dl = diff_raw.strip().lower()
                if dl == "easy":
                    difficulty = -1.25
                elif dl == "medium":
                    difficulty = 0.125
                elif dl in ("hard", "tough"):
                    difficulty = 1.50
                else:
                    try:
                        difficulty = float(diff_raw)
                    except ValueError:
                        difficulty = 0.0
            else:
                difficulty = 0.0

            logit = d_scale * (theta - difficulty)
            prob = float(1.0 / (1.0 + np.exp(-np.clip(logit, -15.0, 15.0))))
            # Under SRT logistic formulation where discrimination scales with deadline:
            fisher_info = (deadline ** 2) * prob * (1.0 - prob)
            if fisher_info > max_info:
                max_info = fisher_info
                best_item = item

        return best_item
