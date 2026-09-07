from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.scenario import (
    ScenarioAttemptResponseSchema,
    ScenarioCreateRequest,
    ScenarioEvaluationResponseSchema,
    ScenarioGenerateRequest,
    ScenarioResponseSchema,
    ScenarioSubmissionRequest,
    ScenarioSubmissionResultResponseSchema,
)
from app.services.scenarios.scenario_interfaces import (
    CandidateValidationError,
    DeterministicScenarioGenerator,
    EvaluationValidationError,
    ScenarioCandidate,
    ScenarioGenerationContext,
)
from app.services.scenarios.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _serialize_scenario(scen: Scenario) -> ScenarioResponseSchema:
    return ScenarioResponseSchema(
        id=scen.id,
        scenario_id=scen.scenario_id,
        title=scen.title,
        description=scen.description,
        scenario_type=scen.scenario_type,
        competency_id=scen.competency_id,
        subskill_id=scen.subskill_id,
        role_id=scen.role_id,
        difficulty=scen.difficulty,
        version=scen.version,
        status=scen.status,
        expected_outcomes=scen.get_expected_outcomes(),
        evaluation_rubric=scen.get_rubric(),
        metadata=scen.get_metadata(),
        created_at=scen.created_at,
        updated_at=scen.updated_at,
    )


@router.get("", response_model=list[ScenarioResponseSchema])
def list_scenarios(
    competency_id: int | None = Query(None),
    subskill_id: int | None = Query(None),
    role_id: int | None = Query(None),
    difficulty: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ScenarioResponseSchema]:
    scenarios = ScenarioService.list_scenarios(
        db,
        competency_id=competency_id,
        subskill_id=subskill_id,
        role_id=role_id,
        difficulty=difficulty,
        skip=skip,
        limit=limit,
    )
    return [_serialize_scenario(s) for s in scenarios]


@router.post("", response_model=ScenarioResponseSchema, status_code=status.HTTP_201_CREATED)
def create_scenario(
    req: ScenarioCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioResponseSchema:
    candidate = ScenarioCandidate(
        title=req.title,
        description=req.description,
        scenario_type=req.scenario_type,
        competency_id=req.competency_id,
        subskill_id=req.subskill_id,
        role_id=req.role_id,
        difficulty=req.difficulty,
        expected_outcomes=req.expected_outcomes,
        evaluation_rubric=req.evaluation_rubric,
        metadata=req.metadata,
    )
    try:
        scen = ScenarioService.create_scenario(db, candidate)
    except CandidateValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _serialize_scenario(scen)


@router.post("/generate", response_model=ScenarioResponseSchema, status_code=status.HTTP_201_CREATED)
def generate_scenario(
    req: ScenarioGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioResponseSchema:
    ctx = ScenarioGenerationContext(
        competency_id=req.competency_id,
        subskill_id=req.subskill_id,
        role_id=req.role_id,
        difficulty=req.difficulty,
        scenario_type=req.scenario_type,
        learning_objective=req.learning_objective,
    )
    try:
        generator = DeterministicScenarioGenerator()
        scen = ScenarioService.generate_and_persist_scenario(db, ctx, generator=generator)
    except CandidateValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return _serialize_scenario(scen)


@router.get("/{scenario_id}", response_model=ScenarioResponseSchema)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioResponseSchema:
    scen = ScenarioService.get_scenario(db, scenario_id)
    if not scen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scenario '{scenario_id}' not found.")
    return _serialize_scenario(scen)


@router.post("/{scenario_id}/attempts", response_model=ScenarioAttemptResponseSchema, status_code=status.HTTP_201_CREATED)
def start_scenario_attempt(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioAttemptResponseSchema:
    try:
        attempt = ScenarioService.start_attempt(db, user_id=current_user.id, scenario_id_or_int=scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return ScenarioAttemptResponseSchema.model_validate(attempt)


@router.get("/attempts/{attempt_id}", response_model=ScenarioAttemptResponseSchema)
def get_scenario_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioAttemptResponseSchema:
    try:
        attempt = ScenarioService.get_attempt(db, user_id=current_user.id, attempt_id=attempt_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attempt '{attempt_id}' not found.")
    return ScenarioAttemptResponseSchema.model_validate(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=ScenarioSubmissionResultResponseSchema)
def submit_scenario_attempt(
    attempt_id: str,
    req: ScenarioSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ScenarioSubmissionResultResponseSchema:
    try:
        attempt, evaluation, comp_update = ScenarioService.submit_attempt(
            db,
            user_id=current_user.id,
            attempt_id=attempt_id,
            response_payload=req.response_payload,
            idempotency_key=req.idempotency_key,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EvaluationValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    eval_schema = None
    if evaluation:
        eval_schema = ScenarioEvaluationResponseSchema(
            id=evaluation.id,
            attempt_id=evaluation.attempt_id,
            score=evaluation.score,
            max_score=evaluation.max_score,
            normalized_score=evaluation.normalized_score,
            passed=evaluation.passed,
            competency_evidence=evaluation.get_competency_evidence(),
            subskill_evidence=evaluation.get_subskill_evidence(),
            rubric_results=evaluation.get_rubric_results(),
            evaluator_type=evaluation.evaluator_type,
            evaluator_version=evaluation.evaluator_version,
            confidence=evaluation.confidence,
            review_required=evaluation.review_required,
            provenance=evaluation.provenance,
            feedback=evaluation.feedback,
            created_at=evaluation.created_at,
        )

    return ScenarioSubmissionResultResponseSchema(
        attempt=ScenarioAttemptResponseSchema.model_validate(attempt),
        evaluation=eval_schema,
        competency_update=comp_update,
    )
