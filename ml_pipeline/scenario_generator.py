"""
Scenario-based assessment generation via Groq.

The generator creates one scenario from supplied training content.
It is intentionally separated from backend/database logic.

Pipeline:
    Training Content
        ↓
    Groq Scenario Generation
        ↓
    JSON Shape Validation
        ↓
    Grounding Validation
        ↓
    Valid Scenario

Contract:
    generate_scenario(
        content,
        competency,
        subskill,
        difficulty,
        cognitive_level,
    ) -> dict

The backend owns scenario IDs, competency/subskill database validation,
user information, timestamps, and persistence.
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from ml_pipeline.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_PRIMARY,
)
from ml_pipeline.scenario_grounding_validator import (
    validate_scenario_grounding,
)


_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "scenario_prompt.txt",
)

_client = None

_ALLOWED_DIFFICULTIES = (
    "easy",
    "medium",
    "hard",
)

_ALLOWED_COGNITIVE_LEVELS = (
    "application",
    "analysis",
    "evaluation",
)

_REQUIRED_TOP_LEVEL_FIELDS = (
    "scenario",
    "expected_reasoning",
    "rubric",
    "difficulty",
    "cognitive_level",
    "source",
)

_REQUIRED_SCENARIO_FIELDS = (
    "title",
    "context",
    "context_data",
    "task",
)

_REQUIRED_TASK_FIELDS = (
    "question",
    "response_type",
    "instructions",
)


def _get_client() -> OpenAI:
    """Create the Groq client lazily so imports/tests need no API call."""
    global _client

    if _client is None:
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )

    return _client


def _load_prompt_template() -> str:
    """Load the scenario generation prompt."""
    with open(
        _PROMPT_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return file.read()


def _strip_code_fences(raw: str) -> str:
    """
    Defensively remove markdown code fences if the model ignores
    the instruction to return raw JSON.
    """
    text = raw.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def _validate_scenario_shape(
    scenario: dict,
    expected_difficulty: str,
    expected_cognitive_level: str,
) -> list[str]:
    """Return human-readable structural validation errors."""
    issues: list[str] = []

    if not isinstance(scenario, dict):
        return ["scenario response must be a JSON object"]

    # ---------------------------------------------------------
    # Top-level fields
    # ---------------------------------------------------------

    for field in _REQUIRED_TOP_LEVEL_FIELDS:
        if field not in scenario:
            issues.append(
                f"missing top-level field '{field}'"
            )

    # ---------------------------------------------------------
    # Scenario object
    # ---------------------------------------------------------

    scenario_data = scenario.get("scenario")

    if not isinstance(scenario_data, dict):
        issues.append(
            "'scenario' must be a JSON object"
        )
    else:
        for field in _REQUIRED_SCENARIO_FIELDS:
            if field not in scenario_data:
                issues.append(
                    f"missing scenario field '{field}'"
                )

        # -----------------------------------------------------
        # Task object
        # -----------------------------------------------------

        task = scenario_data.get("task")

        if not isinstance(task, dict):
            issues.append(
                "'scenario.task' must be a JSON object"
            )
        else:
            for field in _REQUIRED_TASK_FIELDS:
                if field not in task:
                    issues.append(
                        f"missing task field '{field}'"
                    )

            if task.get("response_type") != "structured_text":
                issues.append(
                    "'scenario.task.response_type' must be "
                    "'structured_text'"
                )

    # ---------------------------------------------------------
    # Expected reasoning
    # ---------------------------------------------------------

    expected_reasoning = scenario.get(
        "expected_reasoning"
    )

    if not isinstance(expected_reasoning, dict):
        issues.append(
            "'expected_reasoning' must be a JSON object"
        )
    else:
        key_points = expected_reasoning.get(
            "key_points"
        )

        if (
            not isinstance(key_points, list)
            or not key_points
        ):
            issues.append(
                "'expected_reasoning.key_points' must be "
                "a non-empty list"
            )

        reference_answer = expected_reasoning.get(
            "reference_answer"
        )

        if (
            not isinstance(reference_answer, str)
            or not reference_answer.strip()
        ):
            issues.append(
                "'expected_reasoning.reference_answer' must be "
                "a non-empty string"
            )

    # ---------------------------------------------------------
    # Rubric
    # ---------------------------------------------------------

    rubric = scenario.get("rubric")

    if not isinstance(rubric, dict):
        issues.append(
            "'rubric' must be a JSON object"
        )
    else:
        criteria = rubric.get("criteria")

        if (
            not isinstance(criteria, list)
            or not 2 <= len(criteria) <= 4
        ):
            issues.append(
                "'rubric.criteria' must contain between "
                "2 and 4 criteria"
            )
        else:
            total_score = 0

            for index, criterion in enumerate(criteria):
                if not isinstance(criterion, dict):
                    issues.append(
                        f"rubric criterion {index} must be "
                        "a JSON object"
                    )
                    continue

                for field in (
                    "criterion_id",
                    "description",
                    "max_score",
                ):
                    if field not in criterion:
                        issues.append(
                            f"rubric criterion {index} missing "
                            f"'{field}'"
                        )

                max_score = criterion.get(
                    "max_score"
                )

                if (
                    not isinstance(
                        max_score,
                        (int, float),
                    )
                    or isinstance(max_score, bool)
                    or max_score <= 0
                ):
                    issues.append(
                        f"rubric criterion {index} has "
                        "invalid max_score"
                    )
                else:
                    total_score += max_score

            if total_score != 10:
                issues.append(
                    "rubric total max_score must equal 10, "
                    f"got {total_score}"
                )

        if rubric.get("max_score") != 10:
            issues.append(
                "'rubric.max_score' must equal 10"
            )

    # ---------------------------------------------------------
    # Difficulty
    # ---------------------------------------------------------

    difficulty = scenario.get(
        "difficulty"
    )

    if difficulty not in _ALLOWED_DIFFICULTIES:
        issues.append(
            "'difficulty' must be one of "
            "easy, medium, hard"
        )

    if difficulty != expected_difficulty:
        issues.append(
            "'difficulty' does not match requested value "
            f"'{expected_difficulty}'"
        )

    # ---------------------------------------------------------
    # Cognitive level
    # ---------------------------------------------------------

    cognitive_level = scenario.get(
        "cognitive_level"
    )

    if cognitive_level not in _ALLOWED_COGNITIVE_LEVELS:
        issues.append(
            "'cognitive_level' must be one of "
            "application, analysis, evaluation"
        )

    if cognitive_level != expected_cognitive_level:
        issues.append(
            "'cognitive_level' does not match requested value "
            f"'{expected_cognitive_level}'"
        )

    # ---------------------------------------------------------
    # Source
    # ---------------------------------------------------------

    source = scenario.get("source")

    if not isinstance(source, dict):
        issues.append(
            "'source' must be a JSON object"
        )

    return issues


def parse_scenario_response(
    raw_text: str,
    difficulty: str,
    cognitive_level: str,
) -> dict:
    """
    Parse and structurally validate a raw LLM response.

    This function contains no network calls and can therefore be
    unit-tested independently.
    """
    cleaned = _strip_code_fences(
        raw_text
    )

    try:
        parsed = json.loads(cleaned)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Scenario response is not valid JSON: "
            f"{exc}\nRaw (truncated): "
            f"{cleaned[:500]!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(
            "Scenario response must be a JSON object, "
            f"got {type(parsed).__name__}"
        )

    issues = _validate_scenario_shape(
        parsed,
        expected_difficulty=difficulty,
        expected_cognitive_level=cognitive_level,
    )

    if issues:
        raise ValueError(
            "Scenario response failed shape validation:\n"
            + "\n".join(issues)
        )

    return parsed


def generate_scenario(
    content: str,
    competency: str,
    subskill: str,
    difficulty: str,
    cognitive_level: str,
) -> dict:
    """
    Generate one scenario-based assessment item.

    Args:
        content:
            Training material supplied to the model.

        competency:
            Human-readable competency being assessed.

        subskill:
            Human-readable subskill being assessed.

        difficulty:
            "easy" | "medium" | "hard"

        cognitive_level:
            "application" | "analysis" | "evaluation"

    Returns:
        A shape-validated and grounding-validated scenario dictionary.

    Raises:
        ValueError:
            If the API key is missing, inputs are invalid, or the
            model returns invalid JSON, invalid structure, or content
            containing obvious unsupported factual claims.
    """

    # ---------------------------------------------------------
    # API key
    # ---------------------------------------------------------

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set — see "
            "ENVIRONMENT_SETUP.md / ml_pipeline/.env.example"
        )

    # ---------------------------------------------------------
    # Difficulty validation
    # ---------------------------------------------------------

    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            f"Invalid difficulty '{difficulty}'. "
            f"Expected one of {_ALLOWED_DIFFICULTIES}."
        )

    # ---------------------------------------------------------
    # Cognitive level validation
    # ---------------------------------------------------------

    if cognitive_level not in _ALLOWED_COGNITIVE_LEVELS:
        raise ValueError(
            f"Invalid cognitive_level '{cognitive_level}'. "
            f"Expected one of {_ALLOWED_COGNITIVE_LEVELS}."
        )

    # ---------------------------------------------------------
    # Content validation
    # ---------------------------------------------------------

    if not content.strip():
        raise ValueError(
            "content must not be empty"
        )

    # ---------------------------------------------------------
    # Competency validation
    # ---------------------------------------------------------

    if not competency.strip():
        raise ValueError(
            "competency must not be empty"
        )

    # ---------------------------------------------------------
    # Subskill validation
    # ---------------------------------------------------------

    if not subskill.strip():
        raise ValueError(
            "subskill must not be empty"
        )

    # ---------------------------------------------------------
    # Build prompt
    # ---------------------------------------------------------

    prompt = _load_prompt_template().format(
        competency=competency,
        subskill=subskill,
        difficulty=difficulty,
        cognitive_level=cognitive_level,
        content=content,
    )

    # ---------------------------------------------------------
    # Call Groq
    # ---------------------------------------------------------

    client = _get_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content

    if not raw:
        raise ValueError(
            "Scenario model returned an empty response"
        )

    # ---------------------------------------------------------
    # Parse + structural validation
    # ---------------------------------------------------------

    parsed = parse_scenario_response(
        raw,
        difficulty=difficulty,
        cognitive_level=cognitive_level,
    )

    # ---------------------------------------------------------
    # Grounding validation
    # ---------------------------------------------------------

    grounding_issues = validate_scenario_grounding(
        parsed,
        content,
    )

    if grounding_issues:
        raise ValueError(
            "Scenario failed grounding validation:\n"
            + "\n".join(grounding_issues)
        )

    # ---------------------------------------------------------
    # Return validated scenario
    # ---------------------------------------------------------

    return parsed


if __name__ == "__main__":
    sample_text = (
        "Stratified sampling divides a population into "
        "homogeneous subgroups called strata before sampling "
        "independently within each stratum."
    )

    result = generate_scenario(
        sample_text,
        "Sampling Design",
        "Select appropriate sampling methods",
        "medium",
        "application",
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )