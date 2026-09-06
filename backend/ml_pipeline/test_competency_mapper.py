from ml_pipeline.competency_mapper import (
    _validate_mapping_shape,
    parse_competency_response,
    map_competencies,
)


def run_test(name, test_function):
    try:
        test_function()
        print(f"PASS: {name}")
    except Exception as e:
        print(f"FAIL: {name} -> {e}")


def test_valid_mapping_shape():
    mapping = {
        "concept": "FastAPI Backend Development",
        "competency": "Backend API Engineering",
        "subskills": [
            "API route design",
            "Request handling"
        ],
        "confidence": 0.95,
        "rationale": "The subskills directly support backend API development."
    }

    assert _validate_mapping_shape(mapping) is True


def test_missing_field():
    mapping = {
        "concept": "FastAPI Backend Development",
        "competency": "Backend API Engineering",
        "subskills": ["API route design"],
        "confidence": 0.95
    }

    assert _validate_mapping_shape(mapping) is False


def test_invalid_confidence():
    mapping = {
        "concept": "FastAPI Backend Development",
        "competency": "Backend API Engineering",
        "subskills": ["API route design"],
        "confidence": 1.5,
        "rationale": "Test rationale."
    }

    assert _validate_mapping_shape(mapping) is False


def test_negative_confidence():
    mapping = {
        "concept": "FastAPI Backend Development",
        "competency": "Backend API Engineering",
        "subskills": ["API route design"],
        "confidence": -0.1,
        "rationale": "Test rationale."
    }

    assert _validate_mapping_shape(mapping) is False


def test_invalid_subskills():
    mapping = {
        "concept": "FastAPI Backend Development",
        "competency": "Backend API Engineering",
        "subskills": "API route design",
        "confidence": 0.95,
        "rationale": "Test rationale."
    }

    assert _validate_mapping_shape(mapping) is False


def test_parse_valid_json():
    response = """
    [
        {
            "concept": "MQTT",
            "competency": "Real-time Data Ingestion",
            "subskills": ["Message subscription", "Payload parsing"],
            "confidence": 0.92,
            "rationale": "The subskills directly support real-time data ingestion."
        }
    ]
    """

    mappings = parse_competency_response(response)

    assert len(mappings) == 1
    assert mappings[0]["concept"] == "MQTT"
    assert mappings[0]["competency"] == "Real-time Data Ingestion"
    assert mappings[0]["confidence"] == 0.92


def test_parse_code_fenced_json():
    response = """```json
[
    {
        "concept": "JWT",
        "competency": "Secure Authentication",
        "subskills": ["Token validation"],
        "confidence": 0.90,
        "rationale": "JWT validation supports secure authentication."
    }
]
```"""

    mappings = parse_competency_response(response)

    assert len(mappings) == 1
    assert mappings[0]["concept"] == "JWT"


def test_parse_invalid_json():
    response = "This is not valid JSON"

    try:
        parse_competency_response(response)
        assert False
    except Exception:
        pass


def test_parse_non_array():
    response = """
    {
        "concept": "MQTT"
    }
    """

    try:
        parse_competency_response(response)
        assert False
    except ValueError:
        pass


def test_empty_concepts():
    try:
        map_competencies([])
        assert False
    except ValueError:
        pass


def run_tests() -> bool:
    tests = [
        ("valid mapping shape", test_valid_mapping_shape),
        ("missing field", test_missing_field),
        ("invalid confidence", test_invalid_confidence),
        ("negative confidence", test_negative_confidence),
        ("invalid subskills", test_invalid_subskills),
        ("parse valid JSON", test_parse_valid_json),
        ("parse code-fenced JSON", test_parse_code_fenced_json),
        ("parse invalid JSON", test_parse_invalid_json),
        ("parse non-array", test_parse_non_array),
        ("empty concepts", test_empty_concepts),
    ]

    passed = 0
    for name, test in tests:
        try:
            test()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name} -> {e}")

    print(f"\nCOMPETENCY MAPPER TEST SUITE: {'PASS' if passed == len(tests) else 'FAIL'} ({passed}/{len(tests)} passed)")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_tests()
    if not success:
        raise SystemExit(1)