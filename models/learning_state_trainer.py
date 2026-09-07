"""
GyanSetu - Learning State Classifier Trainer

Trains a Random Forest classifier on Phase 2.5
session signal data.

DATA SOURCE:
[SANDBOX DATA] synthetic session signals.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

try:
    from models.learning_state_classifier import LearningStateClassifier
except ModuleNotFoundError:
    from learning_state_classifier import LearningStateClassifier


DATA_PATH = Path(
    "synthetic_data/data/session_signals.csv"
)

MODEL_PATH = Path(
    "models/learning_state_model.pkl"
)

METRICS_PATH = Path(
    "models/learning_state_model_metrics.json"
)

RANDOM_STATE = 42


def load_training_data():
    """Load and validate session signal data."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required = set(
        LearningStateClassifier.FEATURES
        + [
            LearningStateClassifier.LABEL_COLUMN,
            "learner_id",
            "session_id",
            "data_source",
        ]
    )

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Training dataset is empty."
        )

    if not (
        df["data_source"] == "[SANDBOX DATA]"
    ).all():
        raise ValueError(
            "Training requires [SANDBOX DATA] rows only."
        )

    features = df[
        LearningStateClassifier.FEATURES
    ]

    values = features.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError(
            "Feature data contains non-finite values."
        )

    if features.isna().any().any():
        raise ValueError(
            "Feature data contains missing values."
        )

    labels = set(df["learning_state"])

    invalid = labels - set(
        LearningStateClassifier.VALID_STATES
    )

    if invalid:
        raise ValueError(
            f"Unexpected learning states: {sorted(invalid)}"
        )

    return df


def main():

    print("Loading session signal data...")

    df = load_training_data()

    X = df[
        LearningStateClassifier.FEATURES
    ]

    y = df[
        LearningStateClassifier.LABEL_COLUMN
    ]

    print(f"Rows: {len(df)}")
    print(
        f"Learners: {df['learner_id'].nunique()}"
    )
    print("\nClass distribution:")
    print(y.value_counts().to_string())

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=RANDOM_STATE,
            stratify=y,
        )
    )

    print(
        f"\nTraining rows: {len(X_train)}"
    )
    print(
        f"Testing rows: {len(X_test)}"
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    classifier = LearningStateClassifier(
        model=model
    )

    print("\nTraining Random Forest...")

    classifier.fit(
        X_train,
        y_train,
    )

    predictions = classifier.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
    )

    weighted_f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
    )

    labels = (
        LearningStateClassifier.VALID_STATES
    )

    report = classification_report(
        y_test,
        predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels,
    )

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )
    print(
        f"Macro F1: {macro_f1:.4f}"
    )
    print(
        f"Weighted F1: {weighted_f1:.4f}"
    )

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=labels,
            zero_division=0,
        )
    )

    print("Confusion matrix:")
    print(
        pd.DataFrame(
            matrix,
            index=labels,
            columns=labels,
        ).to_string()
    )

    importances = dict(
        zip(
            LearningStateClassifier.FEATURES,
            classifier.model.feature_importances_,
        )
    )

    importances = dict(
        sorted(
            importances.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    print("\nFeature importance:")
    for feature, importance in importances.items():
        print(
            f"  {feature}: "
            f"{importance:.4f}"
        )

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    classifier.save(
        MODEL_PATH
    )

    metrics = {
        "model": "RandomForestClassifier",
        "task": "learning_state_classification",
        "features": LearningStateClassifier.FEATURES,
        "classes": labels,
        "rows": int(len(df)),
        "learners": int(
            df["learner_id"].nunique()
        ),
        "training_rows": int(
            len(X_train)
        ),
        "testing_rows": int(
            len(X_test)
        ),
        "accuracy": round(
            float(accuracy),
            6,
        ),
        "macro_f1": round(
            float(macro_f1),
            6,
        ),
        "weighted_f1": round(
            float(weighted_f1),
            6,
        ),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "feature_importance": {
            key: round(
                float(value),
                6,
            )
            for key, value in importances.items()
        },
        "random_state": RANDOM_STATE,
        "data_source": "[SANDBOX DATA]",
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metrics,
            f,
            indent=2,
        )

    print(
        f"\nSaved model: {MODEL_PATH}"
    )

    print(
        f"Saved metrics: {METRICS_PATH}"
    )

    # Save/load reproducibility check.
    loaded = (
        LearningStateClassifier.load(
            MODEL_PATH
        )
    )

    original = classifier.predict(
        X_test.head(20)
    )

    restored = loaded.predict(
        X_test.head(20)
    )

    reproducible = bool(
        np.array_equal(
            original,
            restored,
        )
    )

    print(
        f"\nSave/load reproducibility: "
        f"{'PASS' if reproducible else 'FAIL'}"
    )

    if not reproducible:
        raise RuntimeError(
            "Model predictions changed "
            "after save/load."
        )

    # Sanity-check representative sessions.
    examples = [
        {
            "name": "High-performing session",
            "features": {
                "accuracy": 0.95,
                "average_response_time_seconds": 8.0,
                "hints_used": 0,
                "completion_rate": 1.0,
                "engagement_score": 0.95,
                "mastery_change": 0.01,
                "session_quality_score": 0.95,
            },
        },
        {
            "name": "Struggling session",
            "features": {
                "accuracy": 0.25,
                "average_response_time_seconds": 35.0,
                "hints_used": 7,
                "completion_rate": 0.50,
                "engagement_score": 0.30,
                "mastery_change": 0.01,
                "session_quality_score": 0.35,
            },
        },
    ]

    print("\nRepresentative predictions:")

    for example in examples:

        result = loaded.predict_one(
            example["features"]
        )

        print(
            f"  {example['name']}: "
            f"{result['predicted_state']} "
            f"(confidence="
            f"{result['confidence']})"
        )


if __name__ == "__main__":
    main()