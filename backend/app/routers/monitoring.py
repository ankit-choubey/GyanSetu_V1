from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.monitoring import MonitoringEventRequest, MonitoringEventResponse
from app.services.monitoring_agent import MonitoringAgent

router = APIRouter(tags=["monitoring"])


@router.post("/monitoring/events", response_model=MonitoringEventResponse)
def create_monitoring_event(
    payload: MonitoringEventRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonitoringEventResponse:
    if payload.learner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Learner is outside the authenticated user's scope")

    try:
        db.rollback()
        with db.begin():
            result = MonitoringAgent().handle_event(db, payload)
            return MonitoringEventResponse(
                event_id=result.event_id,
                event_type=result.event_type,
                significance=result.significance,
                status=result.status,
                action=result.action,
                result=result.result,
            )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Monitoring event failed; no changes were saved") from exc