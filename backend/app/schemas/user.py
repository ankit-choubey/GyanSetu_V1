from pydantic import BaseModel


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role_id: int | None = None
    is_active: bool = True
