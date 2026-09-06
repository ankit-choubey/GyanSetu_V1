"""
ml_pipeline/api_interface.py — Clean Contract Interface for FastAPI Backend.

Provides typed entry points for the Backend team (Utkarsh) to integrate ML/AI capabilities:
- Document Ingestion & Vector Indexing (/api/content/upload)
- Assessment MCQ Generation & Quality Scoring (/api/assessment/generate)
- Adaptive Question Selection (/api/assessment/next)
- Grounded RAG Chatbot (/api/chat)
- Assessment Response Evaluation & Feedback (/api/assessment/submit)
"""
from __future__ import annotations

from typing import Any

from ml_pipeline.chunker import chunk_structured_document
from ml_pipeline.document_processor import process_document_structured
from ml_pipeline.mcq_generator import generate_mcqs
from ml_pipeline.mcq_validator import validate_mcqs
from ml_pipeline.mcq_scorer import score_mcq_quality, shuffle_mcq_options
from ml_pipeline.vector_store import add_chunks, count_chunks
from ml_pipeline.chatbot import ask_chatbot
from ml_pipeline.adaptive_selector import select_next_question
from ml_pipeline.explanation_generator import generate_feedback


def ingest_training_document(file_path: str, competency: str | None = None) -> dict[str, Any]:
    """
    Ingests, extracts, chunks, and vectorizes a training PDF/PPTX into ChromaDB.
    """
    structured_pages = process_document_structured(file_path)
    chunks = chunk_structured_document(
        structured_pages,
        target="rag",
        source_id=file_path.split("/")[-1].split("\\")[-1],
    )
    if competency:
        for c in chunks:
            c["competency"] = competency

    added = add_chunks(chunks)
    return {
        "status": "success",
        "file_path": file_path,
        "total_pages": len(structured_pages),
        "chunks_indexed": added,
        "total_collection_chunks": count_chunks(),
    }


def generate_and_validate_assessment_mcqs(
    content: str,
    competency: str,
    num_questions: int = 5,
    difficulty: str = "medium",
) -> list[dict[str, Any]]:
    """
    Generates, validates, and quality-scores MCQs with shuffled option distribution.
    """
    raw_mcqs = generate_mcqs(
        content=content,
        competency=competency,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    validated = validate_mcqs(raw_mcqs, content)
    final_items = []
    for i, report in enumerate(validated):
        mcq = dict(raw_mcqs[i])
        mcq["validation"] = report
        if report.get("valid"):
            scored = score_mcq_quality(mcq, content)
            shuffled = shuffle_mcq_options(scored)
            final_items.append(shuffled)
        else:
            final_items.append(mcq)
    return final_items


def get_next_adaptive_mcq(
    item_bank: list[dict[str, Any]],
    session_history: list[dict[str, Any]],
    competency: str | None = None,
) -> dict[str, Any]:
    """
    Picks the next adaptive assessment item based on history.
    """
    return select_next_question(
        item_bank=item_bank,
        session_history=session_history,
        competency=competency,
    )


def query_gyansetu_chatbot(
    query: str,
    competency_filter: str | None = None,
    similarity_threshold: float = 0.15,
) -> dict[str, Any]:
    """
    Queries the grounded RAG virtual assistant.
    """
    return ask_chatbot(
        query=query,
        competency_filter=competency_filter,
        similarity_threshold=similarity_threshold,
    )


def evaluate_officer_submission(
    mcq: dict[str, Any],
    selected_letter: str,
) -> dict[str, Any]:
    """
    Evaluates an officer's selected answer and generates diagnostic feedback.
    """
    return generate_feedback(
        mcq=mcq,
        selected_letter=selected_letter,
    )
