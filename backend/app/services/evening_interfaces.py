from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

ABSTENTION_MESSAGE = "I don't have enough verified information in the official training materials to answer this question accurately."
SUPPORTED_DOCUMENT_FAILURES = {
    "UNSUPPORTED_FORMAT",
    "CORRUPTED_FILE",
    "EMPTY_CONTENT",
    "OCR_FAILURE",
    "ASR_FAILURE",
    "PARTIAL_EXTRACTION",
    "PROCESSING_TIMEOUT",
    "MAPPING_FAILURE",
    "UNKNOWN_PROCESSING_ERROR",
}


@dataclass(frozen=True)
class ChatRequest:
    question: str
    competency_id: int | None


@dataclass(frozen=True)
class ChatAnswer:
    status: str
    answer: str
    sources: tuple[str, ...] = ()
    source_mode: str = "UNAVAILABLE"


class RagProvider(Protocol):
    def answer(self, request: ChatRequest) -> ChatAnswer:
        ...


class UnavailableRagProvider:
    """Explicit fallback until the ML/RAG component is available."""

    def answer(self, request: ChatRequest) -> ChatAnswer:
        return ChatAnswer(
            status="ABSTAINED",
            answer=ABSTENTION_MESSAGE,
            source_mode="UNAVAILABLE",
        )


@dataclass(frozen=True)
class DocumentProcessResult:
    status: str
    trusted: bool
    coverage: float
    successful_pages: tuple[int, ...] = ()
    failed_pages: tuple[int, ...] = ()
    ocr_used: bool = False
    warning: str | None = None


@dataclass(frozen=True)
class ContentConceptResult:
    concept: str
    description: str
    subskills: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContentMappingResult:
    concept: str
    competency: str
    subskills: tuple[str, ...]
    confidence: float
    rationale: str


@dataclass(frozen=True)
class ContentProcessResult:
    status: str
    concepts: tuple[ContentConceptResult, ...] = ()
    competency_mappings: tuple[ContentMappingResult, ...] = ()
    source_reference: str | None = None
    metadata: dict[str, object] | None = None
    warnings: tuple[dict[str, str], ...] = ()
    errors: tuple[dict[str, str], ...] = ()


class DocumentIngestionProvider(Protocol):
    def process(
        self,
        filename: str,
        content_type: str | None,
        content: bytes,
        *,
        content_id: str | None = None,
        storage_reference: str | None = None,
    ) -> DocumentProcessResult | ContentProcessResult:
        ...


class UnavailableDocumentIngestionProvider:
    """Explicit fallback until the ML/document component is available."""

    def process(
        self,
        filename: str,
        content_type: str | None,
        content: bytes,
        *,
        content_id: str | None = None,
        storage_reference: str | None = None,
    ) -> DocumentProcessResult | ContentProcessResult:
        return DocumentProcessResult(
            status="UNKNOWN_PROCESSING_ERROR",
            trusted=False,
            coverage=0.0,
            warning="Document-ingestion component is not available; content was not trusted.",
        )
