"""
Generate synthetic session-level learning signals for GyanSetu.

[SANDBOX DATA]
This dataset is synthetic and is intended only for development,
testing, experimentation, and model training in the sandbox.

Phase 2.5:
    - 2000 learner sessions
    - Four learner states:
        mastered
        improving
        needs_practice
        struggling
    - Session behavior signals for learning-state classification
"""

from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = (
    PROJECT_ROOT
    / "synthetic_data"
    / "data"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "session_signals.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

NUM_LEARNERS = 200
MIN_SESSIONS_PER_LEARNER = 8
MAX_SESSIONS_PER_LEARNER = 12

RANDOM_SEED = 42

LEARNING_STATES = [
    "mastered",
    "improving",
    "needs_practice",
    "struggling",
]


# ============================================================
# STATE BEHAVIOR PROFILES
# ============================================================

STATE_PROFILES = {
    "mastered": {
        "accuracy_mean": 0.88,
        "accuracy_std": 0.07,
        "response_time_mean": 9.0,
        "response_time_sigma": 0.25,
        "hint_probability": 0.08,
        "completion_mean": 0.95,
        "engagement_mean": 0.88,
        "mastery_change_mean": 0.015,
        "mastery_change_std": 0.015,
        "intervention_probability": 0.15,
    },
    "improving": {
        "accuracy_mean": 0.72,
        "accuracy_std": 0.10,
        "response_time_mean": 15.0,
        "response_time_sigma": 0.30,
        "hint_probability": 0.22,
        "completion_mean": 0.84,
        "engagement_mean": 0.78,
        "mastery_change_mean": 0.045,
        "mastery_change_std": 0.025,
        "intervention_probability": 0.35,
    },
    "needs_practice": {
        "accuracy_mean": 0.55,
        "accuracy_std": 0.11,
        "response_time_mean": 21.0,
        "response_time_sigma": 0.32,
        "hint_probability": 0.38,
        "completion_mean": 0.70,
        "engagement_mean": 0.62,
        "mastery_change_mean": 0.020,
        "mastery_change_std": 0.025,
        "intervention_probability": 0.50,
    },
    "struggling": {
        "accuracy_mean": 0.36,
        "accuracy_std": 0.12,
        "response_time_mean": 28.0,
        "response_time_sigma": 0.35,
        "hint_probability": 0.58,
        "completion_mean": 0.55,
        "engagement_mean": 0.42,
        "mastery_change_mean": 0.005,
        "mastery_change_std": 0.025,
        "intervention_probability": 0.65,
    },
}


# ============================================================
# HELPERS
# ============================================================

def clip_probability(value):
    """Keep a probability-like value within [0, 1]."""

    return float(
        np.clip(
            value,
            0.0,
            1.0,
        )
    )


def choose_initial_state(rng):
    """
    Choose a learner's initial state.

    The four classes are deliberately balanced enough to
    support later classification experiments.
    """

    return str(
        rng.choice(
            LEARNING_STATES,
            p=[
                0.25,
                0.25,
                0.25,
                0.25,
            ],
        )
    )


def transition_state(
    current_state,
    rng,
):
    """
    Produce a realistic state transition.

    Most sessions remain in the same state, while some
    learners move toward improvement or deterioration.
    """

    transitions = {
        "mastered": [
            ("mastered", 0.82),
            ("improving", 0.12),
            ("needs_practice", 0.06),
        ],
        "improving": [
            ("improving", 0.62),
            ("mastered", 0.20),
            ("needs_practice", 0.15),
            ("struggling", 0.03),
        ],
        "needs_practice": [
            ("needs_practice", 0.60),
            ("improving", 0.22),
            ("struggling", 0.15),
            ("mastered", 0.03),
        ],
        "struggling": [
            ("struggling", 0.68),
            ("needs_practice", 0.22),
            ("improving", 0.08),
            ("mastered", 0.02),
        ],
    }

    options, probabilities = zip(
        *transitions[current_state]
    )

    return str(
        rng.choice(
            options,
            p=probabilities,
        )
    )


# ============================================================
# SESSION GENERATION
# ============================================================

def generate_session_signals():
    """Generate the complete synthetic session dataset."""

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    rows = []

    print("=" * 70)
    print(
        "GENERATING SYNTHETIC SESSION SIGNAL DATA"
    )
    print("=" * 70)

    print(f"Learners: {NUM_LEARNERS}")
    print(
        f"Sessions per learner: "
        f"{MIN_SESSIONS_PER_LEARNER}-"
        f"{MAX_SESSIONS_PER_LEARNER}"
    )

    print("=" * 70)

    for learner_number in range(
        1,
        NUM_LEARNERS + 1,
    ):

        learner_id = (
            f"learner_{learner_number:04d}"
        )

        num_sessions = int(
            rng.integers(
                MIN_SESSIONS_PER_LEARNER,
                MAX_SESSIONS_PER_LEARNER + 1,
            )
        )

        current_state = choose_initial_state(
            rng
        )

        # Start sessions across a 90-day period.
        learner_start = datetime(
            2026,
            1,
            1,
            9,
            0,
        )

        timestamp = learner_start

        # Initial mastery associated with the state.
        initial_mastery_ranges = {
            "mastered": (0.80, 0.95),
            "improving": (0.45, 0.75),
            "needs_practice": (0.25, 0.55),
            "struggling": (0.05, 0.35),
        }

        low, high = initial_mastery_ranges[
            current_state
        ]

        mastery = float(
            rng.uniform(
                low,
                high,
            )
        )

        for session_number in range(
            1,
            num_sessions + 1,
        ):

            # Space sessions by 1-6 days.
            if session_number > 1:
                timestamp += timedelta(
                    days=int(
                        rng.integers(
                            1,
                            7,
                        )
                    )
                )

            profile = STATE_PROFILES[
                current_state
            ]

            session_id = (
                f"session_{learner_number:04d}_"
                f"{session_number:02d}"
            )

            # ------------------------------------------------
            # Session duration
            # ------------------------------------------------

            duration_minutes = float(
                np.clip(
                    rng.lognormal(
                        mean=np.log(
                            {
                                "mastered": 18,
                                "improving": 25,
                                "needs_practice": 30,
                                "struggling": 22,
                            }[
                                current_state
                            ]
                        ),
                        sigma=0.35,
                    ),
                    5,
                    90,
                )
            )

            # ------------------------------------------------
            # Questions attempted
            # ------------------------------------------------

            questions_attempted = int(
                np.clip(
                    rng.poisson(
                        {
                            "mastered": 16,
                            "improving": 14,
                            "needs_practice": 12,
                            "struggling": 9,
                        }[
                            current_state
                        ]
                    ),
                    3,
                    40,
                )
            )

            # ------------------------------------------------
            # Accuracy
            # ------------------------------------------------

            accuracy = clip_probability(
                rng.normal(
                    profile["accuracy_mean"],
                    profile["accuracy_std"],
                )
            )

            correct_answers = int(
                np.clip(
                    round(
                        accuracy
                        * questions_attempted
                    ),
                    0,
                    questions_attempted,
                )
            )

            actual_accuracy = (
                correct_answers
                / questions_attempted
            )

            # ------------------------------------------------
            # Response time
            # ------------------------------------------------

            response_time = float(
                np.clip(
                    rng.lognormal(
                        mean=np.log(
                            profile[
                                "response_time_mean"
                            ]
                        ),
                        sigma=profile[
                            "response_time_sigma"
                        ],
                    ),
                    2,
                    120,
                )
            )

            # ------------------------------------------------
            # Hints
            # ------------------------------------------------

            hints_used = int(
                rng.binomial(
                    questions_attempted,
                    profile[
                        "hint_probability"
                    ],
                )
            )

            # ------------------------------------------------
            # Completion
            # ------------------------------------------------

            completion_rate = clip_probability(
                rng.normal(
                    profile[
                        "completion_mean"
                    ],
                    0.08,
                )
            )

            questions_completed = int(
                round(
                    completion_rate
                    * questions_attempted
                )
            )

            questions_completed = int(
                np.clip(
                    questions_completed,
                    0,
                    questions_attempted,
                )
            )

            actual_completion_rate = (
                questions_completed
                / questions_attempted
            )

            # ------------------------------------------------
            # Engagement
            # ------------------------------------------------

            engagement_score = clip_probability(
                rng.normal(
                    profile[
                        "engagement_mean"
                    ],
                    0.08,
                )
            )

            # ------------------------------------------------
            # Intervention
            # ------------------------------------------------

            intervention_received = bool(
                rng.random()
                < profile[
                    "intervention_probability"
                ]
            )

            # ------------------------------------------------
            # Mastery change
            # ------------------------------------------------

            mastery_change = float(
                rng.normal(
                    profile[
                        "mastery_change_mean"
                    ],
                    profile[
                        "mastery_change_std"
                    ],
                )
            )

            # Intervention provides additional improvement.
            if intervention_received:
                mastery_change += float(
                    rng.normal(
                        0.025,
                        0.010,
                    )
                )

            mastery_change = float(
                max(
                    0.0,
                    mastery_change,
                )
            )

            mastery_before = mastery

            mastery_after = float(
                np.clip(
                    mastery_before
                    + mastery_change,
                    0.0,
                    1.0,
                )
            )

            # ------------------------------------------------
            # Session quality score
            # ------------------------------------------------

            session_quality = float(
                np.clip(
                    (
                        0.35
                        * actual_accuracy
                        + 0.25
                        * actual_completion_rate
                        + 0.20
                        * engagement_score
                        + 0.20
                        * (1.0 - min(
                            hints_used
                            / questions_attempted,
                            1.0,
                        ))
                    ),
                    0.0,
                    1.0,
                )
            )

            # ------------------------------------------------
            # Save row
            # ------------------------------------------------

            rows.append(
                {
                    "learner_id": learner_id,
                    "session_id": session_id,
                    "session_number": session_number,
                    "timestamp": timestamp.isoformat(),
                    "learning_state": current_state,
                    "session_duration_minutes": round(
                        duration_minutes,
                        2,
                    ),
                    "questions_attempted": (
                        questions_attempted
                    ),
                    "questions_completed": (
                        questions_completed
                    ),
                    "correct_answers": (
                        correct_answers
                    ),
                    "accuracy": round(
                        actual_accuracy,
                        4,
                    ),
                    "average_response_time_seconds": (
                        round(
                            response_time,
                            2,
                        )
                    ),
                    "hints_used": hints_used,
                    "completion_rate": round(
                        actual_completion_rate,
                        4,
                    ),
                    "engagement_score": round(
                        engagement_score,
                        4,
                    ),
                    "intervention_received": (
                        intervention_received
                    ),
                    "mastery_before": round(
                        mastery_before,
                        4,
                    ),
                    "mastery_after": round(
                        mastery_after,
                        4,
                    ),
                    "mastery_change": round(
                        mastery_after
                        - mastery_before,
                        4,
                    ),
                    "session_quality_score": round(
                        session_quality,
                        4,
                    ),
                    "data_source": "[SANDBOX DATA]",
                }
            )

            # Update learner mastery.
            mastery = mastery_after

            # Transition state for next session.
            current_state = transition_state(
                current_state,
                rng,
            )

    df = pd.DataFrame(rows)

    # ========================================================
    # VALIDATION
    # ========================================================

    expected_min_rows = (
        NUM_LEARNERS
        * MIN_SESSIONS_PER_LEARNER
    )

    expected_max_rows = (
        NUM_LEARNERS
        * MAX_SESSIONS_PER_LEARNER
    )

    if not (
        expected_min_rows
        <= len(df)
        <= expected_max_rows
    ):
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected between "
            f"{expected_min_rows} and "
            f"{expected_max_rows}."
        )

    if (
        df["learner_id"].nunique()
        != NUM_LEARNERS
    ):
        raise ValueError(
            "Unexpected number of learners."
        )

    learner_session_counts = (
        df.groupby("learner_id")
        .size()
    )

    if not (
        learner_session_counts
        .between(
            MIN_SESSIONS_PER_LEARNER,
            MAX_SESSIONS_PER_LEARNER,
        )
    ).all():
        raise ValueError(
            "Learner session counts outside "
            "configured range."
        )

    if df["session_id"].duplicated().any():
        raise ValueError(
            "Duplicate session IDs detected."
        )

    if not df["learning_state"].isin(
        LEARNING_STATES
    ).all():
        raise ValueError(
            "Invalid learning state detected."
        )

    probability_columns = [
        "accuracy",
        "completion_rate",
        "engagement_score",
        "session_quality_score",
    ]

    for column in probability_columns:
        if not df[column].between(
            0.0,
            1.0,
        ).all():
            raise ValueError(
                f"{column} outside [0, 1]."
            )

    if (
        df["questions_attempted"] < 1
    ).any():
        raise ValueError(
            "Invalid question count."
        )

    if (
        df["questions_completed"]
        > df["questions_attempted"]
    ).any():
        raise ValueError(
            "Questions completed exceed "
            "questions attempted."
        )

    if (
        df["correct_answers"]
        > df["questions_attempted"]
    ).any():
        raise ValueError(
            "Correct answers exceed "
            "questions attempted."
        )

    if (
        df["hints_used"]
        > df["questions_attempted"]
    ).any():
        raise ValueError(
            "Hints used exceed questions attempted."
        )

    if (
        df["session_duration_minutes"]
        <= 0
    ).any():
        raise ValueError(
            "Invalid session duration."
        )

    if (
        df["average_response_time_seconds"]
        <= 0
    ).any():
        raise ValueError(
            "Invalid response time."
        )

    if not df["mastery_before"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "mastery_before outside [0, 1]."
        )

    if not df["mastery_after"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "mastery_after outside [0, 1]."
        )

    if (
        df["mastery_change"] < 0
    ).any():
        raise ValueError(
            "Negative mastery change detected."
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
        "SESSION SIGNAL GENERATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Learners: "
        f"{df['learner_id'].nunique()}"
    )

    print(
        f"Sessions: {len(df)}"
    )

    print(
        "Average sessions per learner: "
        f"{len(df) / NUM_LEARNERS:.2f}"
    )

    print(
        "Average accuracy: "
        f"{df['accuracy'].mean():.4f}"
    )

    print(
        "Average response time: "
        f"{df['average_response_time_seconds'].mean():.2f}s"
    )

    print(
        "Average completion rate: "
        f"{df['completion_rate'].mean():.4f}"
    )

    print(
        "Average engagement: "
        f"{df['engagement_score'].mean():.4f}"
    )

    print(
        "Intervention rate: "
        f"{df['intervention_received'].mean():.4f}"
    )

    print()
    print("Learning-state distribution:")
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
    generate_session_signals()