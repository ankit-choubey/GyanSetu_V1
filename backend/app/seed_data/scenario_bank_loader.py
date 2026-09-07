from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scenario import ScenarioItem
from app.seed_data.scenario_bank import SCENARIO_BANK, ScenarioBankRecord
from app.seed_data.taxonomy_resolver import resolve_taxonomy

VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
VALID_COGNITIVE_LEVELS = frozenset({"application", "analysis", "evaluation"})
REQUIRED_RECORD_FIELDS = (
    "competency_name",
    "subskill_name",
    "scenario_output",
    "source_reference",
)
SCENARIO_FIELDS = ("title", "context", "context_data", "task")
TASK_FIELDS = ("question", "response_type", "instructions")
MAX_FIELD_LENGTHS = {
    "title": 255,
    "scenario_text": 6000,
    "context_data": 6000,
    "question": 4000,
    "instructions": 2000,
    "expected_reasoning": 6000,
    "rubric": 6000,
    "difficulty": 50,
    "cognitive_level": 50,
    "source_reference": 500,
}


def scenario_bank_fingerprint(record: ScenarioBankRecord) -> str:
    """Return a stable loader-level identity for one scenario record."""
    record = _coerce_record(record)
    scenario = record.scenario_output.get("scenario")
    task = scenario.get("task") if isinstance(scenario, Mapping) else None
    title = scenario.get("title") if isinstance(scenario, Mapping) else ""
    question = task.get("question") if isinstance(task, Mapping) else ""
    canonical = json.dumps(
        [
            record.competency_name,
            record.subskill_name,
            title,
            question,
            record.source_reference,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"gyansetu-scenario:{digest}"


def load_scenario_bank(
    db: Session,
    scenarios: Iterable[ScenarioBankRecord | Mapping[str, Any]] | None = None,
) -> int:
    inserted = 0
    seen_fingerprints: set[str] = set()
    records = SCENARIO_BANK if scenarios is None else scenarios

    for raw in records:
        record = _coerce_record(raw)
        fingerprint = scenario_bank_fingerprint(record)
        if fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)

        if db.execute(
            select(ScenarioItem.id).where(
                ScenarioItem.source_reference == record.source_reference
            )
        ).scalar_one_or_none() is not None:
            continue

        competency, subskill = resolve_taxonomy(
            db,
            record.competency_name,
            record.subskill_name,
        )
        payload = _validate_and_prepare(record)
        db.add(
            ScenarioItem(
                competency_id=competency.id,
                subskill_id=subskill.id,
                title=payload["title"],
                scenario_text=payload["scenario_text"],
                context_data=payload["context_data"],
                question=payload["question"],
                response_type=payload["response_type"],
                instructions=payload["instructions"],
                expected_reasoning=payload["expected_reasoning"],
                rubric=payload["rubric"],
                difficulty=payload["difficulty"],
                cognitive_level=payload["cognitive_level"],
                source_reference=record.source_reference,
            )
        )
        inserted += 1

    if inserted:
        db.flush()
    return inserted


def _coerce_record(
    raw: ScenarioBankRecord | Mapping[str, Any],
) -> ScenarioBankRecord:
    if isinstance(raw, ScenarioBankRecord):
        payload = {
            "competency_name": raw.competency_name,
            "subskill_name": raw.subskill_name,
            "scenario_output": raw.scenario_output,
            "source_reference": raw.source_reference,
        }
    elif isinstance(raw, Mapping):
        payload = dict(raw)
    else:
        raise ValueError(
            "Scenario-bank records must be structured mappings or "
            "ScenarioBankRecord values"
        )

    missing = [
        field
        for field in REQUIRED_RECORD_FIELDS
        if field not in payload or payload[field] is None
    ]
    if missing:
        raise ValueError(
            "Incomplete scenario-bank record; missing fields: "
            + ", ".join(missing)
        )

    return ScenarioBankRecord(
        competency_name=_required_text(payload["competency_name"], "competency_name"),
        subskill_name=_required_text(payload["subskill_name"], "subskill_name"),
        scenario_output=_required_mapping(payload["scenario_output"], "scenario_output"),
        source_reference=_required_text(payload["source_reference"], "source_reference"),
    )


def _validate_and_prepare(record: ScenarioBankRecord) -> dict[str, str]:
    output = record.scenario_output
    for field in ("scenario", "expected_reasoning", "rubric", "difficulty", "cognitive_level", "source"):
        if field not in output:
            raise ValueError(f"Scenario output missing required field: {field}")

    scenario = _required_mapping(output["scenario"], "scenario")
    for field in SCENARIO_FIELDS:
        if field not in scenario:
            raise ValueError(f"Scenario output missing scenario field: {field}")

    task = _required_mapping(scenario["task"], "scenario.task")
    for field in TASK_FIELDS:
        if field not in task:
            raise ValueError(f"Scenario output missing task field: {field}")
    if task["response_type"] != "structured_text":
        raise ValueError("Scenario response_type must be 'structured_text'")

    title = _required_text(scenario["title"], "scenario.title")
    scenario_text = _required_text(scenario["context"], "scenario.context")
    question = _required_text(task["question"], "scenario.task.question")
    instructions = _required_text(task["instructions"], "scenario.task.instructions")
    context_data = _required_mapping(scenario["context_data"], "scenario.context_data")

    expected_reasoning = _required_mapping(
        output["expected_reasoning"],
        "expected_reasoning",
    )
    key_points = expected_reasoning.get("key_points")
    if not isinstance(key_points, list) or not key_points or any(
        not isinstance(point, str) or not point.strip() for point in key_points
    ):
        raise ValueError("expected_reasoning.key_points must be a non-empty list of text")
    _required_text(expected_reasoning.get("reference_answer"), "expected_reasoning.reference_answer")

    rubric = _required_mapping(output["rubric"], "rubric")
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not 2 <= len(criteria) <= 4:
        raise ValueError("rubric.criteria must contain between 2 and 4 criteria")
    total_score = 0
    for index, criterion in enumerate(criteria):
        criterion = _required_mapping(criterion, f"rubric.criteria[{index}]")
        _required_text(criterion.get("criterion_id"), f"rubric.criteria[{index}].criterion_id")
        _required_text(criterion.get("description"), f"rubric.criteria[{index}].description")
        max_score = criterion.get("max_score")
        if isinstance(max_score, bool) or not isinstance(max_score, (int, float)) or max_score <= 0:
            raise ValueError(f"rubric.criteria[{index}].max_score must be positive")
        total_score += max_score
    if rubric.get("max_score") != 10 or total_score != 10:
        raise ValueError("rubric max_score and criterion total must equal 10")

    difficulty = output["difficulty"]
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty '{difficulty}'")
    cognitive_level = output["cognitive_level"]
    if cognitive_level not in VALID_COGNITIVE_LEVELS:
        raise ValueError(f"Invalid cognitive_level '{cognitive_level}'")
    _required_mapping(output["source"], "source")

    serialized = {
        "title": title,
        "scenario_text": scenario_text,
        "context_data": _serialize(context_data, "context_data"),
        "question": question,
        "response_type": "structured_text",
        "instructions": instructions,
        "expected_reasoning": _serialize(expected_reasoning, "expected_reasoning"),
        "rubric": _serialize(rubric, "rubric"),
        "difficulty": difficulty,
        "cognitive_level": cognitive_level,
        "source_reference": record.source_reference,
    }
    for field, maximum in MAX_FIELD_LENGTHS.items():
        if len(serialized[field]) > maximum:
            raise ValueError(f"Scenario field '{field}' exceeds maximum length {maximum}")
    return serialized


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Scenario field '{field_name}' must be non-empty text")
    return value.strip()


def _required_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Scenario field '{field_name}' must be an object")
    return value


def _serialize(value: Mapping[str, Any], field_name: str) -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Scenario field '{field_name}' is not JSON serializable") from exc