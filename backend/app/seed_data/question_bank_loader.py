from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentItem
from app.models.competency import Competency, SubSkill
from app.seed_data.question_bank import QUESTION_BANK, QuestionBankRecord

OPTION_LABELS = ("A", "B", "C", "D")
VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
SOURCE_REFERENCE_PREFIX = "gyansetu-qb:"
REQUIRED_FIELDS = (
    "competency_name",
    "subskill_name",
    "question_text",
    "options",
    "correct_option",
    "difficulty",
)


def question_bank_fingerprint(competency_name: str, subskill_name: str, question_text: str) -> str:
    canonical = "\0".join((competency_name, subskill_name, question_text))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{SOURCE_REFERENCE_PREFIX}{digest}"


def load_question_bank(
    db: Session,
    questions: Iterable[QuestionBankRecord | Mapping[str, Any]] | None = None,
) -> int:
    inserted = 0
    seen_fingerprints: set[str] = set()
    records = QUESTION_BANK if questions is None else questions
    for raw in records:
        record = _coerce_record(raw)
        competency, subskill = _resolve_taxonomy(db, record.competency_name, record.subskill_name)
        fingerprint = question_bank_fingerprint(
            record.competency_name,
            record.subskill_name,
            record.question_text,
        )
        if fingerprint in seen_fingerprints:
            continue
        existing = db.execute(
            select(AssessmentItem.id).where(
                AssessmentItem.source_reference == fingerprint,
                AssessmentItem.user_id.is_(None),
            )
        ).scalar_one_or_none()
        if existing is not None:
            seen_fingerprints.add(fingerprint)
            continue
        seen_fingerprints.add(fingerprint)
        db.add(
            AssessmentItem(
                user_id=None,
                competency_id=competency.id,
                subskill_id=subskill.id,
                question_text=record.question_text,
                options_json=_serialize_options(record.options),
                correct_option=record.correct_option,
                difficulty=record.difficulty,
                source_reference=fingerprint,
            )
        )
        inserted += 1
    if inserted:
        db.flush()
    return inserted


def _coerce_record(raw: QuestionBankRecord | Mapping[str, Any]) -> QuestionBankRecord:
    if isinstance(raw, QuestionBankRecord):
        payload = {
            "competency_name": raw.competency_name,
            "subskill_name": raw.subskill_name,
            "question_text": raw.question_text,
            "options": raw.options,
            "correct_option": raw.correct_option,
            "difficulty": raw.difficulty,
        }
    elif isinstance(raw, Mapping):
        payload = dict(raw)
    else:
        raise ValueError("Question-bank records must be structured mappings or QuestionBankRecord values")

    missing = [field for field in REQUIRED_FIELDS if field not in payload or payload[field] is None]
    if missing:
        raise ValueError(f"Incomplete question-bank record; missing fields: {', '.join(missing)}")

    competency_name = _required_text(payload["competency_name"], "competency_name")
    subskill_name = _required_text(payload["subskill_name"], "subskill_name")
    question_text = _required_text(payload["question_text"], "question_text")
    options = _validate_options(payload["options"])
    correct_option = _validate_correct_option(payload["correct_option"])
    difficulty = _validate_difficulty(payload["difficulty"])
    return QuestionBankRecord(
        competency_name=competency_name,
        subskill_name=subskill_name,
        question_text=question_text,
        options=options,
        correct_option=correct_option,
        difficulty=difficulty,
    )


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Incomplete question-bank record; {field_name} is required")
    return value.strip()


def _validate_options(options: Any) -> tuple[str, str, str, str]:
    if not isinstance(options, (list, tuple)) or len(options) != 4:
        raise ValueError("Question-bank options must be a list of exactly four option texts")
    cleaned: list[str] = []
    for option in options:
        if not isinstance(option, str) or not option.strip():
            raise ValueError("Question-bank options must be unique, non-empty strings")
        cleaned.append(option.strip())
    if len({item.casefold() for item in cleaned}) != 4:
        raise ValueError("Question-bank options must be unique, non-empty strings")
    return (cleaned[0], cleaned[1], cleaned[2], cleaned[3])


def _validate_correct_option(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Incomplete question-bank record; correct_option is required")
    label = value.strip().upper()
    if label not in OPTION_LABELS:
        raise ValueError("Question-bank correct_option must be a bare option label (A, B, C, or D)")
    return label


def _validate_difficulty(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Incomplete question-bank record; difficulty is required")
    difficulty = value.strip().casefold()
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty '{value}'; expected one of: {', '.join(sorted(VALID_DIFFICULTIES))}")
    return difficulty


def _serialize_options(options: tuple[str, str, str, str]) -> str:
    labelled = [f"{label}. {text}" for label, text in zip(OPTION_LABELS, options)]
    return json.dumps(labelled)


def _resolve_taxonomy(db: Session, competency_name: str, subskill_name: str) -> tuple[Competency, SubSkill]:
    competency = db.execute(select(Competency).where(Competency.name == competency_name)).scalar_one_or_none()
    if competency is None:
        raise ValueError(f"Invalid competency reference: {competency_name}")

    subskill = db.execute(
        select(SubSkill).where(
            SubSkill.competency_id == competency.id,
            SubSkill.name == subskill_name,
        )
    ).scalar_one_or_none()
    if subskill is not None:
        return competency, subskill

    elsewhere = db.execute(select(SubSkill.id).where(SubSkill.name == subskill_name)).first()
    if elsewhere is not None:
        raise ValueError(
            f"Subskill '{subskill_name}' does not belong to competency '{competency_name}'"
        )
    raise ValueError(f"Invalid subskill reference: {subskill_name}")
