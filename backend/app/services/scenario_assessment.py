from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import RoleCompetency
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import ScenarioItem
from app.models.scenario_attempt import ScenarioAttempt
from app.models.user import User
from app.services import scenario_ml_adapter
from app.services.orchestrator import OrchestrationResult, recalculate_competency_state


class ScenarioAssessmentError(Exception):
    """A safe, user-facing error from the scenario assessment workflow."""

    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class ScenarioSubmissionResult:
    attempt: ScenarioAttempt
    evaluation: dict[str, Any]
    orchestration: OrchestrationResult


def _parse_json_object(raw_value: str | None, field_name: str, *, required: bool = True) -> dict[str, Any] | None:
    if raw_value is None or not raw_value.strip():
        if required:
            raise ScenarioAssessmentError("Stored scenario data is malformed.", 500)
        return None

    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ScenarioAssessmentError("Stored scenario data is malformed.", 500) from exc

    if not isinstance(value, dict):
        raise ScenarioAssessmentError("Stored scenario data is malformed.", 500)

    return value


def _assert_authorized(db: Session, user: User, competency_id: int) -> None:
    authorized = db.execute(
        select(RoleCompetency.id).where(
            RoleCompetency.role_id == user.role_id,
            RoleCompetency.competency_id == competency_id,
        )
    ).scalar_one_or_none()
    if authorized is None:
        raise ScenarioAssessmentError(
            "Scenario is outside the authenticated user's scope.",
            403,
        )


def get_scenario_for_learner(
    db: Session,
    user: User,
    scenario_id: int,
) -> ScenarioItem:
    scenario = db.get(ScenarioItem, scenario_id)
    if scenario is None:
        raise ScenarioAssessmentError("Scenario not found.", 404)

    _assert_authorized(db, user, scenario.competency_id)
    _parse_json_object(scenario.context_data, "context_data", required=False)
    return scenario


def public_scenario_data(scenario: ScenarioItem) -> dict[str, Any]:
    context_data = _parse_json_object(
        scenario.context_data,
        "context_data",
        required=False,
    )
    return {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "scenario_text": scenario.scenario_text,
        "context_data": context_data,
        "question": scenario.question,
        "response_type": scenario.response_type,
        "instructions": scenario.instructions,
        "difficulty": scenario.difficulty,
        "cognitive_level": scenario.cognitive_level,
        "source_reference": scenario.source_reference,
    }


def _validate_evaluation(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    evaluation = result.get("evaluation")
    feedback = result.get("feedback")
    evidence = result.get("evidence")
    if not isinstance(evaluation, dict) or not isinstance(feedback, dict) or not isinstance(evidence, dict):
        raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    score = evaluation.get("score")
    max_score = evaluation.get("max_score")
    percentage = evaluation.get("percentage")
    criterion_results = evaluation.get("criterion_results")
    overall_result = evaluation.get("overall_result")
    if (
        not isinstance(score, int)
        or isinstance(score, bool)
        or not 0 <= score <= 10
        or max_score != 10
        or not isinstance(percentage, (int, float))
        or isinstance(percentage, bool)
        or not 0 <= percentage <= 100
        or abs(float(percentage) - score / 10 * 100) > 1e-6
        or not isinstance(criterion_results, list)
        or not criterion_results
        or overall_result not in {"correct", "partially_correct", "incorrect"}
    ):
        raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    criterion_total = 0
    for criterion in criterion_results:
        if not isinstance(criterion, dict):
            raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)
        if not all(field in criterion for field in ("criterion_id", "score", "max_score", "result", "feedback")):
            raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)
        criterion_score = criterion["score"]
        criterion_max_score = criterion["max_score"]
        if (
            not isinstance(criterion_score, int)
            or isinstance(criterion_score, bool)
            or not isinstance(criterion_max_score, int)
            or isinstance(criterion_max_score, bool)
            or criterion_score < 0
            or criterion_score > criterion_max_score
            or not isinstance(criterion["feedback"], str)
            or criterion["result"] not in {"met", "partially_met", "not_met"}
        ):
            raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)
        criterion_total += criterion_score

    if criterion_total != score:
        raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    for field in ("summary", "recommended_next_step"):
        if not isinstance(feedback.get(field), str):
            raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)
    for field in ("strengths", "areas_for_improvement"):
        if not isinstance(feedback.get(field), list):
            raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    if (
        evidence.get("evidence_type") != "scenario_assessment"
        or not isinstance(evidence.get("demonstrated_competency"), bool)
        or not isinstance(evidence.get("confidence"), (int, float))
        or isinstance(evidence.get("confidence"), bool)
        or not 0 <= evidence["confidence"] <= 1
    ):
        raise ScenarioAssessmentError("Scenario evaluation was invalid.", 502)

    return result


def submit_scenario_response(
    db: Session,
    user: User,
    scenario_id: int,
    learner_response: str,
) -> ScenarioSubmissionResult:
    if not learner_response.strip():
        raise ScenarioAssessmentError("Response cannot be empty.", 400)

    scenario_item = get_scenario_for_learner(db, user, scenario_id)
    context_data = _parse_json_object(
        scenario_item.context_data,
        "context_data",
        required=False,
    )
    expected_reasoning = _parse_json_object(scenario_item.expected_reasoning, "expected_reasoning")
    rubric = _parse_json_object(scenario_item.rubric, "rubric")

    scenario = {
        "title": scenario_item.title,
        "context": scenario_item.scenario_text,
        "context_data": context_data,
    }
    task = {
        "question": scenario_item.question,
        "response_type": scenario_item.response_type,
        "instructions": scenario_item.instructions,
    }

    try:
        evaluation = scenario_ml_adapter.evaluate_scenario_response(
            scenario,
            task,
            expected_reasoning,
            rubric,
            learner_response,
        )
    except ScenarioAssessmentError:
        raise
    except Exception as exc:
        raise ScenarioAssessmentError("Scenario evaluation failed.", 502) from exc

    validated = _validate_evaluation(evaluation)
    evaluation_data = validated["evaluation"]
    feedback = validated["feedback"]
    evidence_data = validated["evidence"]

    attempt = ScenarioAttempt(
        user_id=user.id,
        scenario_id=scenario_item.id,
        response_text=learner_response,
        score=evaluation_data["score"],
        percentage=float(evaluation_data["percentage"]),
        overall_result=evaluation_data["overall_result"],
        evaluation_feedback=json.dumps(feedback),
        evaluation_criterion_results=json.dumps(evaluation_data["criterion_results"]),
        confidence=float(evidence_data["confidence"]),
        demonstrated_competency=evidence_data["demonstrated_competency"],
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()

    evidence_metadata = {
        "scenario_id": scenario_item.id,
        "attempt_id": attempt.id,
        "source_reference": scenario_item.source_reference,
        "overall_result": evaluation_data["overall_result"],
        "criterion_results": evaluation_data["criterion_results"],
        "ml_evidence": evidence_data,
    }
    db.add(
        Evidence(
            user_id=user.id,
            competency_id=scenario_item.competency_id,
            subskill_id=scenario_item.subskill_id,
            evidence_type=EvidenceType.APPLICATION_SCENARIO,
            title="Scenario assessment submission",
            description="ML-evaluated scenario-based practical assessment evidence",
            score=float(evaluation_data["percentage"]) / 100,
            weight=1.0,
            evidence_metadata=json.dumps(evidence_metadata),
        )
    )
    db.flush()

    try:
        orchestration = recalculate_competency_state(
            db,
            user.id,
            scenario_item.competency_id,
        )
    except Exception as exc:
        raise ScenarioAssessmentError("Scenario submission could not be completed.", 500) from exc

    return ScenarioSubmissionResult(
        attempt=attempt,
        evaluation=validated,
        orchestration=orchestration,
    )