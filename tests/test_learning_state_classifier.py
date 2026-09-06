"""
Tests for GyanSetu Learning State Classifier.

Tests:
1. Model loading
2. Prediction
3. Probability output
4. Missing feature validation
5. Non-finite feature validation
6. Representative behavioral cases
"""

import sys
from pathlib import Path

# Add project root to Python import path so pytest
# can import the models package correctly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import numpy as np
import pandas as pd
import pytest

from models.learning_state_classifier import (
    LearningStateClassifier,
)


MODEL_PATH = PROJECT_ROOT / "models" / "learning_state_model.pkl"


@pytest.fixture
def classifier():
    """Load the trained learning-state classifier."""

    assert MODEL_PATH.exists(), (
        f"Model not found: {MODEL_PATH}"
    )

    return LearningStateClassifier.load(
        MODEL_PATH
    )


def test_model_loads(classifier):
    """Saved model should load successfully."""

    assert classifier.model is not None


def test_predict_returns_valid_state(classifier):
    """Prediction should be one of the valid states."""

    features = {
        "accuracy": 0.90,
        "average_response_time_seconds": 10.0,
        "hints_used": 1,
        "completion_rate": 0.95,
        "engagement_score": 0.90,
        "mastery_change": 0.02,
        "session_quality_score": 0.90,
    }

    result = classifier.predict_one(
        features
    )

    assert result["predicted_state"] in (
        classifier.VALID_STATES
    )


def test_predict_one_returns_probability_map(
    classifier,
):
    """Prediction should include probabilities."""

    features = {
        "accuracy": 0.90,
        "average_response_time_seconds": 10.0,
        "hints_used": 1,
        "completion_rate": 0.95,
        "engagement_score": 0.90,
        "mastery_change": 0.02,
        "session_quality_score": 0.90,
    }

    result = classifier.predict_one(
        features
    )

    assert "confidence" in result
    assert "probabilities" in result

    assert 0.0 <= result["confidence"] <= 1.0

    probabilities = result["probabilities"]

    assert set(probabilities).issubset(
        set(classifier.VALID_STATES)
    )

    assert np.isclose(
        sum(probabilities.values()),
        1.0,
        atol=0.001,
    )


def test_high_performing_session_is_mastered(
    classifier,
):
    """High-quality behavior should classify as mastered."""

    features = {
        "accuracy": 0.95,
        "average_response_time_seconds": 8.0,
        "hints_used": 0,
        "completion_rate": 1.0,
        "engagement_score": 0.95,
        "mastery_change": 0.01,
        "session_quality_score": 0.95,
    }

    result = classifier.predict_one(
        features
    )

    assert result["predicted_state"] == "mastered"


def test_struggling_session_is_struggling(
    classifier,
):
    """Poor behavioral signals should classify as struggling."""

    features = {
        "accuracy": 0.25,
        "average_response_time_seconds": 35.0,
        "hints_used": 7,
        "completion_rate": 0.50,
        "engagement_score": 0.30,
        "mastery_change": 0.01,
        "session_quality_score": 0.35,
    }

    result = classifier.predict_one(
        features
    )

    assert result["predicted_state"] == "struggling"


def test_missing_feature_is_rejected(
    classifier,
):
    """Missing required features should raise ValueError."""

    features = {
        "accuracy": 0.90,
        "average_response_time_seconds": 10.0,
        "hints_used": 1,
        "completion_rate": 0.95,
        "engagement_score": 0.90,
        "mastery_change": 0.02,
        # session_quality_score intentionally missing
    }

    df = pd.DataFrame([features])

    with pytest.raises(ValueError):
        classifier.predict(df)


def test_non_finite_feature_is_rejected(
    classifier,
):
    """NaN or infinite values should be rejected."""

    features = {
        "accuracy": np.nan,
        "average_response_time_seconds": 10.0,
        "hints_used": 1,
        "completion_rate": 0.95,
        "engagement_score": 0.90,
        "mastery_change": 0.02,
        "session_quality_score": 0.90,
    }

    df = pd.DataFrame([features])

    with pytest.raises(ValueError):
        classifier.predict(df)