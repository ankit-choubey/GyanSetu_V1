from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, RoleCompetency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import ScenarioAttempt, ScenarioEvaluation, ScenarioItem
from app.models.user import User
from app.schemas.scenario import (
    ScenarioAttemptCreateResponse,
    ScenarioDeliveryResponse,
    ScenarioEvaluationResponse,
    ScenarioGenerateRequest,
    ScenarioSubmitRequest,
    ScenarioSubmitResponse,
)
from app.services.orchestrator import recalculate_competency_state
from app.services.scenario_interfaces import (
    ScenarioEvaluator,
    ScenarioEvaluatorRequest,
    ScenarioEvaluationOutput,
    ScenarioGenerator,
    ScenarioGeneratorOutput,
    ScenarioGeneratorRequest,
    ScenarioProviderUnavailable,
    UnavailableScenarioEvaluator,
    UnavailableScenarioGenerator,
)

router = APIRouter(tags=["scenario-assessment"])


def get_scenario_generator() -> ScenarioGenerator:
    return UnavailableScenarioGenerator()


def get_scenario_evaluator() -> ScenarioEvaluator:
    return UnavailableScenarioEvaluator()


def _validate_scope(db: Session, user: User, competency_id: int, subskill_id: int | None) -> None:
    if db.get(Competency, competency_id) is None:
        raise HTTPException(status_code=404, detail="Competency not found")
    allowed = db.execute(
        select(RoleCompetency.id).where(
            RoleCompetency.role_id == user.role_id,
            RoleCompetency.competency_id == competency_id,
        )
    ).scalar_one_or_none()
    if allowed is None:
        raise HTTPException(status_code=403, detail="Competency is outside the authenticated user's scope")
    if subskill_id is not None:
        subskill = db.get(SubSkill, subskill_id)
        if subskill is None:
            raise HTTPException(status_code=404, detail="Subskill not found")
        if subskill.competency_id != competency_id:
            raise HTTPException(status_code=400, detail="Subskill does not belong to competency")


def _validate_generator_output(output: ScenarioGeneratorOutput, request: ScenarioGenerateRequest) -> None:
    if output.competency_id != request.competency_id or output.subskill_id != request.subskill_id:
        raise ValueError("Scenario provider competency or subskill does not match the request")


def _validate_response(response: dict[str, Any], response_type: str) -> None:
    if response_type == "structured_text" and (not isinstance(response.get("text"), str) or not response["text"].strip()):
        raise ValueError("Structured-text scenarios require a non-empty text response")
    if response_type == "multiple_choice" and not isinstance(response.get("selected"), str):
        raise ValueError("Multiple-choice scenarios require a selected response")
    if response_type == "numeric" and (isinstance(response.get("value"), bool) or not isinstance(response.get("value"), (int, float))):
        raise ValueError("Numeric scenarios require a numeric value")
    if response_type == "structured_input" and not response:
        raise ValueError("Structured-input scenarios require a non-empty response")


def _validate_evaluation_output(output, item: ScenarioItem) -> None:
    if output.scenario_id != item.scenario_id or output.competency_id != item.competency_id or output.subskill_id != item.subskill_id:
        raise ValueError("Evaluator output does not match scenario context")
    rubric = item.rubric
    if output.evaluation.max_score != rubric["max_score"]:
        raise ValueError("Evaluator max_score does not match scenario rubric")
    limits = {criterion["criterion_id"]: criterion["max_score"] for criterion in rubric["criteria"]}
    for result in output.evaluation.criterion_results:
        if result.criterion_id not in limits:
            raise ValueError("Evaluator returned an unknown rubric criterion")
        if result.score > limits[result.criterion_id]:
            raise ValueError("Evaluator criterion score exceeds rubric limit")


def _persisted_evaluation_payload(evaluation: ScenarioEvaluation) -> dict[str, Any]:
    return {
        "score": evaluation.score,
        "max_score": evaluation.max_score,
        "percentage": evaluation.percentage,
        "overall_result": evaluation.overall_result,
        "criterion_results": evaluation.criterion_results,
        "feedback": evaluation.feedback,
        "demonstrated_competency": evaluation.demonstrated_competency,
        "confidence": evaluation.evaluator_confidence,
        "metadata": evaluation.evaluator_metadata,
    }


def _delivery(output: ScenarioGeneratorOutput) -> ScenarioDeliveryResponse:
    return ScenarioDeliveryResponse(
        status="AVAILABLE",
        scenario_id=output.scenario_id,
        competency_id=output.competency_id,
        subskill_id=output.subskill_id,
        scenario=output.scenario,
        difficulty=output.difficulty,
        cognitive_level=output.cognitive_level,
        source=output.source.model_dump(mode="json"),
    )


def _persist_scenario(db: Session, output: ScenarioGeneratorOutput) -> ScenarioItem:
    item = ScenarioItem(
        scenario_id=output.scenario_id,
        competency_id=output.competency_id,
        subskill_id=output.subskill_id,
        title=output.scenario.title,
        context=output.scenario.context,
        context_data=output.scenario.context_data,
        task_question=output.scenario.task.question,
        response_type=output.scenario.task.response_type,
        instructions=output.scenario.task.instructions,
        expected_reasoning=output.expected_reasoning.model_dump(mode="json"),
        rubric=output.rubric.model_dump(mode="json"),
        difficulty=output.difficulty,
        cognitive_level=output.cognitive_level,
        source_metadata=output.source.model_dump(mode="json"),
        generator_metadata=output.metadata.model_dump(mode="json"),
    )
    db.add(item)
    db.flush()
    return item


def _learner_scenario(db: Session, user: User, scenario_id: str) -> ScenarioItem:
    item = db.execute(select(ScenarioItem).where(ScenarioItem.scenario_id == scenario_id)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    _validate_scope(db, user, item.competency_id, item.subskill_id)
    return item


@router.post("/scenario-assessments", response_model=ScenarioDeliveryResponse)
def generate_scenario(
    payload: ScenarioGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    generator: ScenarioGenerator = Depends(get_scenario_generator),
) -> ScenarioDeliveryResponse:
    _validate_scope(db, user, payload.competency_id, payload.subskill_id)
    try:
        output = ScenarioGeneratorOutput.model_validate(generator.generate(ScenarioGeneratorRequest(**payload.model_dump())))
        _validate_generator_output(output, payload)
        db.rollback()
        with db.begin():
            _persist_scenario(db, output)
        return _delivery(output)
    except ScenarioProviderUnavailable as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail={"status": "PROVIDER_UNAVAILABLE", "message": str(exc)}) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Scenario persistence failed") from exc


@router.get("/scenario-assessments/{scenario_id}", response_model=ScenarioDeliveryResponse)
def get_scenario(scenario_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioDeliveryResponse:
    item = _learner_scenario(db, user, scenario_id)
    return ScenarioDeliveryResponse(
        status=item.status,
        scenario_id=item.scenario_id,
        competency_id=item.competency_id,
        subskill_id=item.subskill_id,
        scenario={
            "title": item.title,
            "context": item.context,
            "context_data": item.context_data,
            "task": {"question": item.task_question, "response_type": item.response_type, "instructions": item.instructions},
        },
    )


@router.post("/scenario-assessments/{scenario_id}/attempts", response_model=ScenarioAttemptCreateResponse)
def create_scenario_attempt(scenario_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioAttemptCreateResponse:
    item = _learner_scenario(db, user, scenario_id)
    db.rollback()
    with db.begin():
        attempt = ScenarioAttempt(
            scenario_item_id=item.id,
            scenario_id=item.scenario_id,
            user_id=user.id,
            competency_id=item.competency_id,
            subskill_id=item.subskill_id,
        )
        db.add(attempt)
        db.flush()
    return ScenarioAttemptCreateResponse(status="ATTEMPTED", attempt_id=attempt.id, scenario_id=scenario_id)


@router.post("/scenario-assessments/{scenario_id}/attempts/{attempt_id}/submit", response_model=ScenarioSubmitResponse)
def submit_scenario(
    scenario_id: str,
    attempt_id: int,
    payload: ScenarioSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    evaluator: ScenarioEvaluator = Depends(get_scenario_evaluator),
) -> ScenarioSubmitResponse:
    attempt = db.get(ScenarioAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="Attempt is outside the authenticated user's scope")
    if attempt.scenario_id != scenario_id:
        raise HTTPException(status_code=409, detail="Scenario ID does not match attempt")
    item = _learner_scenario(db, user, scenario_id)
    existing_evaluation = db.execute(
        select(ScenarioEvaluation).where(ScenarioEvaluation.scenario_attempt_id == attempt.id)
    ).scalar_one_or_none()
    if existing_evaluation is not None:
        return ScenarioSubmitResponse(
            status="EVALUATED",
            attempt_id=attempt.id,
            scenario_id=scenario_id,
            evaluation_id=existing_evaluation.id,
            evaluation=_persisted_evaluation_payload(existing_evaluation),
        )
    if not isinstance(payload.response, dict) or not payload.response:
        raise HTTPException(status_code=422, detail="Scenario response must be a non-empty object")
    _validate_response(payload.response, item.response_type)
    request = ScenarioEvaluatorRequest(
        scenario_id=item.scenario_id,
        competency_id=item.competency_id,
        subskill_id=item.subskill_id,
        scenario={"title": item.title, "context": item.context, "context_data": item.context_data, "task": {"question": item.task_question, "response_type": item.response_type, "instructions": item.instructions}},
        learner_response=payload.response,
        expected_reasoning=item.expected_reasoning,
        rubric=item.rubric,
    )
    db.rollback()
    try:
        with db.begin():
            attempt.submitted_response = payload.response
            attempt.submitted_at = datetime.now(timezone.utc)
            attempt.status = "SUBMITTED"
            try:
                output = ScenarioEvaluationOutput.model_validate(evaluator.evaluate(request))
            except ScenarioProviderUnavailable:
                attempt.status = "PENDING_EVALUATION"
                db.flush()
                return ScenarioSubmitResponse(status="PENDING_EVALUATION", attempt_id=attempt.id, scenario_id=scenario_id)
            _validate_evaluation_output(output, item)
            evaluation = ScenarioEvaluation(
                scenario_attempt_id=attempt.id,
                scenario_id=output.scenario_id,
                competency_id=output.competency_id,
                subskill_id=output.subskill_id,
                score=output.evaluation.score,
                max_score=output.evaluation.max_score,
                percentage=output.evaluation.percentage,
                overall_result=output.evaluation.overall_result,
                criterion_results=[result.model_dump(mode="json") for result in output.evaluation.criterion_results],
                feedback=output.feedback.model_dump(mode="json"),
                demonstrated_competency=output.evidence.demonstrated_competency,
                evaluator_confidence=output.evidence.confidence,
                evaluator_metadata=output.metadata.model_dump(mode="json"),
            )
            db.add(evaluation)
            attempt.status = "EVALUATED"
            attempt.completed_at = datetime.now(timezone.utc)
            db.flush()
            db.add(Evidence(
                user_id=user.id,
                competency_id=item.competency_id,
                subskill_id=item.subskill_id,
                evidence_type=EvidenceType.APPLICATION_SCENARIO,
                title=f"Scenario assessment: {item.title}",
                description=output.feedback.summary,
                score=output.evaluation.percentage / 100,
                weight=1.0,
                evidence_metadata=json.dumps({"scenario_id": item.scenario_id, "attempt_id": attempt.id, "evaluation": output.model_dump(mode="json")}),
            ))
            db.flush()
            recalculate_competency_state(db, user.id, item.competency_id)
            return ScenarioSubmitResponse(status="EVALUATED", attempt_id=attempt.id, scenario_id=scenario_id, evaluation_id=evaluation.id, evaluation=output.model_dump(mode="json"))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Scenario submission failed; no changes were saved") from exc


@router.get("/scenario-assessments/{scenario_id}/attempts/{attempt_id}/evaluation", response_model=ScenarioEvaluationResponse)
def get_scenario_evaluation(scenario_id: str, attempt_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ScenarioEvaluationResponse:
    attempt = db.get(ScenarioAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="Attempt is outside the authenticated user's scope")
    if attempt.scenario_id != scenario_id:
        raise HTTPException(status_code=409, detail="Scenario ID does not match attempt")
    evaluation = db.execute(select(ScenarioEvaluation).where(ScenarioEvaluation.scenario_attempt_id == attempt.id)).scalar_one_or_none()
    if evaluation is None:
        return ScenarioEvaluationResponse(status=attempt.status, attempt_id=attempt.id, scenario_id=scenario_id)
    return ScenarioEvaluationResponse(
        status="EVALUATED",
        attempt_id=attempt.id,
        scenario_id=scenario_id,
        evaluation={
            **_persisted_evaluation_payload(evaluation),
        },
    )