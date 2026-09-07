"""
Retention Model Trainer

Trains a Random Forest regression model to predict
retention_factor from temporal learning signals.

Training data:
    synthetic_data/data/temporal_trajectories.csv

Outputs:
    models/retention_model.pkl
    models/retention_model_metrics.json

All training data must be sandbox-generated.
"""

import os
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.model_selection import train_test_split


# ============================================================
# IMPORT RETENTION MODEL
# ============================================================

try:
    from models.retention_model import RetentionModel
except ModuleNotFoundError:
    from retention_model import RetentionModel


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "synthetic_data",
    "data",
    "temporal_trajectories.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "retention_model.pkl"
)

METRICS_PATH = os.path.join(
    BASE_DIR,
    "models",
    "retention_model_metrics.json"
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "days_since_learning",
    "mastery_before_decay",
    "decay_amount",
    "intervention_count",
    "intervention_boost",
    "mastery",
]

TARGET = "retention_factor"


# ============================================================
# LOAD TRAINING DATA
# ============================================================

def load_training_data():
    """
    Load and validate temporal trajectory data.
    """

    if not os.path.exists(
        DATA_PATH
    ):
        raise FileNotFoundError(
            f"Training data not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    required_columns = (
        FEATURES
        + [
            TARGET,
            "learner_id",
            "day",
            "data_source",
        ]
    )

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # --------------------------------------------------------
    # Data source validation
    # --------------------------------------------------------

    if not (
        df["data_source"]
        == "[SANDBOX DATA]"
    ).all():

        raise ValueError(
            "Retention training requires "
            "sandbox data only."
        )

    # --------------------------------------------------------
    # Missing-value validation
    # --------------------------------------------------------

    if df[
        FEATURES + [TARGET]
    ].isna().any().any():

        raise ValueError(
            "Training data contains missing values."
        )

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    numeric_values = df[
        FEATURES + [TARGET]
    ].to_numpy(
        dtype=float
    )

    if not np.isfinite(
        numeric_values
    ).all():

        raise ValueError(
            "Training data contains "
            "non-finite values."
        )

    # --------------------------------------------------------
    # Target validation
    # --------------------------------------------------------

    if (
        (df[TARGET] < 0)
        |
        (df[TARGET] > 1)
    ).any():

        raise ValueError(
            "retention_factor must be "
            "between 0 and 1."
        )

    return df


# ============================================================
# TRAIN RETENTION MODEL
# ============================================================

def train_retention_model(
    test_size=0.2,
    random_state=42
):
    """
    Train and evaluate the retention model.
    """

    print("=" * 70)
    print("RETENTION MODEL TRAINING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_training_data()

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Learners: "
        f"{df['learner_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Features and target
    # --------------------------------------------------------

    X = df[
        FEATURES
    ]

    y = df[
        TARGET
    ]

    # --------------------------------------------------------
    # Train/test split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state
        )
    )

    print(
        f"Training rows: {len(X_train)}"
    )

    print(
        f"Testing rows: {len(X_test)}"
    )

    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    print(
        "Training Random Forest..."
    )

    estimator = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=-1
    )

    estimator.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictions = estimator.predict(
        X_test
    )

    predictions = np.clip(
        predictions,
        0.0,
        1.0
    )

    # --------------------------------------------------------
    # Evaluation metrics
    # --------------------------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    print(
        f"MAE: {mae:.6f}"
    )

    print(
        f"RMSE: {rmse:.6f}"
    )

    print(
        f"R²: {r2:.6f}"
    )

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    feature_importance = {}

    for feature, importance in zip(
        FEATURES,
        estimator.feature_importances_
    ):

        feature_importance[
            feature
        ] = float(
            importance
        )

    print(
        "Feature importance:"
    )

    for feature, importance in sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        print(
            f"  {feature}: "
            f"{importance:.4f}"
        )

    # --------------------------------------------------------
    # Wrap estimator
    # --------------------------------------------------------

    model = RetentionModel(
        estimator=estimator
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model.save(
        MODEL_PATH
    )

    print(
        f"Saved model: {MODEL_PATH}"
    )

    # --------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------

    metrics = {
        "model": "Random Forest Regressor",
        "target": TARGET,
        "features": FEATURES,
        "n_rows": int(
            len(df)
        ),
        "n_learners": int(
            df["learner_id"].nunique()
        ),
        "train_rows": int(
            len(X_train)
        ),
        "test_rows": int(
            len(X_test)
        ),
        "mae": float(
            mae
        ),
        "rmse": float(
            rmse
        ),
        "r2": float(
            r2
        ),
        "feature_importance": feature_importance,
        "data_source": "[SANDBOX DATA]"
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=2
        )

    print(
        f"Saved metrics: {METRICS_PATH}"
    )

    return model, metrics


# ============================================================
# VALIDATE SAVED MODEL
# ============================================================

def validate_saved_model():
    """
    Load the saved model and perform a prediction check.
    """

    print(
        "\nValidating saved model..."
    )

    model = RetentionModel.load(
        MODEL_PATH
    )

    sample = pd.DataFrame(
        [
            {
                "days_since_learning": 10,
                "mastery_before_decay": 0.60,
                "decay_amount": 0.04,
                "intervention_count": 1,
                "intervention_boost": 0.05,
                "mastery": 0.61,
            }
        ]
    )

    prediction = model.predict(
        sample
    )[0]

    print(
        f"Sample retention prediction: "
        f"{prediction:.4f}"
    )

    if not (
        0.0 <= prediction <= 1.0
    ):

        raise AssertionError(
            "Retention prediction is outside [0, 1]."
        )

    print(
        "Saved model validation: PASS"
    )

    return prediction


# ============================================================
# INDEPENDENT FULL-DATA VALIDATION
# ============================================================

def validate_model_on_full_dataset():
    """
    Load the saved model and run predictions on
    the complete temporal trajectory dataset.

    This does NOT retrain the model.
    """

    print(
        "\nRunning full-dataset prediction validation..."
    )

    df = load_training_data()

    model = RetentionModel.load(
        MODEL_PATH
    )

    predictions = model.predict(
        df[FEATURES]
    )

    predictions = np.asarray(
        predictions,
        dtype=float
    )

    # --------------------------------------------------------
    # Prediction validation
    # --------------------------------------------------------

    if len(predictions) != len(df):

        raise AssertionError(
            "Number of predictions does not "
            "match number of dataset rows."
        )

    if not np.isfinite(
        predictions
    ).all():

        raise AssertionError(
            "Predictions contain non-finite values."
        )

    if not (
        (predictions >= 0.0)
        &
        (predictions <= 1.0)
    ).all():

        raise AssertionError(
            "Predictions outside [0, 1]."
        )

    print(
        f"Predictions: {len(predictions)}"
    )

    print(
        f"Prediction range: "
        f"{predictions.min():.6f} "
        f"to "
        f"{predictions.max():.6f}"
    )

    print(
        f"Mean prediction: "
        f"{predictions.mean():.6f}"
    )

    print(
        "All finite: True"
    )

    print(
        "All within [0,1]: True"
    )

    print(
        "Full-dataset validation: PASS"
    )

    return predictions


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    model, metrics = (
        train_retention_model()
    )

    validate_saved_model()

    validate_model_on_full_dataset()