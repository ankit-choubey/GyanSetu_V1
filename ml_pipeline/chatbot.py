"""
ml_pipeline/chatbot.py — Grounded RAG Chatbot with Strict Abstention & Source Attribution.

Implements the GyanSetu virtual assistant per Build Guide §11:
- Retrieval-Augmented Generation using local ChromaDB vector store.
- Strict Abstention: If similarity score < SIMILARITY_THRESHOLD, never speculate.
  Returns exact standard refusal: "I don't have enough verified information in the official training materials to answer this question accurately."
- Explicit page/table attribution citations.
"""
from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_PRIMARY
from ml_pipeline.vector_store import query_chunks

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "chatbot_prompt.txt")
ABSTENTION_MESSAGE = "I don't have enough verified information in the official training materials to answer this question accurately."
DEFAULT_SIMILARITY_THRESHOLD = 0.15

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment or ml_pipeline/.env")
        _client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    return _client


def _load_prompt_template() -> str:
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_context(hits: list[dict[str, Any]]) -> str:
    """Formats retrieved vector hits into clean cited context blocks."""
    blocks = []
    for hit in hits:
        page = hit.get("metadata", {}).get("page_number", "Unknown")
        source = hit.get("metadata", {}).get("source_id", "Doc")
        text = hit.get("text", "").strip()
        blocks.append(f"--- [Source: {source} | Page: {page}] ---\n{text}")
    return "\n\n".join(blocks)


def ask_chatbot(
    query: str,
    competency_filter: str | None = None,
    collection_name: str = "gyansetu_materials",
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    max_sources: int = 3,
    mock_llm_reply: str | None = None,
) -> dict[str, Any]:
    """
    Core RAG chatbot endpoint.

    Args:
        query: Officer's statistical inquiry.
        competency_filter: Optional competency metadata restriction.
        collection_name: Target ChromaDB collection.
        similarity_threshold: Minimum cosine similarity score required to attempt an answer.
        max_sources: Top-k chunks to retrieve.
        mock_llm_reply: For offline testing without network/Groq calls.

    Returns:
        Structured response dictionary.
    """
    if not query or not str(query).strip():
        return {
            "query": query,
            "answer": ABSTENTION_MESSAGE,
            "sources": [],
            "abstained": True,
            "confidence": 0.0,
        }

    clean_query = query.strip()
    where_filter = {"competency": competency_filter} if competency_filter else None

    # 1. Retrieve candidate chunks from ChromaDB
    hits = query_chunks(
        clean_query,
        n_results=max_sources,
        where_filter=where_filter,
        collection_name=collection_name,
    )

    # 2. Evaluate similarity threshold
    best_score = hits[0]["similarity_score"] if hits else 0.0
    if not hits or best_score < similarity_threshold:
        return {
            "query": clean_query,
            "answer": ABSTENTION_MESSAGE,
            "sources": [],
            "abstained": True,
            "confidence": round(best_score, 4),
        }

    # 3. Assemble verified sources metadata
    sources = [
        {
            "chunk_id": h["chunk_id"],
            "page_number": h.get("metadata", {}).get("page_number", 1),
            "similarity_score": h["similarity_score"],
            "preview": h["text"][:120] + "..." if len(h["text"]) > 120 else h["text"],
        }
        for h in hits
    ]

    # 4. Synthesize answer with grounding prompt
    if mock_llm_reply is not None:
        answer_text = mock_llm_reply
    else:
        context_str = format_context(hits)
        prompt_tmpl = _load_prompt_template()
        prompt = prompt_tmpl.replace("{context}", context_str).replace("{question}", clean_query)

        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        answer_text = response.choices[0].message.content.strip()

    # Double check if model itself abstained
    abstained = (ABSTENTION_MESSAGE in answer_text) or answer_text == ABSTENTION_MESSAGE

    return {
        "query": clean_query,
        "answer": answer_text,
        "sources": sources if not abstained else [],
        "abstained": abstained,
        "confidence": round(best_score, 4),
    }
