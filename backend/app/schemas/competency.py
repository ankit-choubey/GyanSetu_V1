from pydantic import BaseModel


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None


class CompetencyRead(BaseModel):
    id: int
    role_id: int | None = None
    name: str
    description: str | None = None
