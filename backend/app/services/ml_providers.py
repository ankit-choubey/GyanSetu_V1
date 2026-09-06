from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentItem
from app.services.evening_interfaces import (
    ABSTENTION_MESSAGE,
    ChatAnswer,
    ChatRequest,
    DocumentProcessResult,
    DocumentIngestionProvider,
    RagProvider,
)
from app.services.ml_interfaces import (
    ProposedQuestion,
    QuestionSelectionRequest,
    QuestionSelector,
)
from ml_pipeline.api_interface import (
    query_gyansetu_chatbot,
    get_next_adaptive_mcq,
)
from ml_pipeline.chunker import chunk_structured_document
from ml_pipeline.document_processor import process_document_structured
from ml_pipeline.vector_store import add_chunks


class ChromaRagProvider(RagProvider):
    """Grounded RAG provider connected to ChromaDB with strict abstention."""

    def answer(self, request: ChatRequest) -> ChatAnswer:
        if not request.question or not request.question.strip():
            return ChatAnswer(
                status="ABSTAINED",
                answer=ABSTENTION_MESSAGE,
                sources=(),
                source_mode="STRICT_ABSTENTION",
            )
        try:
            res = query_gyansetu_chatbot(
                query=request.question,
                competency_filter=str(request.competency_id) if request.competency_id else None,
                similarity_threshold=0.15,
            )
            if res.get("abstained"):
                return ChatAnswer(
                    status="ABSTAINED",
                    answer=res.get("answer", ABSTENTION_MESSAGE),
                    sources=(),
                    source_mode="UNAVAILABLE",
                )
            return ChatAnswer(
                status="SUCCESS",
                answer=res.get("answer", ""),
                sources=tuple(res.get("sources", ())),
                source_mode="GROUNDED_RAG",
            )
        except Exception:
            return ChatAnswer(
                status="ABSTAINED",
                answer=ABSTENTION_MESSAGE,
                sources=(),
                source_mode="UNAVAILABLE",
            )


class PipelineDocumentIngestionProvider(DocumentIngestionProvider):
    """Processes, extracts, chunks, and indexes training documents into ChromaDB."""

    def process(self, filename: str, content_type: str | None, content: bytes) -> DocumentProcessResult:
        if not content:
            return DocumentProcessResult(
                status="EMPTY_CONTENT",
                trusted=False,
                coverage=0.0,
                warning="Uploaded document is empty.",
            )

        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".ppt", ".pptx"}:
            return DocumentProcessResult(
                status="UNSUPPORTED_FORMAT",
                trusted=False,
                coverage=0.0,
                warning=f"Unsupported format: {suffix}",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = os.path.join(tmpdir, f"upload_{filename}")
            try:
                with open(tmp_path, "wb") as f:
                    f.write(content)

                pages = process_document_structured(tmp_path)
            except ValueError as e:
                return DocumentProcessResult(
                    status="CORRUPTED_FILE",
                    trusted=False,
                    coverage=0.0,
                    warning=f"File could not be parsed: {e}",
                )
            except Exception as e:
                return DocumentProcessResult(
                    status="UNKNOWN_PROCESSING_ERROR",
                    trusted=False,
                    coverage=0.0,
                    warning=f"Processing failed: {e}",
                )

            if not pages:
                return DocumentProcessResult(
                    status="EMPTY_CONTENT",
                    trusted=False,
                    coverage=0.0,
                    warning="No extractable text or pages found.",
                )

            successful_pages: list[int] = []
            failed_pages: list[int] = []
            ocr_used = False

            for page in pages:
                p_num = page.page_number
                if page.content_type == "ocr":
                    ocr_used = True
                if page.content_type in {"text", "table", "ocr", "pptx_slide"} and page.text.strip():
                    successful_pages.append(p_num)
                else:
                    failed_pages.append(p_num)

            # Chunk and index into ChromaDB
            try:
                chunks = chunk_structured_document(pages, target="rag", source_id=filename)
                if chunks:
                    add_chunks(chunks)
            except Exception:
                pass

            total_pages = len(pages)
            coverage = len(successful_pages) / total_pages if total_pages > 0 else 0.0
            trusted = coverage >= 0.70

            status = "SUCCESS" if trusted else "PARTIAL_EXTRACTION"
            warning = None if trusted else "Partial document extraction; coverage fell below confidence threshold."

            return DocumentProcessResult(
                status=status,
                trusted=trusted,
                coverage=round(coverage, 2),
                successful_pages=tuple(successful_pages),
                failed_pages=tuple(failed_pages),
                ocr_used=ocr_used,
                warning=warning,
            )


class AdaptiveItemQuestionSelector(QuestionSelector):
    """Adaptive question selector querying the stored item bank and using ML adaptive logic."""

    def __init__(self, db: Session, session_history: list[dict[str, Any]] | None = None):
        self.db = db
        self.session_history = session_history or []

    def select_next_question(self, request: QuestionSelectionRequest) -> ProposedQuestion | Mapping[str, Any]:
        stmt = select(AssessmentItem).where(
            AssessmentItem.competency_id == request.competency_id,
            AssessmentItem.user_id.is_(None),
        )
        items = self.db.execute(stmt).scalars().all()

        if not items:
            raise ValueError(f"No stored assessment items available for competency {request.competency_id}")

        item_bank: list[dict[str, Any]] = []
        for item in items:
            try:
                options = json.loads(item.options_json)
            except Exception:
                continue
            item_bank.append({
                "question_id": item.id,
                "id": item.id,
                "competency_id": item.competency_id,
                "competency": str(item.competency_id),
                "subskill_id": item.subskill_id,
                "subskill": request.subskill_name or "",
                "question": item.question_text,
                "options": options,
                "correct_answer": item.correct_option,
                "difficulty": item.difficulty or "medium",
                "source_reference": item.source_reference,
            })

        if not item_bank:
            raise ValueError(f"No valid assessment items found for competency {request.competency_id}")

        candidates = item_bank
        if request.subskill_id is not None:
            sub_candidates = [i for i in item_bank if i.get("subskill_id") == request.subskill_id]
            if sub_candidates:
                candidates = sub_candidates

        selection_result = get_next_adaptive_mcq(
            item_bank=candidates,
            session_history=self.session_history,
            competency=str(request.competency_id),
        )

        chosen = selection_result.get("next_question")
        if not chosen:
            chosen = candidates[0]

        qid = chosen.get("question_id") or chosen.get("id") or items[0].id
        return ProposedQuestion(
            question_id=int(qid),
            competency_id=request.competency_id,
            subskill_id=request.subskill_id,
            question_text=str(chosen.get("question", "")),
            options=tuple(str(opt) for opt in chosen.get("options", ())),
            difficulty=str(chosen.get("difficulty", "medium")),
            source_reference=chosen.get("source_reference"),
            correct_option=None,
        )
