from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class PasswordResetOTP(SQLModel, table=True):
    __tablename__ = "password_reset_otps"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, max_length=255)
    otp_code: str = Field(max_length=10)
    expires_at: datetime
    is_used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
