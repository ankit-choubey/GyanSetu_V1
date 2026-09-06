from app.services.learning_science_engine import (
    LearningScienceInput,
    select_pedagogical_strategy,
)


def test_required_deficit_mappings_are_deterministic():
    mappings = {
        "Recall failure": "Retrieval practice",
        "Forgetting": "Spaced repetition",
        "Confusion/Misconception": "Contrastive explanation",
        "Application gap": "Scenario/Virtual Lab",
        "Knowledge gap": "Direct instruction",
    }
    for deficit, strategy in mappings.items():
        result = select_pedagogical_strategy(LearningScienceInput(deficit))
        assert result.known is True
        assert result.strategy == strategy


def test_mapping_is_case_insensitive_and_preserves_context():
    result = select_pedagogical_strategy(
        LearningScienceInput(" recall failure ", competency_id=4, subskill_id=9)
    )
    assert result.strategy == "Retrieval practice"
    assert result.competency_id == 4
    assert result.subskill_id == 9


def test_unknown_deficit_returns_explicit_no_strategy():
    result = select_pedagogical_strategy(LearningScienceInput("Unobserved deficit"))
    assert result.known is False
    assert result.strategy is None
    assert result.deficit == "Unobserved deficit"