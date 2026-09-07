"""
Retention Model

Predicts learner retention factor from temporal learning signals.

This model is trained only on sandbox-generated temporal trajectory data.
"""

import os

import joblib
import numpy as np


class RetentionModel:
    """
    Wrapper around a trained retention regression model.

    The underlying estimator predicts retention_factor
    in the range [0, 1].
    """

    FEATURES = [
        "days_since_learning",
        "mastery_before_decay",
        "decay_amount",
        "intervention_count",
        "intervention_boost",
        "mastery",
    ]

    def __init__(
        self,
        estimator=None
    ):
        self.estimator = estimator

    def _validate_features(
        self,
        X
    ):
        """
        Validate feature input.
        """

        if X is None:
            raise ValueError(
                "Feature input cannot be None."
            )

        missing = [
            feature
            for feature in self.FEATURES
            if feature not in X.columns
        ]

        if missing:
            raise ValueError(
                f"Missing retention features: {missing}"
            )

        values = X[
            self.FEATURES
        ]

        if values.isna().any().any():
            raise ValueError(
                "Retention features contain missing values."
            )

        if not np.isfinite(
            values.to_numpy(
                dtype=float
            )
        ).all():

            raise ValueError(
                "Retention features contain "
                "non-finite values."
            )

        return values

    def predict(
        self,
        X
    ):
        """
        Predict retention factor.

        Returns values clipped to [0, 1].
        """

        if self.estimator is None:
            raise RuntimeError(
                "Retention model is not trained."
            )

        features = self._validate_features(
            X
        )

        predictions = self.estimator.predict(
            features
        )

        return np.clip(
            predictions,
            0.0,
            1.0
        )

    def predict_one(
        self,
        features
    ):
        """
        Predict retention for one learner state.

        features should be a dictionary containing
        all required retention features.
        """

        import pandas as pd

        frame = pd.DataFrame(
            [features]
        )

        return float(
            self.predict(frame)[0]
        )

    def save(
        self,
        path
    ):
        """
        Save the trained model.
        """

        if self.estimator is None:
            raise RuntimeError(
                "Cannot save an untrained retention model."
            )

        os.makedirs(
            os.path.dirname(
                os.path.abspath(path)
            ),
            exist_ok=True
        )

        joblib.dump(
            self,
            path
        )

    @staticmethod
    def load(
        path
    ):
        """
        Load a saved retention model.
        """

        if not os.path.exists(
            path
        ):
            raise FileNotFoundError(
                f"Retention model not found: {path}"
            )

        model = joblib.load(
            path
        )

        if not isinstance(
            model,
            RetentionModel
        ):
            raise TypeError(
                "Loaded object is not a RetentionModel."
            )

        return model