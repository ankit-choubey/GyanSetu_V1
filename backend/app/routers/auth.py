from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Role
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> dict:
    existing = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    if payload.role_id is not None and db.get(Role, payload.role_id) is None:
        raise HTTPException(status_code=400, detail="Role not found")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role_id=payload.role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "message": "User registered successfully",
    }


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/auth/me")
def get_current_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "is_active": user.is_active,
    }
