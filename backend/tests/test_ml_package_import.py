from pathlib import Path

from app.services.scenario_ml_adapter import scenario_evaluator


def test_root_ml_pipeline_is_importable_from_backend():
    repository_root = Path(__file__).resolve().parents[2]

    assert Path(scenario_evaluator.__file__).resolve().is_relative_to(
        repository_root / "ml_pipeline"
    )