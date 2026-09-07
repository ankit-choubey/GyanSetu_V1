from ml_pipeline.scenario_grounding_validator import (
    validate_scenario_grounding,
)


def valid_scenario():
    return {
        "scenario": {
            "title": "Choosing a sampling method",
            "context": (
                "Stratified sampling divides a population into "
                "homogeneous subgroups before sampling."
            ),
            "context_data": {},
            "task": {
                "question": (
                    "Explain how stratified sampling would be applied."
                ),
                "response_type": "structured_text",
                "instructions": "Justify your answer.",
            },
        },
        "expected_reasoning": {
            "key_points": [
                "Identify homogeneous subgroups.",
            ],
            "reference_answer": (
                "The population is divided into homogeneous subgroups."
            ),
        },
        "rubric": {
            "criteria": [],
            "max_score": 10,
        },
    }


def test_grounded_content_has_no_numeric_warning():
    scenario = valid_scenario()

    source = (
        "Stratified sampling divides a population into "
        "homogeneous subgroups before sampling."
    )

    issues = validate_scenario_grounding(
        scenario,
        source,
    )

    assert not any(
        "unsupported factual claim" in issue
        for issue in issues
    )


def test_unsupported_percentage_is_flagged():
    scenario = valid_scenario()

    scenario["scenario"]["context"] = (
        "The survey achieved a 95% response rate."
    )

    source = (
        "Stratified sampling divides a population into "
        "homogeneous subgroups before sampling."
    )

    issues = validate_scenario_grounding(
        scenario,
        source,
    )

    assert any(
        "95%" in issue
        for issue in issues
    )


def test_unsupported_number_of_states_is_flagged():
    scenario = valid_scenario()

    scenario["scenario"]["context"] = (
        "The survey covers three states."
    )

    source = (
        "Stratified sampling divides a population into "
        "homogeneous subgroups before sampling."
    )

    issues = validate_scenario_grounding(
        scenario,
        source,
    )

    assert any(
        "three states" in issue
        for issue in issues
    )


def test_unsupported_urban_rural_claim_is_flagged():
    scenario = valid_scenario()

    scenario["scenario"]["context"] = (
        "The population includes urban and rural households."
    )

    source = (
        "Stratified sampling divides a population into "
        "homogeneous subgroups before sampling."
    )

    issues = validate_scenario_grounding(
        scenario,
        source,
    )

    assert any(
        "urban" in issue.lower()
        for issue in issues
    )


def test_empty_source_is_rejected():
    scenario = valid_scenario()

    issues = validate_scenario_grounding(
        scenario,
        "",
    )

    assert issues == [
        "source_content must not be empty"
    ]


def test_invalid_scenario_is_rejected():
    issues = validate_scenario_grounding(
        "not a dictionary",
        "some training material",
    )

    assert issues == [
        "scenario must be a dictionary"
    ]


def test_empty_scenario_is_rejected():
    issues = validate_scenario_grounding(
        {},
        "some training material",
    )

    assert issues == [
        "scenario contains no textual content"
    ]


def test_source_number_is_not_flagged():
    scenario = valid_scenario()

    scenario["scenario"]["context"] = (
        "The survey achieved a 95% response rate."
    )

    source = (
        "The survey achieved a 95% response rate. "
        "Stratified sampling divides a population into "
        "homogeneous subgroups before sampling."
    )

    issues = validate_scenario_grounding(
        scenario,
        source,
    )

    assert not any(
        "95%" in issue
        for issue in issues
    )