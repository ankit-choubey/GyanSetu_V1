from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_active_user
from app.models.content import ContentAsset, ContentChunk, ProcessingJob
from app.models.user import User
from app.schemas.content import (
    CandidateAssessmentResponse,
    ContentAssetResponse,
    ContentChunkResponse,
    ProcessingJobResponse,
)
from app.schemas.evening import DocumentUploadResponse
from app.services.content.content_interfaces import (
    CandidateAssessmentValidationError,
    ContentExtractionError,
    ContentMappingError,
    DeterministicAssessmentGenerator,
    DeterministicContentChunker,
    DeterministicContentExtractor,
    DeterministicContentMapper,
)
from app.services.content.content_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    ContentService,
    ContentValidationError,
    InvalidStateTransitionError,
)
from app.services.evening_interfaces import DocumentIngestionProvider, UnavailableDocumentIngestionProvider

router = APIRouter(prefix="/content", tags=["content"])


def get_document_processor() -> DocumentIngestionProvider:
    return UnavailableDocumentIngestionProvider()


def _serialize_asset(asset: ContentAsset) -> ContentAssetResponse:
    return ContentAssetResponse(
        id=asset.id,
        asset_id=asset.asset_id,
        filename=asset.filename,
        media_type=asset.media_type,
        file_size=asset.file_size,
        checksum_sha256=asset.checksum_sha256,
        source=asset.source,
        provenance=asset.provenance,
        version=asset.version,
        status=asset.status,
        error_message=asset.error_message,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _serialize_job(job: ProcessingJob) -> ProcessingJobResponse:
    return ProcessingJobResponse(
        id=job.id,
        job_id=job.job_id,
        asset_id=job.asset_id,
        status=job.status,
        current_stage=job.current_stage,
        stage_progress=job.get_stage_progress(),
        error_details=job.error_details,
        retry_count=job.retry_count,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_admin),
    processor: DocumentIngestionProvider = Depends(get_document_processor),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    raw_filename = file.filename or "unnamed"
    
    # Path traversal check
    if ".." in raw_filename or os.path.basename(raw_filename) != raw_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PATH_TRAVERSAL_DETECTED")

    extension = Path(raw_filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FORMAT")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMPTY_CONTENT")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="FILE_SIZE_EXCEEDED")

    # If an external DocumentIngestionProvider was explicitly injected (e.g. in test doubles)
    if not isinstance(processor, UnavailableDocumentIngestionProvider):
        result = processor.process(raw_filename, file.content_type, content)
        return DocumentUploadResponse(
            status=result.status,
            filename=raw_filename,
            trusted=result.trusted,
            coverage=result.coverage,
            successful_pages=list(result.successful_pages),
            failed_pages=list(result.failed_pages),
            ocr_used=result.ocr_used,
            warning=result.warning,
            file_size=len(content),
        )

    # Production 5.3b DB asset persistence & job initialization
    try:
        asset, job, is_duplicate = ContentService.upload_content_asset(
            db,
            filename=raw_filename,
            media_type=file.content_type or "application/octet-stream",
            content_bytes=content,
        )
    except ContentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return DocumentUploadResponse(
        status=asset.status,
        filename=asset.filename,
        trusted=True,
        coverage=1.0,
        successful_pages=[1],
        failed_pages=[],
        ocr_used=False,
        warning=None if not is_duplicate else "Duplicate content detected; existing asset returned.",
        asset_id=asset.asset_id,
        job_id=job.job_id if job else None,
        file_size=asset.file_size,
        checksum_sha256=asset.checksum_sha256,
        is_duplicate=is_duplicate,
    )


@router.get("", response_model=list[ContentAssetResponse])
def list_content_assets(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ContentAssetResponse]:
    assets = ContentService.list_content_assets(db, status=status_filter, skip=skip, limit=limit)
    return [_serialize_asset(a) for a in assets]


@router.get("/{asset_id}", response_model=ContentAssetResponse)
def get_content_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContentAssetResponse:
    asset = ContentService.get_content_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content asset '{asset_id}' not found.")
    return _serialize_asset(asset)


@router.get("/{asset_id}/status", response_model=ProcessingJobResponse)
def get_content_asset_status(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProcessingJobResponse:
    asset = ContentService.get_content_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content asset '{asset_id}' not found.")

    from sqlalchemy import select
    job = db.execute(
        select(ProcessingJob).where(ProcessingJob.asset_id == asset.id).order_by(ProcessingJob.created_at.desc())
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Processing job for asset '{asset_id}' not found.")

    return _serialize_job(job)


@router.post("/{asset_id}/process", response_model=ProcessingJobResponse)
def process_content_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
) -> ProcessingJobResponse:
    try:
        asset, job, chunks, candidates = ContentService.process_content_asset(db, asset_id)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ContentExtractionError, ContentMappingError, CandidateAssessmentValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return _serialize_job(job)


@router.post("/{asset_id}/retry", response_model=ProcessingJobResponse)
def retry_content_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
) -> ProcessingJobResponse:
    try:
        asset, job = ContentService.retry_processing_job(db, asset_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return _serialize_job(job)


@router.post("/{asset_id}/retire", response_model=ContentAssetResponse)
def retire_content_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
) -> ContentAssetResponse:
    try:
        asset = ContentService.retire_content_asset(db, asset_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _serialize_asset(asset)


@router.get("/{asset_id}/chunks", response_model=list[ContentChunkResponse])
def get_content_chunks(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ContentChunkResponse]:
    asset = ContentService.get_content_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content asset '{asset_id}' not found.")

    chunks = ContentService.get_asset_chunks(db, asset_id)
    return [
        ContentChunkResponse(
            id=c.id,
            asset_id=c.asset_id,
            version_id=c.version_id,
            chunk_index=c.chunk_index,
            chunk_type=c.chunk_type,
            content=c.content,
            token_count=c.token_count,
            metadata=c.get_metadata(),
            created_at=c.created_at,
        )
        for c in chunks
    ]


@router.get("/{asset_id}/candidates", response_model=list[CandidateAssessmentResponse])
def get_content_candidates(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CandidateAssessmentResponse]:
    asset = ContentService.get_content_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content asset '{asset_id}' not found.")

    chunks = ContentService.get_asset_chunks(db, asset_id)
    if not chunks:
        return []

    mapper = DeterministicContentMapper()
    generator = DeterministicAssessmentGenerator()
    results: list[CandidateAssessmentResponse] = []

    for c in chunks:
        from app.services.content.content_interfaces import ChunkedBlock
        blk = ChunkedBlock(
            chunk_index=c.chunk_index,
            chunk_type=c.chunk_type,
            content=c.content,
            token_count=c.token_count,
            metadata=c.get_metadata(),
        )
        concepts = mapper.map_chunk(db, blk)
        candidates = generator.generate_candidates(db, asset.asset_id, blk, concepts)
        for cand in candidates:
            results.append(CandidateAssessmentResponse(
                prompt=cand.prompt,
                item_type=cand.item_type,
                options=cand.options,
                correct_answer=cand.correct_answer,
                competency_id=cand.competency_id,
                subskill_id=cand.subskill_id,
                difficulty=cand.difficulty,
                provenance=cand.provenance,
                rubric=cand.rubric,
                metadata=cand.metadata,
            ))

    return results
