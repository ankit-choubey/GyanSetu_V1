from typing import Any

from pydantic import BaseModel, Field


class ContentWarning(BaseModel):
    code: str
    message: str


class ContentError(BaseModel):
    code: str
    message: str


class DocumentUploadResponse(BaseModel):
    status: str
    filename: str
    content_id: str
    concepts_found: int = 0
    competencies_mapped: list[str] = Field(default_factory=list)
    trusted: bool
    coverage: float
    successful_pages: list[int] = Field(default_factory=list)
    failed_pages: list[int] = Field(default_factory=list)
    ocr_used: bool = False
    warning: str | None = None
    source_reference: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)


class ContentResponse(BaseModel):
    content_id: str
    filename: str
    content_type: str | None
    file_size: int
    status: str
    ml_status: str | None
    concepts_found: int
    competencies_mapped: list[str] = Field(default_factory=list)
    source_reference: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)