from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin
from app.dependencies import get_db
from app.models.user import User
from app.schemas.evening import DocumentUploadResponse
from app.services.content_ingestion import ContentIngestionError, ContentIngestionService
from app.services.evening_interfaces import DocumentIngestionProvider

router = APIRouter(tags=["content"])

_ALLOWED_EXTENSIONS = {".pdf", ".pptx"}


def get_document_processor(db: Session = Depends(get_db)) -> DocumentIngestionProvider:
    return ContentIngestionService(db)


@router.post("/content/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    processor: DocumentIngestionProvider = Depends(get_document_processor),
) -> DocumentUploadResponse:
    extension = Path(file.filename or "").suffix.casefold()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FORMAT")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMPTY_CONTENT")

    try:
        db.rollback()
        with db.begin():
            result = processor.process(file.filename or "unnamed", file.content_type, content)
            return DocumentUploadResponse(
                status=result.status,
                filename=file.filename or "unnamed",
                trusted=result.trusted,
                coverage=result.coverage,
                successful_pages=list(result.successful_pages),
                failed_pages=list(result.failed_pages),
                ocr_used=result.ocr_used,
                warning=result.warning,
            )
    except ContentIngestionError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Content ingestion failed; no changes were saved") from exc
