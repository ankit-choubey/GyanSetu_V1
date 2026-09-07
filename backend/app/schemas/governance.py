from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PolicyUpdateRequest(BaseModel):
    value: Any = Field(..., description="New policy value")
    reason: str = Field(..., min_length=5, max_length=500, description="Audit justification for modification")


class LifecycleUpdateRequest(BaseModel):
    action: str = Field(..., description="Action: APPROVE, RETIRE, REVIEW, RETAIN")
    notes: str | None = Field(default=None, max_length=500)
