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


def load_canonical_question_bank(
    db: Session,
    file_path: str | None = None,
) -> int:
    """Loads the canonical JSON question bank into database AssessmentItems."""
    import os
    from pathlib import Path

    if file_path is None:
        candidates = [
            Path(__file__).resolve().parents[3] / "ml_pipeline" / "seed_content" / "canonical_question_bank.json",
            Path(__file__).resolve().parents[2] / "ml_pipeline" / "seed_content" / "canonical_question_bank.json",
            Path("ml_pipeline/seed_content/canonical_question_bank.json"),
            Path("../ml_pipeline/seed_content/canonical_question_bank.json"),
        ]
        chosen = next((p for p in candidates if p.exists()), None)
    else:
        chosen = Path(file_path) if Path(file_path).exists() else None

    if chosen is not None and chosen.exists():
        with open(chosen, "r", encoding="utf-8") as f:
            data = json.load(f)
        questions = data if isinstance(data, list) else data.get("questions", [])
        return load_question_bank(db, questions)

    return load_question_bank(db)



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
        # Canonical schema alias normalization
        if "question_text" not in payload and "question" in payload:
            payload["question_text"] = payload["question"]
        if "correct_option" not in payload and "correct_answer" in payload:
            payload["correct_option"] = payload["correct_answer"]
        if "competency_name" not in payload and "competency" in payload:
            payload["competency_name"] = payload["competency"]
        if "subskill_name" not in payload and "subskill" in payload:
            payload["subskill_name"] = payload["subskill"]
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
        text = option.strip()
        # Clean leading labels like "A. ", "A) ", "(A) " if accidentally present
        if len(text) > 3 and text[0] in "ABCD" and text[1] in ".):" and text[2] == " ":
            text = text[3:].strip()
        elif len(text) > 4 and text.startswith("(") and text[1] in "ABCD" and text[2] == ")" and text[3] == " ":
            text = text[4:].strip()
        cleaned.append(text)
    if len({item.casefold() for item in cleaned}) != 4:
        raise ValueError("Question-bank options must be unique, non-empty strings")
    return (cleaned[0], cleaned[1], cleaned[2], cleaned[3])


def _validate_correct_option(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Incomplete question-bank record; correct_option is required")
    raw = value.strip()
    label = raw.upper()
    if label not in OPTION_LABELS:
        # Check if full text like "A. ..." or "(A)" was provided
        if len(label) > 1 and label[0] in OPTION_LABELS and (label[1] in " .):"):
            label = label[0]
        elif len(label) > 2 and label.startswith("(") and label[1] in OPTION_LABELS and label[2] == ")":
            label = label[1]
        else:
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
