"""
GyanSetu - Learning State Classifier

Classifies a learner's session state from behavioral signals.

Observed sandbox labels:
    mastered
    improving
    needs_practice
    struggling

DATA SOURCE:
[SANDBOX DATA] synthetic session signals.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class LearningStateClassifier:
    """Random Forest based learner-state classifier."""

    FEATURES = [
        "accuracy",
        "average_response_time_seconds",
        "hints_used",
        "completion_rate",
        "engagement_score",
        "mastery_change",
        "session_quality_score",
    ]

    LABEL_COLUMN = "learning_state"

    VALID_STATES = [
        "mastered",
        "improving",
        "needs_practice",
        "struggling",
    ]

    def __init__(self, model=None):
        self.model = model

    def _validate_features(self, df):
        """Validate classifier input features."""

        missing = set(self.FEATURES) - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required features: {sorted(missing)}"
            )

        values = df[self.FEATURES].to_numpy(dtype=float)

        if not np.isfinite(values).all():
            raise ValueError(
                "Input features contain non-finite values."
            )

    def fit(self, X, y):
        """Fit the underlying classifier."""

        self._validate_features(X)

        if len(X) != len(y):
            raise ValueError(
                "X and y must contain the same number of rows."
            )

        invalid_labels = set(y) - set(self.VALID_STATES)

        if invalid_labels:
            raise ValueError(
                f"Invalid learning states: {sorted(invalid_labels)}"
            )

        self.model.fit(
            X[self.FEATURES],
            y,
        )

        return self

    def predict(self, X):
        """Predict learning states."""

        if self.model is None:
            raise ValueError(
                "Model has not been fitted."
            )

        self._validate_features(X)

        predictions = self.model.predict(
            X[self.FEATURES]
        )

        return predictions

    def predict_proba(self, X):
        """Return class probabilities."""

        if self.model is None:
            raise ValueError(
                "Model has not been fitted."
            )

        self._validate_features(X)

        return self.model.predict_proba(
            X[self.FEATURES]
        )

    def predict_one(self, features):
        """Predict one learner session."""

        row = pd.DataFrame(
            [features]
        )

        prediction = self.predict(row)[0]
        probabilities = self.predict_proba(row)[0]

        classes = self.model.classes_

        probability_map = {
            state: round(float(prob), 4)
            for state, prob in zip(
                classes,
                probabilities,
            )
        }

        return {
            "predicted_state": str(prediction),
            "confidence": round(
                float(max(probabilities)),
                4,
            ),
            "probabilities": probability_map,
            "data_source": "[SANDBOX DATA]",
        }

    def save(self, path):
        """Save trained classifier."""

        if self.model is None:
            raise ValueError(
                "Cannot save an untrained model."
            )

        path = Path(path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            self.model,
            path,
        )

    @staticmethod
    def load(path):
        """Load a saved classifier."""

        model = joblib.load(path)

        return LearningStateClassifier(
            model=model
        )