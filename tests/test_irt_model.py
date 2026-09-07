import pytest
from models.irt_model import IRT2PL


def test_irt_parameter_initialization():
    item = IRT2PL(discrimination=1.5, difficulty=0.5)
    assert item.discrimination == 1.5
    assert item.difficulty == 0.5


def test_irt_invalid_discrimination_raises():
    with pytest.raises(ValueError, match="Discrimination parameter must be greater than 0"):
        IRT2PL(discrimination=0.0)
    with pytest.raises(ValueError, match="Discrimination parameter must be greater than 0"):
        IRT2PL(discrimination=-1.0)


def test_irt_probability_at_difficulty_equals_half():
    item = IRT2PL(discrimination=1.0, difficulty=0.0)
    prob = item.probability(theta=0.0)
    assert abs(prob - 0.5) < 1e-5


def test_irt_higher_ability_yields_higher_probability():
    item = IRT2PL(discrimination=1.2, difficulty=0.0)
    p_low = item.probability(theta=-1.5)
    p_mid = item.probability(theta=0.0)
    p_high = item.probability(theta=1.5)

    assert p_low < p_mid < p_high
    assert 0.0 < p_low < 1.0
    assert 0.0 < p_high < 1.0


def test_irt_harder_item_yields_lower_probability_at_same_theta():
    item_easy = IRT2PL(discrimination=1.0, difficulty=-1.0)
    item_hard = IRT2PL(discrimination=1.0, difficulty=1.0)

    theta = 0.0
    assert item_easy.probability(theta) > item_hard.probability(theta)
