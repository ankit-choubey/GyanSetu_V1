from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.seed_data.question_bank import QuestionBankRecord
from app.seed_data.question_bank_loader import load_question_bank
from app.seed_data.taxonomy_resolver import resolve_taxonomy
from app.services.evening_interfaces import DocumentIngestionProvider, DocumentProcessResult
from ml_pipeline.competency_mapper import map_competencies
from ml_pipeline.concept_extractor import extract_concepts
from ml_pipeline.document_processor import process_document_structured
from ml_pipeline.generate_question_bank import QUALITY_THRESHOLD
from ml_pipeline.mcq_generator import generate_mcqs
from ml_pipeline.mcq_scorer import score_mcq_quality
from ml_pipeline.mcq_validator import validate_mcqs

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".pptx"})
DEFAULT_NUM_QUESTIONS = 5
DEFAULT_DIFFICULTY = "medium"
_FAILURE_CONTENT_TYPES = frozenset({"empty", "empty_no_ocr_available", "ocr_failed"})
_OPTION_PREFIX = re.compile(r"^[A-Da-d][.)]\s*")


class ContentIngestionError(Exception):
    """Controlled failure while turning uploaded content into trusted items."""

    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


class ContentIngestionService(DocumentIngestionProvider):
    """Run the trusted document-to-question-bank pipeline in one transaction."""

    def __init__(
        self,
        db: Session,
        *,
        num_questions: int = DEFAULT_NUM_QUESTIONS,
        difficulty: str = DEFAULT_DIFFICULTY,
    ) -> None:
        self.db = db
        self.num_questions = num_questions
        self.difficulty = difficulty

    def process(
        self,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> DocumentProcessResult:
        del content_type
        extension = Path(filename).suffix.casefold()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ContentIngestionError("UNSUPPORTED_FORMAT", status_code=400)
        if not content:
            raise ContentIngestionError("EMPTY_CONTENT", status_code=400)

        with tempfile.TemporaryDirectory(prefix="gyansetu-content-") as temp_dir:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=extension,
                prefix="upload-",
                dir=temp_dir,
                delete=False,
            ) as temporary_file:
                temporary_file.write(content)
                temporary_path = temporary_file.name

            try:
                pages = process_document_structured(temporary_path)
                source_content, successful_pages, failed_pages = _document_text(pages)
                if failed_pages or not source_content:
                    raise ContentIngestionError(
                        "DOCUMENT_EXTRACTION_INCOMPLETE",
                        status_code=422,
                    )
                self._persist_generated_items(source_content)
            except ContentIngestionError:
                raise
            except ValueError as exc:
                raise ContentIngestionError(str(exc), status_code=422) from exc
            except SQLAlchemyError:
                raise
            except Exception as exc:
                raise ContentIngestionError(
                    "CONTENT_PROCESSING_FAILED",
                    status_code=502,
                ) from exc

        return DocumentProcessResult(
            status="success",
            trusted=True,
            coverage=1.0,
            successful_pages=tuple(successful_pages),
            failed_pages=tuple(failed_pages),
            warning=None,
        )

    def _persist_generated_items(self, source_content: str) -> None:
        try:
            concepts = extract_concepts(source_content)
            if not concepts:
                raise ContentIngestionError("NO_CONCEPTS", status_code=422)

            mappings = map_competencies(concepts)
            if not mappings:
                raise ContentIngestionError("NO_COMPETENCY_MAPPINGS", status_code=422)

            records: list[QuestionBankRecord] = []
            targets: set[tuple[str, str]] = set()
            for mapping in mappings:
                competency_name = mapping.get("competency")
                subskills = mapping.get("subskills")
                if not isinstance(competency_name, str) or not competency_name.strip():
                    raise ContentIngestionError("INVALID_COMPETENCY_MAPPING", status_code=422)
                if not isinstance(subskills, list) or not subskills:
                    raise ContentIngestionError("MISSING_SUBSKILL_MAPPING", status_code=422)
                if len(subskills) != 1:
                    raise ContentIngestionError(
                        "AMBIGUOUS_SUBSKILL_MAPPING: competency-only MCQ generation "
                        "cannot safely assign questions to multiple subskills",
                        status_code=422,
                    )

                subskill_name = subskills[0]
                if not isinstance(subskill_name, str) or not subskill_name.strip():
                    raise ContentIngestionError("INVALID_COMPETENCY_MAPPING", status_code=422)
                target = (competency_name.strip(), subskill_name.strip())
                if target in targets:
                    continue
                resolve_taxonomy(self.db, *target)
                targets.add(target)
                generated = generate_mcqs(
                    source_content,
                    target[0],
                    self.num_questions,
                    self.difficulty,
                )
                reports = validate_mcqs(generated, source_content)
                for mcq, report in zip(generated, reports):
                    if not report.get("valid"):
                        continue
                    scored = score_mcq_quality(mcq, source_content)
                    if float(scored.get("quality_score", 0.0)) < QUALITY_THRESHOLD:
                        continue
                    record = _to_question_bank_record(scored, target)
                    if record is not None:
                        records.append(record)

            if not records:
                raise ContentIngestionError("NO_VALID_MCQ", status_code=422)
            load_question_bank(self.db, records)
        except ContentIngestionError:
            raise
        except ValueError as exc:
            raise ContentIngestionError(str(exc), status_code=422) from exc
        except SQLAlchemyError:
            raise
        except Exception as exc:
            raise ContentIngestionError(
                "CONTENT_PROCESSING_FAILED",
                status_code=502,
            ) from exc


def _document_text(pages: Any) -> tuple[str, list[int], list[int]]:
    if not isinstance(pages, list) or not pages:
        raise ContentIngestionError("DOCUMENT_EXTRACTION_EMPTY", status_code=422)

    text_parts: list[str] = []
    successful_pages: list[int] = []
    failed_pages: list[int] = []
    for page in pages:
        if not isinstance(page, dict):
            raise ContentIngestionError("DOCUMENT_EXTRACTION_INVALID", status_code=422)
        page_number = page.get("page")
        page_text = page.get("text")
        content_type = page.get("content_type")
        if not isinstance(page_number, int) or not isinstance(page_text, str):
            raise ContentIngestionError("DOCUMENT_EXTRACTION_INVALID", status_code=422)
        tables = page.get("tables", [])
        table_parts = []
        for table in tables:
            if isinstance(table, list):
                table_parts.extend(
                    " | ".join(str(cell or "") for cell in row)
                    for row in table
                    if isinstance(row, list)
                )
        if content_type in _FAILURE_CONTENT_TYPES or not page_text.strip() and not table_parts:
            failed_pages.append(page_number)
            continue
        successful_pages.append(page_number)
        if page_text.strip():
            text_parts.append(page_text.strip())
        text_parts.extend(table_parts)

    return "\n\n".join(text_parts).strip(), successful_pages, failed_pages


def _to_question_bank_record(
    mcq: dict[str, Any],
    target: tuple[str, str],
) -> QuestionBankRecord | None:
    question = mcq.get("question")
    options = mcq.get("options")
    correct_answer = mcq.get("correct_answer")
    difficulty = mcq.get("difficulty")
    if (
        not isinstance(question, str)
        or not question.strip()
        or not isinstance(options, list)
        or len(options) != 4
        or not isinstance(correct_answer, str)
        or correct_answer.strip().upper() not in {"A", "B", "C", "D"}
        or not isinstance(difficulty, str)
        or difficulty.strip().casefold() not in {"easy", "medium", "hard"}
    ):
        return None
    if any(not isinstance(option, str) or not option.strip() for option in options):
        return None

    normalized_options = tuple(_OPTION_PREFIX.sub("", option.strip()) for option in options)
    if len({option.casefold() for option in normalized_options}) != 4:
        return None
    return QuestionBankRecord(
        competency_name=target[0],
        subskill_name=target[1],
        question_text=question.strip(),
        options=normalized_options,
        correct_option=correct_answer.strip().upper(),
        difficulty=difficulty.strip().casefold(),
    )
