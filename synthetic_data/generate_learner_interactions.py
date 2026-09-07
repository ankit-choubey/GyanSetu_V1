"""
Phase 2.1 - Synthetic Learner Interaction Generator

Generates [SANDBOX DATA] learner interactions using a
Bayesian Knowledge Tracing (BKT)-style transition model.

Target:
    200 learners
    50-100 interactions per learner
    Approximately 15,000 total interactions
"""

import csv
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

QUESTION_BANK_PATH = (
    PROJECT_ROOT
    / "ml_pipeline"
    / "seed_content"
    / "question_bank.json"
)

OUTPUT_PATH = BASE_DIR / "data" / "learner_interactions.csv"


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

NUM_LEARNERS = 200
MIN_INTERACTIONS = 50
MAX_INTERACTIONS = 100

RANDOM_SEED = 42

# BKT parameters
P_INIT = 0.20
P_LEARN = 0.15
P_GUESS = 0.20
P_SLIP = 0.10

# Response-time parameters
RESPONSE_TIME_MEAN = 30.0
RESPONSE_TIME_SIGMA = 0.45

# Base probability of requesting a hint
BASE_HINT_PROBABILITY = 0.15


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def clamp(value, minimum=0.0, maximum=1.0):
    """Keep a numeric value inside [minimum, maximum]."""
    return max(minimum, min(maximum, value))


def sample_response_time(difficulty, rng):
    """
    Generate a realistic positive response time using
    a log-normal distribution.
    """

    difficulty_multiplier = {
        "easy": 0.80,
        "medium": 1.00,
        "hard": 1.35,
    }.get(difficulty.lower(), 1.0)

    seconds = rng.lognormvariate(
        math.log(RESPONSE_TIME_MEAN * difficulty_multiplier),
        RESPONSE_TIME_SIGMA,
    )

    # Keep synthetic response times within a realistic range.
    seconds = max(5.0, min(seconds, 300.0))

    return round(seconds, 2)


def choose_hint(mastery, difficulty, rng):
    """
    Learners with lower mastery and harder questions
    are more likely to request hints.
    """

    difficulty_bonus = {
        "easy": 0.00,
        "medium": 0.05,
        "hard": 0.10,
    }.get(difficulty.lower(), 0.0)

    probability = (
        BASE_HINT_PROBABILITY
        + (1.0 - mastery) * 0.25
        + difficulty_bonus
    )

    probability = clamp(
        probability,
        minimum=0.02,
        maximum=0.60,
    )

    return int(rng.random() < probability)


def classify_learning_state(mastery, recent_accuracy):
    """
    Assign a synthetic learner state.

    IMPORTANT:
    This is only a sandbox label for synthetic training data.
    It is NOT the production learning-state classifier.
    """

    if mastery >= 0.80 and recent_accuracy >= 0.70:
        return "mastered"

    if mastery < 0.35 and recent_accuracy < 0.50:
        return "struggling"

    if recent_accuracy >= 0.65:
        return "improving"

    return "needs_practice"


def bkt_update(mastery, correct, rng):
    """
    Perform one Bayesian Knowledge Tracing-style update.

    Steps:
        1. Calculate probability of the observed response.
        2. Estimate posterior knowledge probability.
        3. Apply the learning transition.
        4. Add very small stochastic variation.
    """

    # Probability of answering correctly.
    p_correct = (
        mastery * (1.0 - P_SLIP)
        + (1.0 - mastery) * P_GUESS
    )

    p_correct = clamp(p_correct)

    # Posterior probability that the learner knows the skill.
    if correct:
        numerator = mastery * (1.0 - P_SLIP)
        denominator = p_correct
    else:
        numerator = mastery * P_SLIP
        denominator = 1.0 - p_correct

    # Avoid division by zero.
    denominator = max(denominator, 1e-12)

    posterior = numerator / denominator
    posterior = clamp(posterior)

    # Learning transition.
    updated_mastery = (
        posterior
        + (1.0 - posterior) * P_LEARN
    )

    # Small noise prevents all learners from following
    # identical mastery trajectories.
    noise = rng.uniform(-0.015, 0.015)

    return clamp(updated_mastery + noise)


def simulate_response(mastery, difficulty, rng):
    """
    Simulate learner correctness.

    Harder questions reduce effective mastery slightly.
    """

    difficulty_penalty = {
        "easy": 0.00,
        "medium": 0.08,
        "hard": 0.18,
    }.get(difficulty.lower(), 0.08)

    effective_mastery = clamp(
        mastery - difficulty_penalty
    )

    probability_correct = (
        effective_mastery * (1.0 - P_SLIP)
        + (1.0 - effective_mastery) * P_GUESS
    )

    probability_correct = clamp(
        probability_correct
    )

    return int(
        rng.random() < probability_correct
    )


# -------------------------------------------------------------------
# Question bank
# -------------------------------------------------------------------

def load_question_bank():
    """Load the generated 200-question sandbox question bank."""

    if not QUESTION_BANK_PATH.exists():
        raise FileNotFoundError(
            f"Question bank not found: {QUESTION_BANK_PATH}"
        )

    with open(
        QUESTION_BANK_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    questions = data.get("questions", [])

    if len(questions) != 200:
        raise ValueError(
            f"Expected exactly 200 questions, "
            f"found {len(questions)}."
        )

    return questions


# -------------------------------------------------------------------
# Main generator
# -------------------------------------------------------------------

def generate_interactions():
    """
    Generate synthetic learner interaction records.
    """

    rng = random.Random(RANDOM_SEED)

    questions = load_question_bank()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "learner_id",
        "interaction_id",
        "item_id",
        "competency_id",
        "timestamp",
        "difficulty",
        "correct",
        "response_time_sec",
        "hint_used",
        "attempt_number",
        "mastery_before",
        "mastery_after",
        "learning_state",
        "data_source",
    ]

    total_rows = 0

    # Base date for the synthetic learning period.
    start_time = datetime(
        2026,
        1,
        1,
        9,
        0,
        0,
    )

    with open(
        OUTPUT_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        # -----------------------------------------------------------
        # Generate each learner
        # -----------------------------------------------------------

        for learner_number in range(
            1,
            NUM_LEARNERS + 1,
        ):

            learner_id = (
                f"learner_{learner_number:04d}"
            )

            # Each learner gets between 50 and 100 interactions.
            interaction_count = rng.randint(
                MIN_INTERACTIONS,
                MAX_INTERACTIONS,
            )

            # Different learners start with slightly different
            # initial knowledge levels.
            mastery = clamp(
                rng.normalvariate(
                    P_INIT,
                    0.08,
                )
            )

            recent_results = []

            # Give each learner a different starting date.
            learner_start = (
                start_time
                + timedelta(
                    days=rng.randint(0, 30)
                )
            )

            # IMPORTANT:
            # Keep a cumulative timestamp so interactions can
            # never move backwards in time.
            timestamp = learner_start

            # -------------------------------------------------------
            # Generate learner interactions
            # -------------------------------------------------------

            for attempt in range(
                1,
                interaction_count + 1,
            ):

                # Select a question randomly from the 200-item bank.
                question = rng.choice(questions)

                # Use an explicit item_id if present.
                # Otherwise create a stable ID from the question's
                # position in the question bank.
                question_index = questions.index(question)

                item_id = question.get(
                    "item_id",
                    f"item_{question_index + 1:04d}",
                )

                competency_id = question.get(
                    "competency",
                    "unknown_competency",
                )

                difficulty = question.get(
                    "difficulty",
                    "medium",
                )

                # ---------------------------------------------------
                # Mastery before response
                # ---------------------------------------------------

                mastery_before = mastery

                # ---------------------------------------------------
                # Simulate response
                # ---------------------------------------------------

                correct = simulate_response(
                    mastery,
                    difficulty,
                    rng,
                )

                # ---------------------------------------------------
                # Simulate hint usage
                # ---------------------------------------------------

                hint_used = choose_hint(
                    mastery,
                    difficulty,
                    rng,
                )

                # ---------------------------------------------------
                # Simulate response time
                # ---------------------------------------------------

                response_time = sample_response_time(
                    difficulty,
                    rng,
                )

                # Hints generally require additional time.
                if hint_used:
                    response_time = round(
                        response_time
                        * rng.uniform(
                            1.10,
                            1.35,
                        ),
                        2,
                    )

                # ---------------------------------------------------
                # BKT mastery update
                # ---------------------------------------------------

                mastery = bkt_update(
                    mastery,
                    correct,
                    rng,
                )

                # ---------------------------------------------------
                # Recent accuracy
                # ---------------------------------------------------

                recent_results.append(correct)

                # Only keep the most recent 10 responses.
                recent_results = recent_results[-10:]

                recent_accuracy = (
                    sum(recent_results)
                    / len(recent_results)
                )

                # ---------------------------------------------------
                # Learning state
                # ---------------------------------------------------

                learning_state = classify_learning_state(
                    mastery,
                    recent_accuracy,
                )

                # ---------------------------------------------------
                # Timestamp
                # ---------------------------------------------------

                if attempt == 1:
                    timestamp = learner_start
                else:
                    # Every subsequent interaction happens
                    # 5-20 minutes after the previous interaction.
                    timestamp = (
                        timestamp
                        + timedelta(
                            minutes=rng.randint(
                                5,
                                20,
                            )
                        )
                    )

                # ---------------------------------------------------
                # Interaction ID
                # ---------------------------------------------------

                interaction_id = (
                    f"{learner_id}"
                    f"_interaction_{attempt:03d}"
                )

                # ---------------------------------------------------
                # Write row
                # ---------------------------------------------------

                writer.writerow(
                    {
                        "learner_id": learner_id,
                        "interaction_id": interaction_id,
                        "item_id": item_id,
                        "competency_id": competency_id,
                        "timestamp": timestamp.isoformat(),
                        "difficulty": difficulty,
                        "correct": correct,
                        "response_time_sec": response_time,
                        "hint_used": hint_used,
                        "attempt_number": attempt,
                        "mastery_before": round(
                            mastery_before,
                            4,
                        ),
                        "mastery_after": round(
                            mastery,
                            4,
                        ),
                        "learning_state": learning_state,
                        "data_source": "[SANDBOX DATA]",
                    }
                )

                total_rows += 1

    # ----------------------------------------------------------------
    # Final summary
    # ----------------------------------------------------------------

    print("=" * 70)
    print(
        "SYNTHETIC LEARNER INTERACTION "
        "GENERATION COMPLETE"
    )
    print("=" * 70)
    print(f"Learners: {NUM_LEARNERS}")
    print(f"Interactions: {total_rows}")
    print(f"Output: {OUTPUT_PATH}")
    print("Data source: [SANDBOX DATA]")
    print("=" * 70)


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    generate_interactions()