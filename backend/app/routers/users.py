from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserProfile

router = APIRouter(tags=["users"])


@router.get("/users/profile", response_model=UserProfile)
def get_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_id=user.role_id,
        is_active=user.is_active,
    )
