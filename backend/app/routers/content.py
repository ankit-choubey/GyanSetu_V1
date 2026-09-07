from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_admin, get_current_user, get_db
from app.models.competency import Competency, Role, SubSkill
from app.models.content import ContentCompetencyMapping, ContentConcept, ContentItem
from app.models.user import User
from app.schemas.content import ContentResponse, DocumentUploadResponse
from app.services.evening_interfaces import (
    ContentProcessResult,
    DocumentIngestionProvider,
    DocumentProcessResult,
    UnavailableDocumentIngestionProvider,
)

router = APIRouter(tags=["content"])

_ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}
_ML_STATUSES = {"completed", "partial", "failed"}


def get_document_processor() -> DocumentIngestionProvider:
    return UnavailableDocumentIngestionProvider()


def _storage_root() -> Path:
    root = Path(settings.content_storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_storage_path(content_id: str, extension: str) -> Path:
    root = _storage_root()
    path = (root / f"{content_id}{extension}").resolve()
    if path.parent != root:
        raise ValueError("Invalid storage path")
    return path


def _is_admin(db: Session, user: User) -> bool:
    role = db.get(Role, user.role_id) if user.role_id else None
    return role is not None and role.name.casefold() in {"admin", "administrator"}


def _authorize_content(db: Session, user: User, content: ContentItem) -> None:
    if content.owner_id != user.id and not _is_admin(db, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Content is outside the authenticated user's scope")


def _normalize(value: str) -> str:
    return value.strip().casefold()


def _validate_content_result(result: ContentProcessResult) -> None:
    if result.status not in _ML_STATUSES:
        raise ValueError("Invalid content processor status")
    for concept in result.concepts:
        if not concept.concept.strip() or not concept.description.strip() or any(not item.strip() for item in concept.subskills):
            raise ValueError("Malformed content concept")
    for mapping in result.competency_mappings:
        if not mapping.concept.strip() or not mapping.competency.strip() or not mapping.rationale.strip():
            raise ValueError("Malformed competency mapping")
        if not 0 <= mapping.confidence <= 1:
            raise ValueError("Content mapping confidence must be between 0 and 1")


def _legacy_result(result: DocumentProcessResult) -> ContentProcessResult:
    warning = result.warning or "Document-ingestion provider is unavailable."
    if result.status == "PARTIAL_EXTRACTION":
        return ContentProcessResult(status="partial", warnings=({"code": result.status, "message": warning},))
    return ContentProcessResult(status="failed", warnings=({"code": result.status, "message": warning},), errors=({"code": "PROVIDER_UNAVAILABLE", "message": warning},))


def _process(provider: DocumentIngestionProvider, filename: str, content_type: str | None, content: bytes, content_id: str, storage_reference: str):
    try:
        return provider.process(filename, content_type, content, content_id=content_id, storage_reference=storage_reference)
    except TypeError as exc:
        if "content_id" not in str(exc) and "storage_reference" not in str(exc):
            raise
        return provider.process(filename, content_type, content)


def _resolve_competency(db: Session, name: str) -> Competency | None:
    normalized = _normalize(name)
    return next((item for item in db.execute(select(Competency)).scalars() if _normalize(item.name) == normalized), None)


def _resolve_subskill(db: Session, competency_id: int, name: str) -> SubSkill | None:
    normalized = _normalize(name)
    return next((item for item in db.execute(select(SubSkill).where(SubSkill.competency_id == competency_id)).scalars() if _normalize(item.name) == normalized), None)


def _persist_result(db: Session, content: ContentItem, result: ContentProcessResult) -> list[str]:
    _validate_content_result(result)
    errors = list(result.errors)
    mapped_names: list[str] = []
    for concept in result.concepts:
        db.add(ContentConcept(content_item_id=content.id, concept=concept.concept.strip(), description=concept.description.strip(), subskills=[item.strip() for item in concept.subskills]))

    for mapping in result.competency_mappings:
        competency = _resolve_competency(db, mapping.competency)
        if competency is None:
            errors.append({"code": "MAPPING_FAILURE", "message": f"Unknown competency: {mapping.competency}"})
            continue
        subskill_ids: list[int | None] = [None]
        if mapping.subskills:
            subskill_ids = []
            for name in mapping.subskills:
                subskill = _resolve_subskill(db, competency.id, name)
                if subskill is None:
                    errors.append({"code": "MAPPING_FAILURE", "message": f"Unknown subskill for {competency.name}: {name}"})
                    continue
                subskill_ids.append(subskill.id)
            if not subskill_ids:
                continue
        for subskill_id in subskill_ids:
            db.add(ContentCompetencyMapping(content_item_id=content.id, competency_id=competency.id, subskill_id=subskill_id, concept=mapping.concept.strip(), confidence=mapping.confidence, rationale=mapping.rationale.strip(), source_reference=result.source_reference))
        mapped_names.append(competency.name)

    content.ml_status = result.status
    content.status = "READY" if result.status == "completed" and not errors else "PARTIAL" if result.status == "partial" or errors else "FAILED"
    if result.status == "failed":
        content.status = "FAILED"
    content.source_reference = result.source_reference
    content.provider_metadata = result.metadata or {}
    content.warnings = list(result.warnings)
    content.errors = errors
    content.updated_at = datetime.now(timezone.utc)
    if content.status == "READY":
        content.completed_at = content.updated_at
    return mapped_names


@router.post("/content/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), user: User = Depends(get_current_admin), db: Session = Depends(get_db), processor: DocumentIngestionProvider = Depends(get_document_processor)) -> DocumentUploadResponse:
    filename = Path(file.filename or "unnamed").name
    extension = Path(filename).suffix.casefold()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_FORMAT")
    content = await file.read(settings.content_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="EMPTY_CONTENT")
    if len(content) > settings.content_max_upload_bytes:
        raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")

    content_id = str(uuid.uuid4())
    storage_path = _safe_storage_path(content_id, extension)
    storage_reference = f"content/{storage_path.name}"
    try:
        storage_path.write_bytes(content)
        with db.begin():
            record = ContentItem(content_id=content_id, owner_id=user.id, original_filename=filename, content_type=file.content_type, file_size=len(content), checksum=hashlib.sha256(content).hexdigest(), storage_reference=storage_reference, status="PROCESSING")
            db.add(record)
            db.flush()
            raw_result = _process(processor, filename, file.content_type, content, content_id, storage_reference)
            result = raw_result if isinstance(raw_result, ContentProcessResult) else _legacy_result(raw_result)
            mapped_names = _persist_result(db, record, result)
            response = DocumentUploadResponse(status=record.status, filename=record.original_filename, content_id=record.content_id, concepts_found=len(result.concepts), competencies_mapped=mapped_names, trusted=record.status == "READY", coverage=raw_result.coverage if isinstance(raw_result, DocumentProcessResult) else 1.0 if record.status == "READY" else 0.0, successful_pages=list(raw_result.successful_pages) if isinstance(raw_result, DocumentProcessResult) else [], failed_pages=list(raw_result.failed_pages) if isinstance(raw_result, DocumentProcessResult) else [], ocr_used=raw_result.ocr_used if isinstance(raw_result, DocumentProcessResult) else False, warning=raw_result.warning if isinstance(raw_result, DocumentProcessResult) else record.warnings[0]["message"] if record.warnings else None, source_reference=record.source_reference, warnings=record.warnings, errors=record.errors)
    except (ValueError, SQLAlchemyError) as exc:
        db.rollback()
        if storage_path.exists():
            storage_path.unlink()
        if isinstance(exc, ValueError):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail="Content persistence failed") from exc
    except Exception:
        db.rollback()
        if storage_path.exists():
            storage_path.unlink()
        raise
    return response


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content(content_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ContentResponse:
    content = db.execute(select(ContentItem).where(ContentItem.content_id == content_id)).scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    _authorize_content(db, user, content)
    return ContentResponse(content_id=content.content_id, filename=content.original_filename, content_type=content.content_type, file_size=content.file_size, status=content.status, ml_status=content.ml_status, concepts_found=len(content.concepts), competencies_mapped=[item.competency.name for item in content.mappings if item.competency], source_reference=content.source_reference, warnings=content.warnings, errors=content.errors)


@router.get("/content/{content_id}/status", response_model=ContentResponse)
def get_content_status(content_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ContentResponse:
    return get_content(content_id, user, db)