"""
Generate synthetic intervention outcome data for GyanSetu.

[SANDBOX DATA]
This dataset is synthetic and is intended only for development,
testing, experimentation, and model training in the sandbox.

Phase 2.3:
    200 learners
    3-5 interventions per learner
    Pre/post mastery
    Completion
    Retention outcome
"""

from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "synthetic_data" / "data"
OUTPUT_PATH = OUTPUT_DIR / "intervention_outcomes.csv"


# ============================================================
# CONFIGURATION
# ============================================================

NUM_LEARNERS = 200
MIN_INTERVENTIONS = 3
MAX_INTERVENTIONS = 5

RANDOM_SEED = 42

INTERVENTION_TYPES = [
    "targeted_practice",
    "video_lesson",
    "worked_example",
    "peer_discussion",
    "adaptive_quiz",
]

# Average effectiveness of each intervention.
# These are synthetic assumptions for sandbox experimentation.
BASE_EFFECTIVENESS = {
    "targeted_practice": 0.16,
    "video_lesson": 0.11,
    "worked_example": 0.14,
    "peer_discussion": 0.10,
    "adaptive_quiz": 0.13,
}

# Probability that a learner completes an intervention.
COMPLETION_PROBABILITY = {
    "targeted_practice": 0.84,
    "video_lesson": 0.88,
    "worked_example": 0.82,
    "peer_discussion": 0.76,
    "adaptive_quiz": 0.86,
}


# ============================================================
# SYNTHETIC LEARNER BASELINES
# ============================================================

def generate_initial_mastery(rng):
    """
    Generate an initial learner mastery level.

    Beta distribution gives more realistic values concentrated
    toward lower/middle mastery levels rather than uniform values.
    """
    return float(rng.beta(2.2, 3.0))


def choose_intervention(rng):
    """Randomly select one intervention type."""
    return str(rng.choice(INTERVENTION_TYPES))


# ============================================================
# INTERVENTION SIMULATION
# ============================================================

def simulate_intervention(
    rng,
    intervention_type,
    mastery_before,
):
    """
    Simulate one intervention.

    Returns:
        completion
        mastery_after
        improvement
        retained_mastery
        retention_rate
    """

    completion_probability = COMPLETION_PROBABILITY[intervention_type]

    completed = bool(
        rng.random() < completion_probability
    )

    # If the learner does not complete the intervention,
    # improvement should be small.
    if not completed:
        improvement = float(
            max(0.0, rng.normal(0.01, 0.015))
        )

        retention_rate = float(
            np.clip(rng.normal(0.65, 0.12), 0.30, 0.90)
        )

    else:
        base_effect = BASE_EFFECTIVENESS[intervention_type]

        # Learners with lower mastery generally have more
        # room for improvement.
        learning_room = 1.0 - mastery_before

        # Add small learner/intervention variability.
        raw_improvement = (
            base_effect
            * learning_room
            * rng.normal(1.0, 0.20)
        )

        improvement = float(
            max(0.0, raw_improvement)
        )

        retention_rate = float(
            np.clip(rng.normal(0.82, 0.08), 0.55, 0.98)
        )

    mastery_after = float(
        np.clip(
            mastery_before + improvement,
            0.0,
            1.0,
        )
    )

    # Retained mastery represents mastery remaining after
    # a short retention interval.
    retained_mastery = float(
        np.clip(
            mastery_before
            + improvement * retention_rate,
            0.0,
            1.0,
        )
    )

    return (
        completed,
        mastery_after,
        improvement,
        retained_mastery,
        retention_rate,
    )


# ============================================================
# DATA GENERATION
# ============================================================

def generate_intervention_dataset():
    """Generate the complete synthetic intervention dataset."""

    rng = np.random.default_rng(RANDOM_SEED)

    rows = []

    print("=" * 70)
    print("GENERATING SYNTHETIC INTERVENTION OUTCOME DATA")
    print("=" * 70)
    print(f"Learners: {NUM_LEARNERS}")
    print(
        f"Interventions per learner: "
        f"{MIN_INTERVENTIONS}-{MAX_INTERVENTIONS}"
    )
    print("=" * 70)

    for learner_number in range(1, NUM_LEARNERS + 1):

        learner_id = f"learner_{learner_number:04d}"

        # Each learner receives 3-5 interventions.
        num_interventions = int(
            rng.integers(
                MIN_INTERVENTIONS,
                MAX_INTERVENTIONS + 1,
            )
        )

        # Give every learner a starting mastery.
        mastery = generate_initial_mastery(rng)

        learner_start = datetime(
            2026,
            1,
            1,
            9,
            0,
        )

        timestamp = learner_start

        for intervention_number in range(
            1,
            num_interventions + 1,
        ):

            # Keep intervention timestamps increasing.
            if intervention_number > 1:
                timestamp += timedelta(
                    days=int(rng.integers(2, 8))
                )

            intervention_id = (
                f"intervention_{learner_number:04d}_"
                f"{intervention_number:02d}"
            )

            intervention_type = choose_intervention(rng)

            mastery_before = mastery

            (
                completed,
                mastery_after,
                improvement,
                retained_mastery,
                retention_rate,
            ) = simulate_intervention(
                rng=rng,
                intervention_type=intervention_type,
                mastery_before=mastery_before,
            )

            # Retention outcome:
            # retained if at least 70% of the intervention
            # improvement remains after the retention interval.
            if improvement > 0:
                retention_ratio = (
                    retained_mastery - mastery_before
                ) / improvement
            else:
                retention_ratio = retention_rate

            retention_success = bool(
                retention_ratio >= 0.70
            )

            rows.append(
                {
                    "learner_id": learner_id,
                    "intervention_id": intervention_id,
                    "intervention_number": intervention_number,
                    "timestamp": timestamp.isoformat(),
                    "intervention_type": intervention_type,
                    "completed": completed,
                    "mastery_before": round(
                        mastery_before,
                        4,
                    ),
                    "mastery_after": round(
                        mastery_after,
                        4,
                    ),
                    "improvement": round(
                        mastery_after - mastery_before,
                        4,
                    ),
                    "retained_mastery": round(
                        retained_mastery,
                        4,
                    ),
                    "retention_rate": round(
                        retention_rate,
                        4,
                    ),
                    "retention_success": retention_success,
                    "data_source": "[SANDBOX DATA]",
                }
            )

            # Sequential interventions operate on the updated
            # mastery level.
            mastery = mastery_after

    df = pd.DataFrame(rows)

    # ========================================================
    # VALIDATION
    # ========================================================

    expected_min_rows = (
        NUM_LEARNERS * MIN_INTERVENTIONS
    )

    expected_max_rows = (
        NUM_LEARNERS * MAX_INTERVENTIONS
    )

    if not (
        expected_min_rows
        <= len(df)
        <= expected_max_rows
    ):
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected {expected_min_rows}-"
            f"{expected_max_rows}."
        )

    if df["learner_id"].nunique() != NUM_LEARNERS:
        raise ValueError(
            "Unexpected number of learners."
        )

    if not df["intervention_type"].isin(
        INTERVENTION_TYPES
    ).all():
        raise ValueError(
            "Invalid intervention type detected."
        )

    if not df["completed"].isin(
        [True, False]
    ).all():
        raise ValueError(
            "Invalid completion values detected."
        )

    for column in [
        "mastery_before",
        "mastery_after",
        "improvement",
        "retained_mastery",
        "retention_rate",
    ]:
        if not df[column].between(
            0.0,
            1.0,
        ).all():
            raise ValueError(
                f"Invalid value in {column}."
            )

    if not df["retention_success"].isin(
        [True, False]
    ).all():
        raise ValueError(
            "Invalid retention_success values."
        )

    if not (
        df["data_source"]
        == "[SANDBOX DATA]"
    ).all():
        raise ValueError(
            "Dataset contains a non-sandbox source."
        )

    # Every intervention ID must be unique.
    if df["intervention_id"].duplicated().any():
        raise ValueError(
            "Duplicate intervention IDs detected."
        )

    # Mastery should never decrease immediately after
    # an intervention in this synthetic dataset.
    if (
        df["mastery_after"]
        < df["mastery_before"]
    ).any():
        raise ValueError(
            "Mastery decreased after intervention."
        )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("INTERVENTION DATA GENERATION COMPLETE")
    print("=" * 70)

    print(f"Learners: {df['learner_id'].nunique()}")
    print(f"Interventions: {len(df)}")
    print(
        "Average interventions per learner: "
        f"{len(df) / NUM_LEARNERS:.2f}"
    )

    print(
        "Completion rate: "
        f"{df['completed'].mean():.4f}"
    )

    print(
        "Average mastery before: "
        f"{df['mastery_before'].mean():.4f}"
    )

    print(
        "Average mastery after: "
        f"{df['mastery_after'].mean():.4f}"
    )

    print(
        "Average improvement: "
        f"{df['improvement'].mean():.4f}"
    )

    print(
        "Retention success rate: "
        f"{df['retention_success'].mean():.4f}"
    )

    print()
    print("Intervention distribution:")
    print(
        df["intervention_type"]
        .value_counts()
        .to_string()
    )

    print()
    print(f"Output: {OUTPUT_PATH}")
    print("Data source: [SANDBOX DATA]")
    print("=" * 70)

    return df


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    generate_intervention_dataset()