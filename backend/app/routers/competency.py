from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, Role
from app.models.user import User

router = APIRouter(tags=["competency"])


@router.get("/competencies/{role_id}")
def get_role_competencies(
    role_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if user.role_id != role_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is outside the authenticated user's scope")

    competencies = db.execute(select(Competency).where(Competency.role_id == role_id)).scalars().all()
    return {
        "role_id": role.id,
        "role_name": role.name,
        "competencies": [
            {
                "id": comp.id,
                "name": comp.name,
                "description": comp.description,
            }
            for comp in competencies
        ],
        "user_id": user.id,
    }
