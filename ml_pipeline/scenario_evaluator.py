"""
Scenario-based assessment evaluation via Groq.

The evaluator scores a learner response against the scenario's rubric
and expected reasoning.

Contract:
    evaluate_scenario(
        scenario,
        task,
        expected_reasoning,
        rubric,
        learner_response,
    ) -> dict

The evaluator does not write to the backend database. The backend is
responsible for converting the evaluation result into Evidence.
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


_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "scenario_evaluator_prompt.txt",
)

_client = None

_ALLOWED_RESULTS = (
    "met",
    "partially_met",
    "not_met",
)

_ALLOWED_OVERALL_RESULTS = (
    "correct",
    "partially_correct",
    "incorrect",
)

_REQUIRED_TOP_LEVEL_FIELDS = (
    "evaluation",
    "feedback",
    "evidence",
)

_REQUIRED_EVALUATION_FIELDS = (
    "score",
    "max_score",
    "percentage",
    "criterion_results",
    "overall_result",
)

_REQUIRED_FEEDBACK_FIELDS = (
    "summary",
    "strengths",
    "areas_for_improvement",
    "recommended_next_step",
)

_REQUIRED_EVIDENCE_FIELDS = (
    "demonstrated_competency",
    "evidence_type",
    "confidence",
)

_PERCENTAGE_TOLERANCE = 1e-6


def _get_client() -> OpenAI:
    """Create the Groq client lazily."""
    global _client

    if _client is None:
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )

    return _client


def _load_prompt_template() -> str:
    """Load the evaluator prompt."""
    with open(_PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences defensively."""
    text = raw.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def _validate_evaluation_shape(
    result: dict,
) -> list[str]:
    """Return human-readable structural validation errors."""
    issues: list[str] = []

    if not isinstance(result, dict):
        return ["evaluation response must be a JSON object"]

    for field in _REQUIRED_TOP_LEVEL_FIELDS:
        if field not in result:
            issues.append(
                f"missing top-level field '{field}'"
            )

    evaluation = result.get("evaluation")

    if not isinstance(evaluation, dict):
        issues.append("'evaluation' must be a JSON object")
    else:
        for field in _REQUIRED_EVALUATION_FIELDS:
            if field not in evaluation:
                issues.append(
                    f"missing evaluation field '{field}'"
                )

        max_score = evaluation.get("max_score")
        score = evaluation.get("score")
        percentage = evaluation.get("percentage")

        if (
            not isinstance(max_score, int)
            or isinstance(max_score, bool)
            or max_score != 10
        ):
            issues.append(
                f"'evaluation.max_score' must equal 10, got {max_score}"
            )

        if not isinstance(score, int) or isinstance(score, bool):
            issues.append(
                "'evaluation.score' must be an integer"
            )
        elif not 0 <= score <= 10:
            issues.append(
                "'evaluation.score' must be between 0 and 10"
            )

        if not isinstance(percentage, (int, float)) or isinstance(
            percentage, bool
        ):
            issues.append(
                "'evaluation.percentage' must be a number"
            )
        elif not 0 <= percentage <= 100:
            issues.append(
                "'evaluation.percentage' must be between 0 and 100"
            )

        criterion_results = evaluation.get("criterion_results")

        if not isinstance(criterion_results, list) or not criterion_results:
            issues.append(
                "'evaluation.criterion_results' must be a non-empty list"
            )
        else:
            criterion_total = 0

            for index, criterion in enumerate(criterion_results):
                if not isinstance(criterion, dict):
                    issues.append(
                        f"criterion result {index} must be a JSON object"
                    )
                    continue

                for field in (
                    "criterion_id",
                    "score",
                    "max_score",
                    "result",
                    "feedback",
                ):
                    if field not in criterion:
                        issues.append(
                            f"criterion result {index} missing "
                            f"'{field}'"
                        )

                criterion_score = criterion.get("score")
                criterion_max_score = criterion.get("max_score")

                if not isinstance(
                    criterion_score,
                    int,
                ) or isinstance(criterion_score, bool):
                    issues.append(
                        f"criterion result {index} score must be an integer"
                    )
                elif criterion_score < 0:
                    issues.append(
                        f"criterion result {index} score cannot be negative"
                    )

                if not isinstance(
                    criterion_max_score,
                    int,
                ) or isinstance(criterion_max_score, bool):
                    issues.append(
                        f"criterion result {index} max_score "
                        "must be an integer"
                    )
                elif criterion_max_score <= 0:
                    issues.append(
                        f"criterion result {index} max_score "
                        "must be positive"
                    )
                else:
                    if (
                        isinstance(criterion_score, int)
                        and criterion_score > criterion_max_score
                    ):
                        issues.append(
                            f"criterion result {index} score cannot exceed "
                            "max_score"
                        )
                    elif isinstance(criterion_score, int):
                        criterion_total += criterion_score

                criterion_result = criterion.get("result")

                if criterion_result not in _ALLOWED_RESULTS:
                    issues.append(
                        f"criterion result {index} has invalid result "
                        f"'{criterion_result}'"
                    )

                if not isinstance(
                    criterion.get("feedback"),
                    str,
                ):
                    issues.append(
                        f"criterion result {index} feedback must be a string"
                    )

            if isinstance(score, int) and criterion_total != score:
                issues.append(
                    "sum of criterion scores must equal evaluation.score"
                )

        if (
            isinstance(score, int)
            and isinstance(max_score, int)
            and isinstance(percentage, (int, float))
            and not isinstance(percentage, bool)
            and abs(percentage - (score / max_score * 100))
            > _PERCENTAGE_TOLERANCE
        ):
            issues.append(
                "'evaluation.percentage' must equal score / max_score * 100"
            )

        overall_result = evaluation.get("overall_result")

        if overall_result not in _ALLOWED_OVERALL_RESULTS:
            issues.append(
                f"'evaluation.overall_result' has invalid value "
                f"'{overall_result}'"
            )

    feedback = result.get("feedback")

    if not isinstance(feedback, dict):
        issues.append("'feedback' must be a JSON object")
    else:
        for field in _REQUIRED_FEEDBACK_FIELDS:
            if field not in feedback:
                issues.append(
                    f"missing feedback field '{field}'"
                )

        for field in (
            "summary",
            "recommended_next_step",
        ):
            if field in feedback and not isinstance(
                feedback[field],
                str,
            ):
                issues.append(
                    f"feedback.{field} must be a string"
                )

        for field in (
            "strengths",
            "areas_for_improvement",
        ):
            if field in feedback and not isinstance(
                feedback[field],
                list,
            ):
                issues.append(
                    f"feedback.{field} must be a list"
                )

    evidence = result.get("evidence")

    if not isinstance(evidence, dict):
        issues.append("'evidence' must be a JSON object")
    else:
        for field in _REQUIRED_EVIDENCE_FIELDS:
            if field not in evidence:
                issues.append(
                    f"missing evidence field '{field}'"
                )

        if evidence.get("evidence_type") != "scenario_assessment":
            issues.append(
                "'evidence.evidence_type' must be "
                "'scenario_assessment'"
            )

        demonstrated = evidence.get("demonstrated_competency")

        if not isinstance(demonstrated, bool):
            issues.append(
                "'evidence.demonstrated_competency' must be boolean"
            )

        confidence = evidence.get("confidence")

        if not isinstance(confidence, (int, float)) or isinstance(
            confidence,
            bool,
        ):
            issues.append(
                "'evidence.confidence' must be a number"
            )
        elif not 0 <= confidence <= 1:
            issues.append(
                "'evidence.confidence' must be between 0 and 1"
            )

    return issues


def parse_evaluation_response(raw_text: str) -> dict:
    """
    Parse and structurally validate a raw LLM evaluation response.

    This function performs no network calls and can therefore be
    unit-tested independently.
    """
    cleaned = _strip_code_fences(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Evaluation response is not valid JSON: "
            f"{exc}\nRaw (truncated): {cleaned[:500]!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(
            "Evaluation response must be a JSON object, "
            f"got {type(parsed).__name__}"
        )

    issues = _validate_evaluation_shape(parsed)

    if issues:
        raise ValueError(
            "Evaluation response failed shape validation:\n"
            + "\n".join(issues)
        )

    return parsed


def evaluate_scenario(
    scenario: dict,
    task: dict,
    expected_reasoning: dict,
    rubric: dict,
    learner_response: str,
) -> dict:
    """
    Evaluate one learner response against a generated scenario.

    Args:
        scenario:
            Scenario content generated by scenario_generator.py.

        task:
            Task object from the generated scenario.

        expected_reasoning:
            Expected reasoning object from the generated scenario.

        rubric:
            Rubric object from the generated scenario.

        learner_response:
            Learner's submitted textual response.

    Returns:
        A shape-validated evaluation dictionary.

    Raises:
        ValueError:
            If the API key is missing, required inputs are invalid,
            or the model returns an invalid response.
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set — see "
            "ENVIRONMENT_SETUP.md / ml_pipeline/.env.example"
        )

    if not isinstance(scenario, dict):
        raise ValueError("scenario must be a dictionary")

    if not isinstance(task, dict):
        raise ValueError("task must be a dictionary")

    if not isinstance(expected_reasoning, dict):
        raise ValueError(
            "expected_reasoning must be a dictionary"
        )

    if not isinstance(rubric, dict):
        raise ValueError("rubric must be a dictionary")

    if not isinstance(learner_response, str):
        raise ValueError(
            "learner_response must be a string"
        )

    if not learner_response.strip():
        raise ValueError(
            "learner_response must not be empty"
        )

    prompt = _load_prompt_template().format(
        scenario=json.dumps(
            scenario,
            ensure_ascii=False,
        ),
        task=json.dumps(
            task,
            ensure_ascii=False,
        ),
        expected_reasoning=json.dumps(
            expected_reasoning,
            ensure_ascii=False,
        ),
        rubric=json.dumps(
            rubric,
            ensure_ascii=False,
        ),
        learner_response=learner_response,
    )

    client = _get_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content

    if not raw:
        raise ValueError(
            "Scenario evaluator returned an empty response"
        )

    return parse_evaluation_response(raw)


if __name__ == "__main__":
    sample_scenario = {
        "title": "Sampling Design Scenario",
        "context": (
            "A population is divided into homogeneous subgroups "
            "before sampling."
        ),
    }

    sample_task = {
        "question": (
            "Explain why stratified sampling is appropriate."
        ),
        "response_type": "structured_text",
        "instructions": "Justify your answer.",
    }

    sample_reasoning = {
        "key_points": [
            "Identify homogeneous subgroups",
            "Sample independently within each subgroup",
        ],
        "reference_answer": (
            "Stratified sampling divides the population into "
            "homogeneous subgroups before independent sampling."
        ),
    }

    sample_rubric = {
        "criteria": [
            {
                "criterion_id": "C1",
                "description": "Identifies the method.",
                "max_score": 4,
            },
            {
                "criterion_id": "C2",
                "description": "Explains subgroup formation.",
                "max_score": 3,
            },
            {
                "criterion_id": "C3",
                "description": "Justifies independent sampling.",
                "max_score": 3,
            },
        ],
        "max_score": 10,
    }

    result = evaluate_scenario(
        sample_scenario,
        sample_task,
        sample_reasoning,
        sample_rubric,
        "Stratified sampling is appropriate because the population "
        "can be divided into homogeneous subgroups and sampling can "
        "then be performed independently within each subgroup.",
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))