import os
import sys
import pandas as pd
import pytest

import models.retention_model as _rm
sys.modules["retention_model"] = _rm

from models.retention_model import RetentionModel


@pytest.fixture
def sample_features():
    return pd.DataFrame([
        {
            "days_since_learning": 15.0,
            "mastery_before_decay": 0.85,
            "decay_amount": 0.05,
            "intervention_count": 1.0,
            "intervention_boost": 0.10,
            "mastery": 0.80,
        }
    ])


def test_retention_model_feature_validation_rejects_missing():
    model = RetentionModel()
    bad_df = pd.DataFrame([{"days_since_learning": 10.0}])
    with pytest.raises(ValueError, match="Missing retention features"):
        model._validate_features(bad_df)


def test_retention_model_feature_validation_rejects_none():
    model = RetentionModel()
    with pytest.raises(ValueError, match="Feature input cannot be None"):
        model._validate_features(None)


def test_retention_model_loads_and_predicts(sample_features):
    artifact_path = os.path.join(os.path.dirname(__file__), "..", "models", "retention_model.pkl")
    if not os.path.exists(artifact_path):
        pytest.skip("retention_model.pkl not found")

    model = RetentionModel.load(artifact_path)
    predictions = model.predict(sample_features)

    assert len(predictions) == 1
    assert 0.0 <= predictions[0] <= 1.0


def test_retention_decay_trend():
    artifact_path = os.path.join(os.path.dirname(__file__), "..", "models", "retention_model.pkl")
    if not os.path.exists(artifact_path):
        pytest.skip("retention_model.pkl not found")

    model = RetentionModel.load(artifact_path)
    df_early = pd.DataFrame([{
        "days_since_learning": 2.0,
        "mastery_before_decay": 0.90,
        "decay_amount": 0.02,
        "intervention_count": 1.0,
        "intervention_boost": 0.10,
        "mastery": 0.88,
    }])
    df_late = pd.DataFrame([{
        "days_since_learning": 90.0,
        "mastery_before_decay": 0.90,
        "decay_amount": 0.30,
        "intervention_count": 1.0,
        "intervention_boost": 0.10,
        "mastery": 0.60,
    }])

    p_early = model.predict(df_early)[0]
    p_late = model.predict(df_late)[0]

    assert p_early > p_late
