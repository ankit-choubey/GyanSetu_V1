"""
Generate synthetic 90-day learner mastery trajectories for GyanSetu.

[SANDBOX DATA]
This dataset is synthetic and is intended only for development,
testing, experimentation, and model training in the sandbox.

Phase 2.4:
    - 200 learners
    - 90 days per learner
    - Ebbinghaus-style mastery decay
    - Intervention-based mastery boosts
    - Retention/decay signals
"""

from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "synthetic_data"
    / "data"
    / "intervention_outcomes.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "synthetic_data"
    / "data"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "temporal_trajectories.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

NUM_LEARNERS = 200
NUM_DAYS = 90

RANDOM_SEED = 42

# Ebbinghaus-style exponential decay rate.
DECAY_RATE = 0.018

# Small daily stochastic variation.
DAILY_NOISE_STD = 0.008

# Synthetic effectiveness of each intervention type.
INTERVENTION_BOOSTS = {
    "targeted_practice": 0.10,
    "video_lesson": 0.065,
    "worked_example": 0.085,
    "peer_discussion": 0.055,
    "adaptive_quiz": 0.075,
}


# ============================================================
# INPUT LOADING
# ============================================================

def load_interventions():
    """Load and validate intervention outcomes."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Intervention dataset not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {
        "learner_id",
        "intervention_id",
        "intervention_number",
        "timestamp",
        "intervention_type",
        "completed",
        "mastery_before",
        "mastery_after",
        "improvement",
        "retained_mastery",
        "retention_rate",
        "retention_success",
        "data_source",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing intervention columns: {sorted(missing)}"
        )

    if not (df["data_source"] == "[SANDBOX DATA]").all():
        raise ValueError(
            "Intervention dataset contains non-sandbox data."
        )

    return df


# ============================================================
# INTERVENTION LOOKUP
# ============================================================

def build_intervention_lookup(df):
    """
    Build a lookup keyed by learner and calendar date.
    """

    lookup = {}

    for _, row in df.iterrows():

        learner_id = row["learner_id"]

        timestamp = pd.to_datetime(
            row["timestamp"]
        )

        date_key = timestamp.date()

        key = (
            learner_id,
            date_key,
        )

        if key not in lookup:
            lookup[key] = []

        lookup[key].append(row)

    return lookup


# ============================================================
# EBBINGHAUS DECAY
# ============================================================

def apply_decay(
    previous_mastery,
    days_since_last_learning,
):
    """
    Apply exponential Ebbinghaus-style decay.
    """

    retention_factor = np.exp(
        -DECAY_RATE * days_since_last_learning
    )

    retention_factor = float(
        np.clip(
            retention_factor,
            0.0,
            1.0,
        )
    )

    decayed_mastery = (
        previous_mastery * retention_factor
    )

    return float(
        np.clip(
            decayed_mastery,
            0.0,
            1.0,
        )
    )


# ============================================================
# INTERVENTION EFFECT
# ============================================================

def apply_intervention(
    mastery,
    intervention_rows,
    rng,
):
    """
    Apply intervention boosts to current mastery.
    """

    total_boost = 0.0

    for row in intervention_rows:

        intervention_type = row[
            "intervention_type"
        ]

        base_boost = INTERVENTION_BOOSTS.get(
            intervention_type,
            0.05,
        )

        completed = bool(
            row["completed"]
        )

        if completed:
            effectiveness = rng.normal(
                1.0,
                0.15,
            )
        else:
            effectiveness = rng.normal(
                0.20,
                0.08,
            )

        effectiveness = max(
            0.0,
            effectiveness,
        )

        learning_room = (
            1.0 - mastery
        )

        boost = (
            base_boost
            * learning_room
            * effectiveness
        )

        total_boost += boost

        mastery = float(
            np.clip(
                mastery + boost,
                0.0,
                1.0,
            )
        )

    return mastery, total_boost


# ============================================================
# LEARNING STATE
# ============================================================

def determine_learning_state(mastery):
    """Assign a simple synthetic learning state."""

    if mastery >= 0.80:
        return "mastered"

    if mastery >= 0.60:
        return "proficient"

    if mastery >= 0.40:
        return "developing"

    return "needs_practice"


# ============================================================
# TRAJECTORY GENERATION
# ============================================================

def generate_temporal_trajectories():
    """Generate 90-day mastery trajectories."""

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    interventions = load_interventions()

    learner_ids = sorted(
        interventions["learner_id"].unique()
    )

    if len(learner_ids) < NUM_LEARNERS:
        raise ValueError(
            f"Expected at least {NUM_LEARNERS} learners, "
            f"found {len(learner_ids)}."
        )

    learner_ids = learner_ids[:NUM_LEARNERS]

    intervention_lookup = build_intervention_lookup(
        interventions
    )

    rows = []

    print("=" * 70)
    print(
        "GENERATING SYNTHETIC TEMPORAL "
        "LEARNING TRAJECTORIES"
    )
    print("=" * 70)
    print(f"Learners: {NUM_LEARNERS}")
    print(f"Days per learner: {NUM_DAYS}")
    print(
        f"Expected observations: "
        f"{NUM_LEARNERS * NUM_DAYS}"
    )
    print("=" * 70)

    for learner_id in learner_ids:

        learner_interventions = interventions[
            interventions["learner_id"] == learner_id
        ]

        initial_mastery = float(
            learner_interventions.iloc[0][
                "mastery_before"
            ]
        )

        mastery = float(
            np.clip(
                initial_mastery
                + rng.normal(0.0, 0.015),
                0.0,
                1.0,
            )
        )

        start_date = datetime(
            2026,
            1,
            1,
        )

        # Day index of the most recent learning event.
        last_learning_day = 0

        for day in range(
            1,
            NUM_DAYS + 1,
        ):

            current_date = (
                start_date
                + timedelta(days=day - 1)
            )

            days_since_learning = max(
                0,
                day - last_learning_day - 1,
            )

            mastery_before_decay = mastery

            mastery = apply_decay(
                previous_mastery=mastery,
                days_since_last_learning=(
                    days_since_learning
                ),
            )

            decay_amount = (
                mastery_before_decay - mastery
            )

            intervention_rows = (
                intervention_lookup.get(
                    (
                        learner_id,
                        current_date.date(),
                    ),
                    [],
                )
            )

            intervention_count = len(
                intervention_rows
            )

            intervention_boost = 0.0

            if intervention_rows:

                mastery, intervention_boost = (
                    apply_intervention(
                        mastery=mastery,
                        intervention_rows=(
                            intervention_rows
                        ),
                        rng=rng,
                    )
                )

                last_learning_day = day

            noise = float(
                rng.normal(
                    0.0,
                    DAILY_NOISE_STD,
                )
            )

            mastery = float(
                np.clip(
                    mastery + noise,
                    0.0,
                    1.0,
                )
            )

            learning_state = (
                determine_learning_state(
                    mastery
                )
            )

            retention_factor = float(
                np.exp(
                    -DECAY_RATE
                    * days_since_learning
                )
            )

            retention_factor = float(
                np.clip(
                    retention_factor,
                    0.0,
                    1.0,
                )
            )

            rows.append(
                {
                    "learner_id": learner_id,
                    "day": day,
                    "date": (
                        current_date
                        .date()
                        .isoformat()
                    ),
                    "mastery": round(
                        mastery,
                        4,
                    ),
                    "mastery_before_decay": round(
                        mastery_before_decay,
                        4,
                    ),
                    "decay_amount": round(
                        max(
                            0.0,
                            decay_amount,
                        ),
                        4,
                    ),
                    "intervention_count": (
                        intervention_count
                    ),
                    "intervention_boost": round(
                        intervention_boost,
                        4,
                    ),
                    "days_since_learning": (
                        days_since_learning
                    ),
                    "retention_factor": round(
                        retention_factor,
                        4,
                    ),
                    "learning_state": learning_state,
                    "data_source": "[SANDBOX DATA]",
                }
            )

    df = pd.DataFrame(rows)

    # ========================================================
    # VALIDATION
    # ========================================================

    expected_rows = (
        NUM_LEARNERS * NUM_DAYS
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(df)}."
        )

    if (
        df["learner_id"].nunique()
        != NUM_LEARNERS
    ):
        raise ValueError(
            "Unexpected number of learners."
        )

    learner_day_counts = (
        df.groupby("learner_id").size()
    )

    if not (
        learner_day_counts == NUM_DAYS
    ).all():
        raise ValueError(
            "Not every learner has exactly "
            f"{NUM_DAYS} observations."
        )

    if df.duplicated(
        ["learner_id", "day"]
    ).any():
        raise ValueError(
            "Duplicate learner/day observations."
        )

    if not df["mastery"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "Mastery outside [0, 1]."
        )

    if not df["retention_factor"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "Retention factor outside [0, 1]."
        )

    if (
        df["decay_amount"] < 0
    ).any():
        raise ValueError(
            "Negative decay amount detected."
        )

    if (
        df["intervention_count"] < 0
    ).any():
        raise ValueError(
            "Negative intervention count."
        )

    if not (
        df["data_source"] == "[SANDBOX DATA]"
    ).all():
        raise ValueError(
            "Non-sandbox data detected."
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
    print(
        "TEMPORAL TRAJECTORY GENERATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Learners: "
        f"{df['learner_id'].nunique()}"
    )

    print(
        f"Observations: {len(df)}"
    )

    print(
        f"Days per learner: {NUM_DAYS}"
    )

    print(
        f"Average mastery: "
        f"{df['mastery'].mean():.4f}"
    )

    print(
        f"Average decay amount: "
        f"{df['decay_amount'].mean():.4f}"
    )

    print(
        f"Days with interventions: "
        f"{(df['intervention_count'] > 0).sum()}"
    )

    print(
        f"Average retention factor: "
        f"{df['retention_factor'].mean():.4f}"
    )

    print()
    print("Learning states:")
    print(
        df["learning_state"]
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
    generate_temporal_trajectories()