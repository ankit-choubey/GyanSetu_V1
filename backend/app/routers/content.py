from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.dependencies import get_current_admin
from app.models.user import User
from app.schemas.evening import DocumentUploadResponse
from app.services.evening_interfaces import DocumentIngestionProvider, UnavailableDocumentIngestionProvider

router = APIRouter(tags=["content"])

_ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}


def get_document_processor() -> DocumentIngestionProvider:
    return UnavailableDocumentIngestionProvider()


@router.post("/content/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_admin),
    processor: DocumentIngestionProvider = Depends(get_document_processor),
) -> DocumentUploadResponse:
    extension = Path(file.filename or "").suffix.casefold()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_FORMAT")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMPTY_CONTENT")

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
