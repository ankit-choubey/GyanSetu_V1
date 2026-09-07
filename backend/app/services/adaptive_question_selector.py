from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, SubSkill
from app.services.ml_interfaces import (
    ProposedQuestion,
    QuestionSelectionRequest,
    QuestionSelector,
    validate_proposed_question,
)
from ml_pipeline import adaptive_selector


class NoEligibleDiagnosticQuestionError(Exception):
    """Raised when the adaptive selector reports no remaining question."""


class DatabaseAdaptiveQuestionSelector(QuestionSelector):
    """Adapt validated database assessment items to the ML selector contract."""

    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id

    def select_next_question(
        self,
        request: QuestionSelectionRequest,
    ) -> ProposedQuestion:
        items = self._load_items(request.competency_id)
        item_bank = [self._item_to_ml(item, competency, subskill) for item, competency, subskill in items]
        history = self._load_history(request.competency_id)

        if request.subskill_name is not None:
            item_bank.sort(key=lambda item: item["subskill"] != request.subskill_name)

        result = adaptive_selector.select_next_question(
            item_bank=item_bank,
            session_history=history,
            competency=self._competency_name(items),
        )
        if not isinstance(result, dict):
            raise ValueError("ML adaptive selector response must be an object")
        if "next_question" not in result or not isinstance(result.get("is_complete"), bool):
            raise ValueError("ML adaptive selector response is malformed")
        if result["is_complete"] is True or result["next_question"] is None:
            raise NoEligibleDiagnosticQuestionError(
                "No eligible diagnostic question remains for this competency."
            )

        proposed = self._selected_item_to_question(result["next_question"], request, items)
        validation_request = request
        if request.subskill_id is None and proposed.subskill_id is not None:
            validation_request = QuestionSelectionRequest(
                competency_id=request.competency_id,
                subskill_id=proposed.subskill_id,
                subskill_name=request.subskill_name,
                evidence_count=request.evidence_count,
                evidence_diversity=request.evidence_diversity,
                competency_status=request.competency_status,
                gap_reason=request.gap_reason,
                constraints=request.constraints,
            )
        return validate_proposed_question(proposed, validation_request)

    def _load_items(
        self,
        competency_id: int,
    ) -> list[tuple[AssessmentItem, Competency, SubSkill | None]]:
        rows = self.db.execute(
            select(AssessmentItem, Competency, SubSkill)
            .join(Competency, Competency.id == AssessmentItem.competency_id)
            .outerjoin(SubSkill, SubSkill.id == AssessmentItem.subskill_id)
            .where(
                AssessmentItem.competency_id == competency_id,
                AssessmentItem.user_id.is_(None),
            )
            .order_by(AssessmentItem.id)
        ).all()
        return list(rows)

    def _load_history(self, competency_id: int) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(AssessmentResponse, AssessmentItem, SubSkill)
            .join(AssessmentAttempt, AssessmentAttempt.id == AssessmentResponse.attempt_id)
            .join(AssessmentItem, AssessmentItem.id == AssessmentResponse.assessment_item_id)
            .outerjoin(SubSkill, SubSkill.id == AssessmentResponse.subskill_id)
            .where(
                AssessmentAttempt.user_id == self.user_id,
                AssessmentAttempt.competency_id == competency_id,
                AssessmentResponse.competency_id == competency_id,
            )
            .order_by(AssessmentResponse.answered_at, AssessmentResponse.id)
        ).all()
        return [
            {
                "question_id": response.assessment_item_id,
                "question": item.question_text,
                "difficulty": item.difficulty or "medium",
                "subskill": subskill.name if subskill is not None else None,
                "is_correct": response.is_correct,
            }
            for response, item, subskill in rows
        ]

    @staticmethod
    def _competency_name(
        items: list[tuple[AssessmentItem, Competency, SubSkill | None]],
    ) -> str | None:
        return items[0][1].name if items else None

    @staticmethod
    def _item_to_ml(
        item: AssessmentItem,
        competency: Competency,
        subskill: SubSkill | None,
    ) -> dict[str, Any]:
        return {
            "question_id": item.id,
            "question": item.question_text,
            "options": _parse_options(item.options_json),
            "correct_option": item.correct_option,
            "difficulty": item.difficulty or "medium",
            "competency": competency.name,
            "subskill": subskill.name if subskill is not None else None,
            "source_reference": item.source_reference,
        }

    @staticmethod
    def _selected_item_to_question(
        selected: Any,
        request: QuestionSelectionRequest,
        items: list[tuple[AssessmentItem, Competency, SubSkill | None]],
    ) -> ProposedQuestion:
        if not isinstance(selected, dict):
            raise ValueError("ML adaptive selector returned a malformed question")
        selected_id = selected.get("question_id")
        selected_item = next(
            (row for row in items if row[0].id == selected_id),
            None,
        )
        if selected_item is None:
            raise ValueError("ML adaptive selector returned an unknown question")
        item, _, subskill = selected_item
        return ProposedQuestion(
            question_id=item.id,
            competency_id=item.competency_id,
            subskill_id=item.subskill_id,
            question_text=item.question_text,
            options=tuple(_parse_options(item.options_json)),
            difficulty=item.difficulty,
            source_reference=item.source_reference,
            correct_option=item.correct_option,
        )


def _parse_options(options_json: str) -> list[str]:
    try:
        options = json.loads(options_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Assessment item options are malformed") from exc
    if (
        not isinstance(options, list)
        or len(options) != 4
        or any(not isinstance(option, str) or not option.strip() for option in options)
        or len({option.strip().casefold() for option in options}) != 4
    ):
        raise ValueError("Assessment item options are malformed")
    return options