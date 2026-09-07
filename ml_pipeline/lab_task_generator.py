"""
ml_pipeline/lab_task_generator.py — Hands-on Statistical Practical Lab Task Generator.
GyanSetu - Phase 5.4b

Generates authentic, dataset-grounded practical data analysis exercises for statistical officers.
Supports task types: data_analysis, sampling_exercise, index_calculation, survey_design, estimation.
Includes realistic dataset schema, step-by-step instructions, expected outputs, and grading rubric.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ml_pipeline.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_PRIMARY,
)

_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "lab_task_prompt.txt",
)

SUPPORTED_TASK_TYPES = {
    "data_analysis",
    "sampling_exercise",
    "index_calculation",
    "survey_design",
    "estimation",
}

SUPPORTED_DIFFICULTIES = {"easy", "medium", "hard"}

_REQUIRED_TOP_LEVEL_FIELDS = (
    "title",
    "task_type",
    "competency",
    "subskill",
    "difficulty",
    "context",
    "dataset_description",
    "instructions",
    "deliverables",
    "expected_outputs",
    "rubric",
)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured; cannot generate lab tasks.")
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )
    return _client


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def validate_lab_task_shape(task: Dict[str, Any]) -> List[str]:
    """
    Validates the structure of a generated lab task.
    Returns a list of human-readable issues (empty if valid).
    """
    issues: List[str] = []

    if not isinstance(task, dict):
        return ["lab task response must be a JSON object"]

    for field in _REQUIRED_TOP_LEVEL_FIELDS:
        if field not in task:
            issues.append(f"missing required field '{field}'")

    if issues:
        return issues

    if task.get("task_type") not in SUPPORTED_TASK_TYPES:
        issues.append(f"invalid task_type '{task.get('task_type')}'; must be one of {sorted(SUPPORTED_TASK_TYPES)}")

    if task.get("difficulty") not in SUPPORTED_DIFFICULTIES:
        issues.append(f"invalid difficulty '{task.get('difficulty')}'; must be one of {sorted(SUPPORTED_DIFFICULTIES)}")

    ds = task.get("dataset_description")
    if not isinstance(ds, dict):
        issues.append("dataset_description must be a dictionary")
    else:
        if not ds.get("columns") or not isinstance(ds.get("columns"), list):
            issues.append("dataset_description must have a non-empty 'columns' list")

    instr = task.get("instructions")
    if not isinstance(instr, list) or len(instr) == 0:
        issues.append("instructions must be a non-empty list of steps")

    deliv = task.get("deliverables")
    if not isinstance(deliv, list) or len(deliv) == 0:
        issues.append("deliverables must be a non-empty list")

    exp = task.get("expected_outputs")
    if not isinstance(exp, dict):
        issues.append("expected_outputs must be a dictionary")

    rubric = task.get("rubric")
    if not isinstance(rubric, dict):
        issues.append("rubric must be a dictionary")
    else:
        max_score = rubric.get("max_score")
        if not isinstance(max_score, int) or isinstance(max_score, bool) or max_score <= 0:
            issues.append("rubric.max_score must be a positive integer")
        criteria = rubric.get("criteria")
        if not isinstance(criteria, list) or len(criteria) == 0:
            issues.append("rubric.criteria must be a non-empty list")
        else:
            total_crit = 0
            for idx, c in enumerate(criteria):
                if not isinstance(c, dict):
                    issues.append(f"rubric criterion {idx} must be a dictionary")
                    continue
                c_score = c.get("max_score")
                if not isinstance(c_score, int) or isinstance(c_score, bool) or c_score <= 0:
                    issues.append(f"rubric criterion {idx} max_score must be a positive integer")
                else:
                    total_crit += c_score
                if not c.get("criterion_id"):
                    issues.append(f"rubric criterion {idx} missing 'criterion_id'")
            if isinstance(max_score, int) and total_crit != max_score:
                issues.append(f"criteria max_score sum ({total_crit}) must equal rubric.max_score ({max_score})")

    return issues


def parse_lab_task_response(raw_text: str) -> Dict[str, Any]:
    """Parses raw text into validated lab task dictionary."""
    cleaned = _strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Lab task response is not valid JSON: {exc}\nRaw: {cleaned[:300]!r}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Lab task response must be a JSON object, got {type(data).__name__}")

    issues = validate_lab_task_shape(data)
    if issues:
        raise ValueError("Lab task failed shape validation:\n" + "\n".join(issues))

    return data


def generate_lab_task(
    content: str,
    competency: str,
    subskill: str,
    difficulty: str = "medium",
    task_type: str = "data_analysis",
    source_id: str = "doc_source",
) -> Dict[str, Any]:
    """
    Generates a structured practical lab task grounded in source content.
    """
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content must be a non-empty string")
    if not isinstance(competency, str) or not competency.strip():
        raise ValueError("competency must be a non-empty string")
    if not isinstance(subskill, str) or not subskill.strip():
        raise ValueError("subskill must be a non-empty string")

    difficulty_clean = difficulty.lower().strip()
    if difficulty_clean not in SUPPORTED_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty '{difficulty}'; must be one of {sorted(SUPPORTED_DIFFICULTIES)}")

    task_type_clean = task_type.lower().strip()
    if task_type_clean not in SUPPORTED_TASK_TYPES:
        raise ValueError(f"Invalid task_type '{task_type}'; must be one of {sorted(SUPPORTED_TASK_TYPES)}")

    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        content=content,
        competency=competency,
        subskill=subskill,
        difficulty=difficulty_clean,
        task_type=task_type_clean,
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    raw = response.choices[0].message.content or ""
    if not raw.strip():
        raise ValueError("Lab task generator returned empty response")

    task = parse_lab_task_response(raw)
    task["task_id"] = f"lab_{uuid.uuid4().hex[:8]}"
    task["source_metadata"] = {
        "source_id": source_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return task
