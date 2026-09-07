from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.scenario import (
    ScenarioItemResponse,
    ScenarioSubmitRequest,
    ScenarioSubmitResponse,
)
from app.services.scenario_assessment import (
    ScenarioAssessmentError,
    get_scenario_for_learner,
    public_scenario_data,
    submit_scenario_response,
)

router = APIRouter(tags=["scenario assessment"])


def _raise_scenario_error(db: Session, error: ScenarioAssessmentError) -> None:
    db.rollback()
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/scenario/{scenario_id}", response_model=ScenarioItemResponse)
def get_scenario(
    scenario_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioItemResponse:
    try:
        db.rollback()
        scenario = get_scenario_for_learner(db, user, scenario_id)
        return ScenarioItemResponse(**public_scenario_data(scenario))
    except ScenarioAssessmentError as exc:
        _raise_scenario_error(db, exc)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Scenario retrieval failed.") from exc


@router.post("/scenario/submit", response_model=ScenarioSubmitResponse)
def submit_scenario(
    payload: ScenarioSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioSubmitResponse:
    try:
        db.rollback()
        with db.begin():
            result = submit_scenario_response(
                db,
                user,
                payload.scenario_id,
                payload.response_text,
            )

        calculation = result.orchestration.calculation
        return ScenarioSubmitResponse(
            status="success",
            message="Scenario submitted successfully",
            scenario_id=payload.scenario_id,
            attempt_id=result.attempt.id,
            score=result.attempt.score,
            max_score=10,
            percentage=result.attempt.percentage,
            overall_result=result.attempt.overall_result,
            feedback=result.evaluation["feedback"],
            demonstrated_competency=result.attempt.demonstrated_competency,
            updated_competency={
                "mastery": calculation.mastery,
                "confidence": calculation.confidence,
                "coverage": calculation.coverage,
                "evidence_count": calculation.evidence_count,
                "evidence_diversity": calculation.evidence_diversity,
                "status": result.orchestration.state.status,
                "gaps": list(calculation.gaps),
                "message": calculation.message,
            },
        )
    except ScenarioAssessmentError as exc:
        _raise_scenario_error(db, exc)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Scenario submission failed; no changes were saved.",
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Scenario submission failed; no changes were saved.",
        ) from exc