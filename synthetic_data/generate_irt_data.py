"""
Phase 2.2 - Synthetic 2PL IRT Dataset Generator

Generates [SANDBOX DATA] for:
    1. Learner abilities (theta)
    2. Item difficulty (b)
    3. Item discrimination (a)
    4. Learner-item response matrix

Full target:
    500 learners
    200 items
    100,000 responses

2PL IRT model:

    P(X_ij = 1) =
        1 / (1 + exp(-a_j * (theta_i - b_j)))

where:
    theta_i = learner ability
    a_j     = item discrimination
    b_j     = item difficulty
    X_ij    = observed response
"""

import csv
import json
import math
import random
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

DATA_DIR = BASE_DIR / "data"

RESPONSE_MATRIX_PATH = (
    DATA_DIR / "irt_response_matrix.csv"
)

ITEM_PARAMS_PATH = (
    DATA_DIR / "irt_item_params.csv"
)

LEARNER_ABILITIES_PATH = (
    DATA_DIR / "irt_learner_abilities.csv"
)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

NUM_LEARNERS = 500
NUM_ITEMS = 200

RANDOM_SEED = 42


# -------------------------------------------------------------------
# IRT parameter configuration
# -------------------------------------------------------------------

# Learner ability distribution.
THETA_MEAN = 0.0
THETA_STD = 1.0


# Item discrimination range.
#
# Higher values mean the item better distinguishes
# between learners of different ability.
DISCRIMINATION_MIN = 0.5
DISCRIMINATION_MAX = 2.0


# Item difficulty distribution.
#
# b < 0  -> easier item
# b = 0  -> average difficulty
# b > 0  -> harder item
DIFFICULTY_MEAN = 0.0
DIFFICULTY_STD = 1.0


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def sigmoid(value):
    """
    Numerically stable sigmoid function.

    sigmoid(x) = 1 / (1 + exp(-x))
    """

    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)

    z = math.exp(value)
    return z / (1.0 + z)


def irt_probability(theta, discrimination, difficulty):
    """
    Calculate probability of a correct response using
    the 2PL IRT model.

    P(X=1) = sigmoid(a * (theta - b))
    """

    value = discrimination * (
        theta - difficulty
    )

    return sigmoid(value)


# -------------------------------------------------------------------
# Question bank
# -------------------------------------------------------------------

def load_question_bank():
    """
    Load the existing question bank.

    For the full run:
        NUM_ITEMS = 200
        -> all 200 questions are used.

    For a small test:
        NUM_ITEMS = 10
        -> first 10 questions are used.

    The original question_bank.json is never modified.
    """

    if not QUESTION_BANK_PATH.exists():
        raise FileNotFoundError(
            f"Question bank not found: "
            f"{QUESTION_BANK_PATH}"
        )

    with open(
        QUESTION_BANK_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    questions = data.get(
        "questions",
        [],
    )

    if len(questions) < NUM_ITEMS:
        raise ValueError(
            f"Question bank contains only "
            f"{len(questions)} questions, "
            f"but {NUM_ITEMS} are required."
        )

    # Return only the requested number of questions.
    # Full run uses all 200.
    return questions[:NUM_ITEMS]


# -------------------------------------------------------------------
# Learner ability generation
# -------------------------------------------------------------------

def generate_learner_abilities(rng):
    """
    Generate one latent ability value theta
    for every learner.

    theta follows approximately:

        N(0, 1)

    Returns:
        dict:
            learner_id -> theta
    """

    abilities = {}

    for learner_number in range(
        1,
        NUM_LEARNERS + 1,
    ):

        learner_id = (
            f"learner_{learner_number:04d}"
        )

        theta = rng.normalvariate(
            THETA_MEAN,
            THETA_STD,
        )

        abilities[learner_id] = round(
            theta,
            4,
        )

    return abilities


# -------------------------------------------------------------------
# Item parameter generation
# -------------------------------------------------------------------

def generate_item_parameters(
    questions,
    rng,
):
    """
    Generate ground-truth 2PL parameters
    for every question.

    Each item receives:

        discrimination_a
        difficulty_b

    Returns:
        list of dictionaries
    """

    items = []

    for index, question in enumerate(
        questions,
        start=1,
    ):

        item_id = question.get(
            "item_id",
            f"item_{index:04d}",
        )

        discrimination = rng.uniform(
            DISCRIMINATION_MIN,
            DISCRIMINATION_MAX,
        )

        difficulty = rng.normalvariate(
            DIFFICULTY_MEAN,
            DIFFICULTY_STD,
        )

        items.append(
            {
                "item_id": item_id,
                "question_index": index,
                "difficulty_b": round(
                    difficulty,
                    4,
                ),
                "discrimination_a": round(
                    discrimination,
                    4,
                ),
                "source_difficulty": question.get(
                    "difficulty",
                    "medium",
                ),
                "competency": question.get(
                    "competency",
                    "unknown_competency",
                ),
                "data_source": "[SANDBOX DATA]",
            }
        )

    return items


# -------------------------------------------------------------------
# Response matrix generation
# -------------------------------------------------------------------

def generate_response_matrix(
    abilities,
    item_parameters,
    rng,
):
    """
    Generate one response for every
    learner-item combination.

    For each pair:

        1. Calculate P(correct)
        2. Sample Bernoulli response

    Returns:
        list of dictionaries
    """

    rows = []

    for learner_id, theta in abilities.items():

        for item in item_parameters:

            probability = irt_probability(
                theta=theta,
                discrimination=item[
                    "discrimination_a"
                ],
                difficulty=item[
                    "difficulty_b"
                ],
            )

            response = int(
                rng.random() < probability
            )

            rows.append(
                {
                    "learner_id": learner_id,
                    "item_id": item["item_id"],
                    "response": response,
                    "probability": round(
                        probability,
                        6,
                    ),
                    "data_source": "[SANDBOX DATA]",
                }
            )

    return rows


# -------------------------------------------------------------------
# Save learner abilities
# -------------------------------------------------------------------

def save_learner_abilities(
    abilities,
):
    """
    Save ground-truth learner ability values.

    This is useful when evaluating whether a later
    IRT calibration model can recover learner ability.
    """

    with open(
        LEARNER_ABILITIES_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "learner_id",
            "theta",
            "data_source",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for learner_id, theta in abilities.items():

            writer.writerow(
                {
                    "learner_id": learner_id,
                    "theta": theta,
                    "data_source": "[SANDBOX DATA]",
                }
            )


# -------------------------------------------------------------------
# Save item parameters
# -------------------------------------------------------------------

def save_item_parameters(
    item_parameters,
):
    """
    Save ground-truth item parameters.
    """

    with open(
        ITEM_PARAMS_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "item_id",
            "question_index",
            "difficulty_b",
            "discrimination_a",
            "source_difficulty",
            "competency",
            "data_source",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            item_parameters
        )


# -------------------------------------------------------------------
# Save response matrix
# -------------------------------------------------------------------

def save_response_matrix(
    rows,
):
    """
    Save learner-item responses.
    """

    with open(
        RESPONSE_MATRIX_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "learner_id",
            "item_id",
            "response",
            "probability",
            "data_source",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(rows)


# -------------------------------------------------------------------
# Dataset validation
# -------------------------------------------------------------------

def validate_generated_data(
    abilities,
    item_parameters,
    rows,
):
    """
    Perform basic structural validation before
    reporting successful generation.
    """

    expected_rows = (
        len(abilities)
        * len(item_parameters)
    )

    if len(rows) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} responses, "
            f"generated {len(rows)}."
        )

    if len(abilities) != NUM_LEARNERS:
        raise ValueError(
            f"Expected {NUM_LEARNERS} learners, "
            f"generated {len(abilities)}."
        )

    if len(item_parameters) != NUM_ITEMS:
        raise ValueError(
            f"Expected {NUM_ITEMS} items, "
            f"generated {len(item_parameters)}."
        )

    # Check response values.
    invalid_responses = [
        row["response"]
        for row in rows
        if row["response"] not in (0, 1)
    ]

    if invalid_responses:
        raise ValueError(
            "Response matrix contains values "
            "other than 0 or 1."
        )

    # Check probabilities.
    invalid_probabilities = [
        row["probability"]
        for row in rows
        if not 0.0 <= row["probability"] <= 1.0
    ]

    if invalid_probabilities:
        raise ValueError(
            "Response matrix contains invalid "
            "probabilities."
        )


# -------------------------------------------------------------------
# Main generator
# -------------------------------------------------------------------

def generate_irt_dataset():
    """
    Generate the synthetic 2PL IRT dataset.
    """

    rng = random.Random(
        RANDOM_SEED
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    questions = load_question_bank()

    print("=" * 70)
    print(
        "GENERATING SYNTHETIC 2PL IRT DATA"
    )
    print("=" * 70)

    print(
        f"Learners: {NUM_LEARNERS}"
    )

    print(
        f"Items: {NUM_ITEMS}"
    )

    print(
        f"Expected responses: "
        f"{NUM_LEARNERS * NUM_ITEMS}"
    )

    print("=" * 70)

    # ---------------------------------------------------------------
    # Generate learner abilities
    # ---------------------------------------------------------------

    abilities = (
        generate_learner_abilities(
            rng
        )
    )

    # ---------------------------------------------------------------
    # Generate item parameters
    # ---------------------------------------------------------------

    item_parameters = (
        generate_item_parameters(
            questions,
            rng,
        )
    )

    # ---------------------------------------------------------------
    # Generate responses
    # ---------------------------------------------------------------

    rows = generate_response_matrix(
        abilities,
        item_parameters,
        rng,
    )

    # ---------------------------------------------------------------
    # Validate
    # ---------------------------------------------------------------

    validate_generated_data(
        abilities,
        item_parameters,
        rows,
    )

    # ---------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------

    save_learner_abilities(
        abilities
    )

    save_item_parameters(
        item_parameters
    )

    save_response_matrix(
        rows
    )

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    correct_count = sum(
        row["response"] == 1
        for row in rows
    )

    accuracy = (
        correct_count / len(rows)
        if rows
        else 0.0
    )

    print()
    print("=" * 70)
    print(
        "2PL IRT DATA GENERATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Learners: {len(abilities)}"
    )

    print(
        f"Items: {len(item_parameters)}"
    )

    print(
        f"Responses: {len(rows)}"
    )

    print(
        f"Overall response accuracy: "
        f"{accuracy:.4f}"
    )

    print()
    print(
        f"Response matrix: "
        f"{RESPONSE_MATRIX_PATH}"
    )

    print(
        f"Item parameters: "
        f"{ITEM_PARAMS_PATH}"
    )

    print(
        f"Learner abilities: "
        f"{LEARNER_ABILITIES_PATH}"
    )

    print()
    print(
        "Data source: [SANDBOX DATA]"
    )

    print("=" * 70)


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    generate_irt_dataset()