import os
from pathlib import Path
import pytest

from models.intervention_recommender import InterventionRecommender


@pytest.fixture
def dataset_path():
    path = Path(__file__).resolve().parent.parent / "synthetic_data" / "data" / "intervention_outcomes.csv"
    if not path.exists():
        pytest.skip(f"Dataset not found at {path}")
    return path


def test_intervention_recommender_loads_data(dataset_path):
    rec = InterventionRecommender(dataset_path)
    rec.load_data()
    assert rec.data is not None
    assert len(rec.data) > 0


def test_intervention_recommender_computes_effectiveness(dataset_path):
    rec = InterventionRecommender(dataset_path)
    df_eff = rec.fit()
    assert df_eff is not None
    assert len(df_eff) > 0
    assert "score" in df_eff.columns


def test_intervention_recommender_recommendation_ranks(dataset_path):
    rec = InterventionRecommender(dataset_path)
    res = rec.recommend(mastery=0.45)
    assert "recommendations" in res
    recs = res["recommendations"]
    assert len(recs) > 0
    scores = [r["effectiveness_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
