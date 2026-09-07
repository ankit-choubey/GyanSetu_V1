from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.practical import PracticalAttempt, PracticalTask
from app.models.user import User
from app.schemas.practical import (
    PracticalAttemptRead,
    PracticalSubmitRequest,
    PracticalSubmitResponse,
    PracticalTaskRead,
)
from app.services.practical.practical_service import PracticalService

router = APIRouter(prefix="/practical", tags=["practical-learning"])


def _format_task_read(task: PracticalTask) -> PracticalTaskRead:
    return PracticalTaskRead(
        id=task.id,
        task_id=task.task_id,
        title=task.title,
        competency_id=task.competency_id,
        subskill_id=task.subskill_id,
        scenario_type=task.scenario_type,
        difficulty=task.difficulty,
        scenario_context=task.scenario_context,
        instructions=task.instructions,
        input_artifacts=task.get_input_artifacts(),
        expected_output_type=task.expected_output_type,
        rubric_version=task.rubric_version,
        prerequisites=task.get_prerequisites(),
        provenance=task.provenance,
        source=task.source,
        version=task.version,
        status=task.status,
        created_at=task.created_at,
    )


def _format_attempt_read(attempt: PracticalAttempt) -> PracticalAttemptRead:
    return PracticalAttemptRead(
        id=attempt.id,
        attempt_id=attempt.attempt_id,
        task_id=attempt.task_id,
        user_id=attempt.user_id,
        status=attempt.status,
        task_version=attempt.task_version,
        rubric_version=attempt.rubric_version,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        evaluator_type=attempt.evaluator_type,
        evaluator_version=attempt.evaluator_version,
        evaluation_result=attempt.get_evaluation_result() if attempt.evaluation_result_json else None,
        evidence_id=attempt.evidence_id,
        created_at=attempt.created_at,
    )


@router.get("/tasks", response_model=list[PracticalTaskRead])
def list_tasks(
    competency_id: int | None = Query(None, description="Filter by competency ID"),
    difficulty: str | None = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    scenario_type: str | None = Query(None, description="Filter by scenario type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PracticalTaskRead]:
    tasks = PracticalService.list_tasks(
        db, competency_id=competency_id, difficulty=difficulty, scenario_type=scenario_type, skip=skip, limit=limit
    )
    return [_format_task_read(t) for t in tasks]


@router.get("/tasks/{task_identifier}", response_model=PracticalTaskRead)
def get_task(
    task_identifier: str,
    db: Session = Depends(get_db),
) -> PracticalTaskRead:
    task = PracticalService.get_task(db, task_identifier)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practical task '{task_identifier}' not found.",
        )
    return _format_task_read(task)


@router.post("/tasks/{task_identifier}/attempts", response_model=PracticalAttemptRead)
def start_attempt(
    task_identifier: str,
    idempotency_key: str | None = Query(None, description="Optional idempotency key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticalAttemptRead:
    try:
        attempt = PracticalService.start_attempt(
            db, current_user.id, task_identifier, idempotency_key=idempotency_key
        )
        return _format_attempt_read(attempt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/attempts", response_model=list[PracticalAttemptRead])
def list_attempts(
    task_id: int | None = Query(None, description="Filter by practical task ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PracticalAttemptRead]:
    attempts = PracticalService.list_user_attempts(
        db, user_id=current_user.id, task_id=task_id, skip=skip, limit=limit
    )
    return [_format_attempt_read(a) for a in attempts]


@router.get("/attempts/{attempt_id}", response_model=PracticalAttemptRead)
def get_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticalAttemptRead:
    try:
        attempt = PracticalService.get_attempt(db, current_user.id, attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practical attempt '{attempt_id}' not found.",
            )
        return _format_attempt_read(attempt)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/attempts/{attempt_id}/submit", response_model=PracticalSubmitResponse)
def submit_attempt(
    attempt_id: str,
    request: PracticalSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticalSubmitResponse:
    try:
        attempt, comp_update = PracticalService.submit_attempt(
            db,
            user_id=current_user.id,
            attempt_id=attempt_id,
            submission_payload=request.submission,
            idempotency_key=request.idempotency_key,
            evaluator_type=request.evaluator_type,
        )
        return PracticalSubmitResponse(
            attempt=_format_attempt_read(attempt),
            evaluation=attempt.get_evaluation_result(),
            competency_update=comp_update,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/attempts/{attempt_id}/evaluation")
def get_attempt_evaluation(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        attempt = PracticalService.get_attempt(db, current_user.id, attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practical attempt '{attempt_id}' not found.",
            )
        return {
            "attempt_id": attempt.attempt_id,
            "status": attempt.status,
            "score": attempt.score,
            "evaluator_type": attempt.evaluator_type,
            "evaluator_version": attempt.evaluator_version,
            "evaluation_result": attempt.get_evaluation_result(),
            "evidence_id": attempt.evidence_id,
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
