from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class QuestionSelectionRequest:
    competency_id: int
    subskill_id: int | None
    subskill_name: str | None
    evidence_count: int
    evidence_diversity: int
    competency_status: str
    gap_reason: str | None
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class ProposedQuestion:
    question_id: int
    competency_id: int
    subskill_id: int | None
    question_text: str
    options: tuple[str, ...]
    difficulty: str | None = None
    source_reference: str | None = None
    correct_option: str | None = None


class QuestionSelector(Protocol):
    """Future ML boundary; this Afternoon phase does not implement it."""

    def select_next_question(self, request: QuestionSelectionRequest) -> ProposedQuestion | Mapping[str, Any]:
        ...


def validate_proposed_question(
    question: ProposedQuestion | Mapping[str, Any],
    request: QuestionSelectionRequest,
) -> ProposedQuestion:
    if isinstance(question, Mapping):
        try:
            question = ProposedQuestion(
                question_id=int(question["question_id"]),
                competency_id=int(question["competency_id"]),
                subskill_id=question.get("subskill_id"),
                question_text=str(question["question_text"]),
                options=tuple(str(option) for option in question["options"]),
                difficulty=question.get("difficulty"),
                source_reference=question.get("source_reference"),
                correct_option=question.get("correct_option"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("ML question response is malformed") from exc
    if not isinstance(question, ProposedQuestion):
        raise ValueError("ML question response must be a structured question")
    if question.question_id <= 0 or question.competency_id != request.competency_id:
        raise ValueError("ML question does not match the requested competency")
    if question.subskill_id != request.subskill_id:
        raise ValueError("ML question does not match the requested subskill")
    if not question.question_text.strip() or len(question.options) != 4:
        raise ValueError("ML question must contain text and exactly four options")
    normalized_options = {option.strip().casefold() for option in question.options}
    if len(normalized_options) != 4 or "" in normalized_options:
        raise ValueError("ML question options must be unique and non-empty")
    if question.correct_option is not None and question.correct_option not in question.options:
        raise ValueError("ML question correct option is not present in options")
    return question
