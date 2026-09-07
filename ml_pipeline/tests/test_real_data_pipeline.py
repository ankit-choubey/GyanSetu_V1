"""
ml_pipeline/tests/test_real_data_pipeline.py — Automated Unit Tests for Real Learner Data Pipeline.

Tests:
1. Schema and statistical power validation through LearnerDataValidator.
2. Expectation-Maximization parameter estimation for BKT.
3. 2PL IRT item parameter calibration.
4. Spacing retention decay estimation.
5. End-to-end retraining workflow and JSON parameter export.
"""
from __future__ import annotations

import json
import os
import tempfile
import pandas as pd
import pytest

from ml_pipeline.data_validator import LearnerDataValidator
from ml_pipeline.learner_data_pipeline import (
    RealDataTrainingPipeline,
    TrainingReport,
)


@pytest.fixture
def sample_learner_df():
    """Synthetic interaction data mimicking real learner sequences."""
    rows = []
    learners = [f"officer_{i}" for i in range(1, 10)]
    items = [f"item_{j}" for j in range(1, 6)]
    competencies = ["Sampling Design", "National Accounts"]

    for l_idx, learner in enumerate(learners):
        for it_idx, item in enumerate(items):
            comp = competencies[it_idx % len(competencies)]
            # Higher index learners have higher proficiency
            is_corr = 1 if (l_idx + it_idx) % 3 != 0 else 0
            rows.append({
                "learner_id": learner,
                "item_id": item,
                "is_correct": is_corr,
                "competency": comp,
                "response_time_seconds": 25.0 + l_idx * 2,
            })
    return pd.DataFrame(rows)


def test_validator_valid_dataset(sample_learner_df):
    validator = LearnerDataValidator(min_records=10, min_learners=3, min_items=2)
    report = validator.validate_dataframe(sample_learner_df)
    assert report.is_valid is True
    assert report.valid_records == len(sample_learner_df)
    assert report.unique_learners == 9
    assert report.unique_items == 5
    assert len(report.errors) == 0


def test_validator_missing_columns():
    validator = LearnerDataValidator()
    bad_df = pd.DataFrame([{"user": "u1", "score": 1}])
    report = validator.validate_dataframe(bad_df)
    assert report.is_valid is False
    assert any("Missing mandatory columns" in e for e in report.errors)


def test_validator_too_few_records():
    validator = LearnerDataValidator(min_records=100)
    small_df = pd.DataFrame([
        {"learner_id": "u1", "item_id": "i1", "is_correct": 1},
        {"learner_id": "u2", "item_id": "i2", "is_correct": 0},
    ])
    report = validator.validate_dataframe(small_df)
    assert report.is_valid is False
    assert any("below the minimum threshold" in e for e in report.errors)


def test_bkt_em_retraining(sample_learner_df):
    pipeline = RealDataTrainingPipeline()
    bkt_params = pipeline.retrain_bkt(sample_learner_df, max_iter=15)

    assert "Sampling Design" in bkt_params
    assert "National Accounts" in bkt_params

    sd_params = bkt_params["Sampling Design"]
    assert 0.05 <= sd_params.p_init <= 0.60
    assert 0.02 <= sd_params.p_learn <= 0.40
    assert 0.05 <= sd_params.p_guess <= 0.35
    assert 0.02 <= sd_params.p_slip <= 0.25
    assert sd_params.iterations >= 1


def test_irt_2pl_retraining(sample_learner_df):
    pipeline = RealDataTrainingPipeline()
    irt_params = pipeline.retrain_irt(sample_learner_df)

    assert len(irt_params) == 5
    assert "item_1" in irt_params
    assert isinstance(irt_params["item_1"].difficulty, float)
    assert irt_params["item_1"].discrimination >= 0.40


def test_retention_retraining(sample_learner_df):
    pipeline = RealDataTrainingPipeline()
    retention_params = pipeline.retrain_retention(sample_learner_df)

    assert "Sampling Design" in retention_params
    assert retention_params["Sampling Design"].half_life_hours > 0.0
    assert retention_params["Sampling Design"].decay_rate > 0.0


def test_end_to_end_retraining_and_export(sample_learner_df):
    pipeline = RealDataTrainingPipeline(
        validator=LearnerDataValidator(min_records=10, min_learners=3, min_items=2)
    )
    report = pipeline.retrain_all(sample_learner_df)

    assert isinstance(report, TrainingReport)
    assert report.total_interactions == len(sample_learner_df)
    assert report.unique_learners == 9
    assert report.log_likelihood_improvement >= 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = os.path.join(tmpdir, "calibrated_params.json")
        pipeline.export_model_params(export_path)

        assert os.path.exists(export_path)
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "bkt_parameters" in data
        assert "irt_parameters" in data
        assert "retention_parameters" in data
        assert data["total_interactions"] == len(sample_learner_df)
