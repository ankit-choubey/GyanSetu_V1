import os
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.competency import Competency, Role, RoleCompetency
from app.models.competency_state import CompetencyState
from app.models.password_reset import PasswordResetOTP
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
    VerifyOTPRequest,
)
from app.services.email_service import send_otp_email
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


def _format_user_profile(user: User, role: Role | None) -> dict:
    is_admin = (role and "admin" in role.name.lower()) or user.role_id == 9
    role_type = "admin" if is_admin else "learner"
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_type,
        "role_name": role.name if role else ("Administrator" if is_admin else "Statistical Officer"),
        "designation": "Workforce Platform Administrator" if is_admin else "Statistical Officer",
        "department": "DIID & Training Planning (MoSPI)" if is_admin else "National Accounts Division (NAD)",
    }


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> Token:
    clean_email = payload.email.lower().strip()
    existing = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="USER_ALREADY_EXISTS: An account is already registered with this email. Please sign in.",
        )

    # Determine role ID
    is_admin = (payload.role or "").lower() == "admin"
    if is_admin:
        admin_role = db.execute(select(Role).where(Role.name.ilike("%admin%"))).scalars().first()
        role_id = admin_role.id if admin_role else 9
    else:
        stat_role = db.execute(select(Role).where(Role.name.ilike("%statistical%"))).scalars().first()
        role_id = stat_role.id if stat_role else 1

    user = User(
        email=clean_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role_id=role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-provision clean baseline CompetencyState entries for 7 role competencies
    role_competency_ids = db.execute(
        select(RoleCompetency.competency_id).where(RoleCompetency.role_id == role_id)
    ).scalars().all()

    if not role_competency_ids:
        # Fallback to standard core official statistics competencies
        role_competency_ids = [1, 2, 3, 8, 10, 31, 40]

    for comp_id in role_competency_ids:
        comp_state = CompetencyState(
            user_id=user.id,
            competency_id=comp_id,
            mastery=None,
            confidence=0.0,
            coverage=0.0,
            evidence_count=0,
            status="UNASSESSED",
        )
        db.add(comp_state)

    try:
        db.commit()
    except Exception:
        db.rollback()

    role = db.get(Role, user.role_id) if user.role_id else None
    token = create_access_token(user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user=_format_user_profile(user, role),
    )


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    clean_email = payload.email.lower().strip()
    user = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND: No account registered with this email. Please sign up as a new user.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_INACTIVE: This account has been deactivated. Contact administration.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_PASSWORD: Incorrect password. Please try again or use forgot password.",
        )

    role = db.get(Role, user.role_id) if user.role_id else None
    access_token = create_access_token(user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=_format_user_profile(user, role),
    )


@router.post("/auth/forgot-password/request-otp")
def request_password_reset_otp(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    clean_email = payload.email.lower().strip()
    user = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND: No account registered with this email. Please check your email or sign up.",
        )

    # Invalidate previous unused OTPs for this email
    existing_otps = db.execute(
        select(PasswordResetOTP).where(
            PasswordResetOTP.email == clean_email,
            PasswordResetOTP.is_used == False,
        )
    ).scalars().all()
    for o in existing_otps:
        o.is_used = True

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    otp_record = PasswordResetOTP(
        email=clean_email,
        otp_code=otp,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(otp_record)
    db.commit()

    # Dispatch email
    dispatch_result = send_otp_email(clean_email, otp)
    return {
        "status": "success",
        "message": f"Verification code sent to {clean_email}.",
        "dev_otp": otp if dispatch_result.get("mode") in ["dev_console", "dev_fallback"] else None,
    }


@router.post("/auth/forgot-password/verify-otp")
def verify_otp_and_reset_password(payload: VerifyOTPRequest, db: Session = Depends(get_db)) -> dict:
    clean_email = payload.email.lower().strip()
    user = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND: User account not found.",
        )

    now = datetime.now(timezone.utc)
    otp_record = db.execute(
        select(PasswordResetOTP).where(
            PasswordResetOTP.email == clean_email,
            PasswordResetOTP.otp_code == payload.otp.strip(),
            PasswordResetOTP.is_used == False,
            PasswordResetOTP.expires_at >= now,
        ).order_by(PasswordResetOTP.created_at.desc())
    ).scalars().first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_OR_EXPIRED_OTP: The verification code is invalid or has expired. Please request a new one.",
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WEAK_PASSWORD: Password must be at least 6 characters long.",
        )

    # Update password and invalidate OTP
    user.password_hash = hash_password(payload.new_password)
    otp_record.is_used = True
    db.commit()

    return {
        "status": "success",
        "message": "Password reset successfully. You can now sign in with your new password.",
    }


@router.get("/auth/me")
def get_current_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    role = db.get(Role, user.role_id) if user.role_id else None
    return _format_user_profile(user, role)

