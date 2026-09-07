from typing import Any
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str | None = "learner"
    role_id: int | None = None
    department: str | None = None
    designation: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any] | None = None


class TokenData(BaseModel):
    user_id: int | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
