from ml_pipeline.api_interface import recommend_learning_resources
from ml_pipeline.resource_recommender import rank_resources


RESOURCES = [
    {
        "resource_id": 1,
        "competency_id": 10,
        "subskill_id": 20,
        "availability": "AVAILABLE",
    },
    {
        "resource_id": 2,
        "competency_id": 10,
        "subskill_id": 21,
        "availability": "AVAILABLE",
    },
    {
        "resource_id": 3,
        "competency_id": None,
        "subskill_id": None,
        "availability": "AVAILABLE",
    },
    {
        "resource_id": 4,
        "competency_id": 99,
        "subskill_id": 40,
        "availability": "AVAILABLE",
    },
    {
        "resource_id": 5,
        "competency_id": 10,
        "subskill_id": 20,
        "availability": "UNAVAILABLE",
    },
    {
        "competency_id": 10,
        "subskill_id": 20,
        "availability": "AVAILABLE",
    },
]


def test_exact_subskill_match_ranks_first_with_score_one():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    assert ranked[0]["resource_id"] == 1
    assert ranked[0]["relevance_score"] == 1.0


def test_competency_only_match_scores_point_eight():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    competency_match = next(item for item in ranked if item["resource_id"] == 2)
    assert competency_match["relevance_score"] == 0.8


def test_general_resource_scores_point_four():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    general_match = next(item for item in ranked if item["resource_id"] == 3)
    assert general_match["relevance_score"] == 0.4


def test_unrelated_resource_is_excluded():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    assert 4 not in {item["resource_id"] for item in ranked}


def test_unavailable_resource_is_excluded():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    assert 5 not in {item["resource_id"] for item in ranked}


def test_ranking_order_is_subskill_then_competency_then_general():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    assert [item["resource_id"] for item in ranked] == [1, 2, 3]
    assert [item["relevance_score"] for item in ranked] == [1.0, 0.8, 0.4]


def test_missing_resource_id_is_ignored():
    ranked = rank_resources(RESOURCES, competency_id=10, subskill_id=20)

    assert all("resource_id" in item for item in ranked)
    assert len(ranked) == 3


def test_empty_resource_list_returns_empty_list():
    assert rank_resources([]) == []


def test_api_wrapper_returns_same_result_as_rank_resources():
    expected = rank_resources(
        RESOURCES,
        competency_id=10,
        subskill_id=20,
        gap_reason="low_mastery",
    )
    actual = recommend_learning_resources(
        RESOURCES,
        competency_id=10,
        subskill_id=20,
        gap_reason="low_mastery",
    )

    assert actual == expected
