from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import (
    ContentAsset,
    ContentChunk,
    ContentStatus,
    ContentVersion,
    JobStatus,
    ProcessingJob,
)
from app.services.content.content_interfaces import (
    AssessmentGenerator,
    CandidateAssessment,
    CandidateAssessmentValidationError,
    ContentChunker,
    ContentExtractionError,
    ContentExtractor,
    ContentMapper,
    ContentMappingError,
    DeterministicAssessmentGenerator,
    DeterministicContentChunker,
    DeterministicContentExtractor,
    DeterministicContentMapper,
)


class ContentValidationError(Exception):
    """Raised on invalid upload files or media parameters."""
    pass


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state machine transition is attempted."""
    pass


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

VALID_STATUS_TRANSITIONS = {
    ContentStatus.UPLOADED.value: {ContentStatus.VALIDATING.value, ContentStatus.FAILED.value, ContentStatus.RETIRED.value},
    ContentStatus.VALIDATING.value: {ContentStatus.PROCESSING.value, ContentStatus.FAILED.value},
    ContentStatus.PROCESSING.value: {ContentStatus.EXTRACTED.value, ContentStatus.FAILED.value},
    ContentStatus.EXTRACTED.value: {ContentStatus.STRUCTURED.value, ContentStatus.FAILED.value},
    ContentStatus.STRUCTURED.value: {ContentStatus.MAPPED.value, ContentStatus.FAILED.value},
    ContentStatus.MAPPED.value: {ContentStatus.READY.value, ContentStatus.REQUIRES_REVIEW.value, ContentStatus.FAILED.value},
    ContentStatus.FAILED.value: {ContentStatus.PROCESSING.value, ContentStatus.VALIDATING.value, ContentStatus.RETIRED.value},
    ContentStatus.READY.value: {ContentStatus.RETIRED.value, ContentStatus.PROCESSING.value},
    ContentStatus.REQUIRES_REVIEW.value: {ContentStatus.READY.value, ContentStatus.RETIRED.value},
    ContentStatus.RETIRED.value: set(),  # Terminal
}


class ContentService:
    """Service orchestrating content upload, state machine processing, chunking, and candidate generation."""

    @staticmethod
    def validate_file(filename: str, content_bytes: bytes) -> None:
        if not filename or len(filename.strip()) == 0:
            raise ContentValidationError("Filename cannot be empty.")

        # Path traversal protection
        safe_name = os.path.basename(filename)
        if ".." in filename or safe_name != filename:
            raise ContentValidationError("Path traversal characters not allowed in filename.")

        ext = Path(filename).suffix.casefold()
        if ext not in ALLOWED_EXTENSIONS:
            raise ContentValidationError(f"Unsupported media extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

        if not content_bytes or len(content_bytes) == 0:
            raise ContentValidationError("Uploaded file content cannot be empty.")

        if len(content_bytes) > MAX_FILE_SIZE:
            raise ContentValidationError(f"File size {len(content_bytes)} bytes exceeds maximum allowed {MAX_FILE_SIZE} bytes.")

    @staticmethod
    def transition_asset_status(asset: ContentAsset, new_status: str) -> None:
        current = asset.status
        allowed = VALID_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(f"Cannot transition content asset from '{current}' to '{new_status}'.")
        asset.status = new_status
        asset.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def upload_content_asset(
        db: Session,
        filename: str,
        media_type: str | None,
        content_bytes: bytes,
    ) -> tuple[ContentAsset, ProcessingJob, bool]:
        """Validate, store metadata, detect duplicate checksums, and create initial processing job."""
        ContentService.validate_file(filename, content_bytes)

        checksum = hashlib.sha256(content_bytes).hexdigest()
        media_type_clean = media_type or "application/octet-stream"

        # Checksum-based duplicate detection
        existing_asset = db.execute(
            select(ContentAsset).where(ContentAsset.checksum_sha256 == checksum)
        ).scalar_one_or_none()

        if existing_asset:
            # Return existing asset with its most recent job
            latest_job = db.execute(
                select(ProcessingJob)
                .where(ProcessingJob.asset_id == existing_asset.id)
                .order_by(ProcessingJob.created_at.desc())
            ).scalar_one_or_none()
            return existing_asset, latest_job, True

        # Create new asset
        asset_id = f"asset_{uuid.uuid4().hex[:10]}"
        asset = ContentAsset(
            asset_id=asset_id,
            filename=filename,
            media_type=media_type_clean,
            file_size=len(content_bytes),
            checksum_sha256=checksum,
            storage_path=f"storage/content/{asset_id}/{filename}",
            source="MOSPI_TRAINING",
            provenance="[SANDBOX DATA]",
            version=1,
            status=ContentStatus.UPLOADED.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(asset)
        db.flush()

        # Create version 1 record
        version = ContentVersion(
            asset_id=asset.id,
            version_number=1,
            checksum_sha256=checksum,
            file_size=len(content_bytes),
            change_summary="Initial upload",
            created_at=datetime.now(timezone.utc),
        )
        db.add(version)
        db.flush()

        # Create initial processing job
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = ProcessingJob(
            job_id=job_id,
            asset_id=asset.id,
            status=JobStatus.QUEUED.value,
            current_stage="UPLOADED",
            stage_progress_json=json.dumps({"uploaded": True, "checksum": checksum}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(asset)
        db.refresh(job)

        return asset, job, False

    @staticmethod
    def process_content_asset(
        db: Session,
        asset_id: str,
        extractor: ContentExtractor | None = None,
        chunker: ContentChunker | None = None,
        mapper: ContentMapper | None = None,
        generator: AssessmentGenerator | None = None,
        content_bytes_override: bytes | None = None,
    ) -> tuple[ContentAsset, ProcessingJob, list[ContentChunk], list[CandidateAssessment]]:
        """Run the end-to-end processing pipeline through validated state transitions."""
        asset = db.execute(
            select(ContentAsset).where(ContentAsset.asset_id == asset_id)
        ).scalar_one_or_none()
        if not asset:
            raise ValueError(f"Content asset '{asset_id}' not found.")

        if asset.status == ContentStatus.RETIRED.value:
            raise InvalidStateTransitionError("Cannot process retired content asset.")

        job = db.execute(
            select(ProcessingJob)
            .where(ProcessingJob.asset_id == asset.id)
            .order_by(ProcessingJob.created_at.desc())
        ).scalar_one_or_none()

        if not job:
            job = ProcessingJob(
                job_id=f"job_{uuid.uuid4().hex[:12]}",
                asset_id=asset.id,
                status=JobStatus.PROCESSING.value,
                current_stage="VALIDATING",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(job)
            db.flush()

        # Pipeline boundary dependencies
        if extractor is None:
            extractor = DeterministicContentExtractor()
        if chunker is None:
            chunker = DeterministicContentChunker()
        if mapper is None:
            mapper = DeterministicContentMapper()
        if generator is None:
            generator = DeterministicAssessmentGenerator()

        chunks: list[ContentChunk] = []
        candidates: list[CandidateAssessment] = []

        try:
            # 1. VALIDATING
            ContentService.transition_asset_status(asset, ContentStatus.VALIDATING.value)
            job.status = JobStatus.PROCESSING.value
            job.current_stage = "VALIDATING"
            job.started_at = datetime.now(timezone.utc)
            db.flush()

            # 2. PROCESSING & EXTRACTION
            ContentService.transition_asset_status(asset, ContentStatus.PROCESSING.value)
            job.current_stage = "EXTRACTING"
            db.flush()

            content_bytes = content_bytes_override or b"MoSPI Official Statistics Training Manual. Data verification and survey procedures."
            extracted_doc = extractor.extract(asset.filename, asset.media_type, content_bytes)

            ContentService.transition_asset_status(asset, ContentStatus.EXTRACTED.value)
            job.current_stage = "EXTRACTED"
            db.flush()

            # 3. STRUCTURED CHUNKING
            ContentService.transition_asset_status(asset, ContentStatus.STRUCTURED.value)
            job.current_stage = "CHUNKING"
            db.flush()

            chunked_blocks = chunker.chunk(extracted_doc.sections)

            # Persist ContentChunk entities
            latest_version = db.execute(
                select(ContentVersion)
                .where(ContentVersion.asset_id == asset.id)
                .order_by(ContentVersion.version_number.desc())
            ).scalar_one_or_none()
            version_id = latest_version.id if latest_version else None

            for blk in chunked_blocks:
                chunk_rec = ContentChunk(
                    asset_id=asset.id,
                    version_id=version_id,
                    chunk_index=blk.chunk_index,
                    chunk_type=blk.chunk_type,
                    content=blk.content,
                    token_count=blk.token_count,
                    metadata_json=json.dumps(blk.metadata),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(chunk_rec)
                chunks.append(chunk_rec)
            db.flush()

            # 4. MAPPING & CANDIDATE GENERATION
            ContentService.transition_asset_status(asset, ContentStatus.MAPPED.value)
            job.current_stage = "MAPPING"
            db.flush()

            for blk in chunked_blocks:
                concept_mappings = mapper.map_chunk(db, blk)
                chunk_candidates = generator.generate_candidates(db, asset.asset_id, blk, concept_mappings)
                candidates.extend(chunk_candidates)

            # 5. READY
            ContentService.transition_asset_status(asset, ContentStatus.READY.value)
            job.status = JobStatus.COMPLETED.value
            job.current_stage = "READY"
            job.completed_at = datetime.now(timezone.utc)
            job.stage_progress_json = json.dumps({
                "chunks_count": len(chunks),
                "candidates_count": len(candidates),
                "completed": True,
            })
            asset.error_message = None

            db.commit()
            db.refresh(asset)
            db.refresh(job)
            return asset, job, chunks, candidates

        except Exception as exc:
            db.rollback()
            # Mark as FAILED on error
            asset.status = ContentStatus.FAILED.value
            asset.error_message = str(exc)
            job.status = JobStatus.FAILED.value
            job.error_details = str(exc)
            job.updated_at = datetime.now(timezone.utc)
            db.add(asset)
            db.add(job)
            db.commit()
            raise exc

    @staticmethod
    def retry_processing_job(db: Session, asset_id: str) -> tuple[ContentAsset, ProcessingJob]:
        """Retry a failed processing job."""
        asset = db.execute(
            select(ContentAsset).where(ContentAsset.asset_id == asset_id)
        ).scalar_one_or_none()
        if not asset:
            raise ValueError(f"Content asset '{asset_id}' not found.")

        job = db.execute(
            select(ProcessingJob)
            .where(ProcessingJob.asset_id == asset.id)
            .order_by(ProcessingJob.created_at.desc())
        ).scalar_one_or_none()

        if not job:
            raise ValueError(f"No processing job found for asset '{asset_id}'.")

        job.retry_count += 1
        job.status = JobStatus.QUEUED.value
        job.error_details = None
        asset.status = ContentStatus.UPLOADED.value
        asset.error_message = None
        db.commit()

        asset, job, _, _ = ContentService.process_content_asset(db, asset_id)
        return asset, job

    @staticmethod
    def retire_content_asset(db: Session, asset_id: str) -> ContentAsset:
        asset = db.execute(
            select(ContentAsset).where(ContentAsset.asset_id == asset_id)
        ).scalar_one_or_none()
        if not asset:
            raise ValueError(f"Content asset '{asset_id}' not found.")

        ContentService.transition_asset_status(asset, ContentStatus.RETIRED.value)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def list_content_assets(
        db: Session,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ContentAsset]:
        stmt = select(ContentAsset)
        if status:
            stmt = stmt.where(ContentAsset.status == status.upper())
        stmt = stmt.offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_content_asset(db: Session, asset_id: str) -> ContentAsset | None:
        return db.execute(
            select(ContentAsset).where(ContentAsset.asset_id == asset_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_asset_chunks(db: Session, asset_id: str) -> list[ContentChunk]:
        asset = ContentService.get_content_asset(db, asset_id)
        if not asset:
            return []
        return db.execute(
            select(ContentChunk).where(ContentChunk.asset_id == asset.id).order_by(ContentChunk.chunk_index)
        ).scalars().all()
