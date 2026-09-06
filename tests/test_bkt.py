"""
BKT Model Tests
GyanSetu - Phase 3.1
"""

import json
import os
import tempfile

import pandas as pd
import pytest

from models.bkt_model import BKTModel
from models.bkt_trainer import BKTTrainer


def test_default_parameters():
    model = BKTModel()

    assert model.p_init == 0.20
    assert model.p_learn == 0.15
    assert model.p_guess == 0.20
    assert model.p_slip == 0.10


def test_invalid_probability():
    with pytest.raises(ValueError):
        BKTModel(p_init=1.5)

    with pytest.raises(ValueError):
        BKTModel(p_slip=-0.1)


def test_probability_type_validation():
    with pytest.raises(TypeError):
        BKTModel(p_init="0.2")


def test_initial_knowledge():
    model = BKTModel(p_init=0.35)

    assert model.initialize_knowledge() == 0.35


def test_correct_response_probability():
    model = BKTModel()

    probability = model.predict_response_probability(0.20)

    assert abs(probability - 0.34) < 1e-9


def test_correct_response_increases_knowledge():
    model = BKTModel()

    before = 0.20
    after = model.update_after_response(before, True)

    assert after > before
    assert 0.0 <= after <= 1.0


def test_incorrect_response_decreases_knowledge():
    model = BKTModel()

    before = 0.20
    after = model.update_after_response(before, False)

    assert after < before
    assert 0.0 <= after <= 1.0


def test_invalid_response_type():
    model = BKTModel()

    with pytest.raises(TypeError):
        model.update_after_response(0.20, 1)


def test_trajectory_length():
    model = BKTModel()

    responses = [True, False, True, True, False]

    trajectory = model.trace_responses(responses)

    assert len(trajectory) == len(responses)


def test_trajectory_values_are_probabilities():
    model = BKTModel()

    trajectory = model.trace_responses(
        [True, False, True, False, True]
    )

    assert all(0.0 <= value <= 1.0 for value in trajectory)


def test_trainer_loads_dataset():
    trainer = BKTTrainer()

    df = trainer.load_data()

    assert len(df) == 14954
    assert df["learner_id"].nunique() == 200
    assert df["data_source"].eq("[SANDBOX DATA]").all()


def test_trainer_generates_same_number_of_rows():
    trainer = BKTTrainer()

    df = trainer.load_data()
    trajectories = trainer.train_trajectories(df)

    assert len(trajectories) == len(df)


def test_trainer_preserves_learners():
    trainer = BKTTrainer()

    df = trainer.load_data()
    trajectories = trainer.train_trajectories(df)

    assert trajectories["learner_id"].nunique() == 200


def test_trainer_output_schema():
    trainer = BKTTrainer()

    df = trainer.load_data()
    trajectories = trainer.train_trajectories(df)

    required_columns = {
        "learner_id",
        "competency_id",
        "timestamp",
        "correct",
        "p_known_before",
        "p_correct_before",
        "p_known_after",
        "data_source",
    }

    assert required_columns.issubset(trajectories.columns)


def test_trainer_probabilities_are_valid():
    trainer = BKTTrainer()

    df = trainer.load_data()
    trajectories = trainer.train_trajectories(df)

    for column in [
        "p_known_before",
        "p_correct_before",
        "p_known_after",
    ]:
        assert trajectories[column].between(0.0, 1.0).all()


def test_trainer_output_is_sandbox_data():
    trainer = BKTTrainer()

    df = trainer.load_data()
    trajectories = trainer.train_trajectories(df)

    assert trajectories["data_source"].eq(
        "[SANDBOX DATA]"
    ).all()


def test_config_file():
    config_path = "models/bkt_config.json"

    assert os.path.exists(config_path)

    with open(config_path, encoding="utf-8") as file:
        config = json.load(file)

    assert config["model"] == "Bayesian Knowledge Tracing"

    parameters = config["parameters"]

    for name in [
        "p_init",
        "p_learn",
        "p_guess",
        "p_slip",
    ]:
        assert 0.0 <= parameters[name] <= 1.0


def test_trajectory_file_exists():
    path = "models/bkt_learner_trajectories.csv"

    assert os.path.exists(path)

    df = pd.read_csv(path)

    assert len(df) == 14954
    assert df["data_source"].eq("[SANDBOX DATA]").all()