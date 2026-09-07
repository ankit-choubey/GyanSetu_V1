"""
ml_pipeline/chunker.py — Token/character-aware semantic chunking.

Implements reusable document chunking per GyanSetu Build Guide §11:
- RAG target: ~500–1000 characters with ~100 character overlap.
- MCQ generation target: ~1000–2000 characters with ~200 character overlap.
- Preserves table block boundaries ([TABLE]...[/TABLE]) when possible.
- Tracks source page numbers and metadata on every chunk for source attribution.
"""
from __future__ import annotations

import re
from typing import Any


DEFAULT_RAG_CHUNK_SIZE = 800
DEFAULT_RAG_OVERLAP = 100

DEFAULT_MCQ_CHUNK_SIZE = 1600
DEFAULT_MCQ_OVERLAP = 200


def _approx_token_count(text: str) -> int:
    """Approximates token count based on whitespace tokenization and word boundaries."""
    if not text:
        return 0
    words = len(text.split())
    return max(words, len(text) // 4)


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_RAG_CHUNK_SIZE,
    overlap: int = DEFAULT_RAG_OVERLAP,
    source_id: str = "doc",
    base_page: int = 1,
) -> list[dict[str, Any]]:
    """
    Slices raw plain text into overlapping chunks respecting paragraph/sentence boundaries.

    Args:
        text: The source text to chunk.
        chunk_size: Target character length per chunk (must be > overlap).
        overlap: Character overlap between consecutive chunks.
        source_id: Identifier for source document.
        base_page: Page number attribution for raw text.

    Returns:
        List of chunk dictionaries with metadata.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and strictly less than chunk_size")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[dict[str, Any]] = []
    current_buf: list[str] = []
    current_len = 0
    chunk_idx = 0

    def _flush_buffer():
        nonlocal chunk_idx, current_buf, current_len
        if not current_buf:
            return
        chunk_str = "\n\n".join(current_buf).strip()
        if chunk_str:
            has_table = "[TABLE]" in chunk_str and "[/TABLE]" in chunk_str
            chunk_type = "table" if (chunk_str.startswith("[TABLE]") and chunk_str.endswith("[/TABLE]")) else ("mixed" if has_table else "text")
            chunks.append({
                "chunk_id": f"{source_id}_chunk_{chunk_idx:04d}",
                "text": chunk_str,
                "page_number": base_page,
                "page_numbers": [base_page],
                "chunk_type": chunk_type,
                "char_length": len(chunk_str),
                "approx_tokens": _approx_token_count(chunk_str),
                "source_id": source_id,
            })
            chunk_idx += 1

    for para in paragraphs:
        if len(para) > chunk_size:
            _flush_buffer()
            current_buf = []
            current_len = 0

            raw_sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", para) if s.strip()]
            sentences: list[str] = []
            for s in raw_sentences:
                if len(s) > chunk_size:
                    # Break unpunctuated overlong speech segment on word boundaries
                    words = s.split()
                    w_buf: list[str] = []
                    w_len = 0
                    for w in words:
                        if w_len + len(w) + 1 > chunk_size and w_buf:
                            sentences.append(" ".join(w_buf))
                            w_buf = []
                            w_len = 0
                        w_buf.append(w)
                        w_len += len(w) + 1
                    if w_buf:
                        sentences.append(" ".join(w_buf))
                else:
                    sentences.append(s)

            sub_buf: list[str] = []
            sub_len = 0

            for sent in sentences:
                if sub_len + len(sent) > chunk_size and sub_buf:
                    sub_str = " ".join(sub_buf).strip()
                    chunks.append({
                        "chunk_id": f"{source_id}_chunk_{chunk_idx:04d}",
                        "text": sub_str,
                        "page_number": base_page,
                        "page_numbers": [base_page],
                        "chunk_type": "text",
                        "char_length": len(sub_str),
                        "approx_tokens": _approx_token_count(sub_str),
                        "source_id": source_id,
                    })
                    chunk_idx += 1

                    overlap_chars = sub_str[-overlap:] if overlap > 0 else ""
                    sub_buf = [overlap_chars] if overlap_chars else []
                    sub_len = len(overlap_chars)

                sub_buf.append(sent)
                sub_len += len(sent) + 1

            if sub_buf:
                current_buf = sub_buf
                current_len = sub_len
            continue

        if current_len + len(para) + 2 > chunk_size and current_buf:
            _flush_buffer()
            last_text = "\n\n".join(current_buf)
            overlap_prefix = last_text[-overlap:] if overlap > 0 else ""
            current_buf = [overlap_prefix, para] if overlap_prefix else [para]
            current_len = len(overlap_prefix) + len(para) + (2 if overlap_prefix else 0)
        else:
            current_buf.append(para)
            current_len += len(para) + 2

    _flush_buffer()
    return chunks


def chunk_structured_document(
    pages: list[dict[str, Any]],
    chunk_size: int | None = None,
    overlap: int | None = None,
    target: str = "rag",
    source_id: str = "doc",
) -> list[dict[str, Any]]:
    """
    Chunks output from document_processor.process_document_structured(),
    preserving page boundaries, table integrity, and page number attributions.

    Args:
        pages: List of page dicts with 'page', 'text', 'tables', 'content_type'.
        chunk_size: Explicit chunk character size (defaults based on target).
        overlap: Explicit overlap size (defaults based on target).
        target: 'rag' (smaller, overlapping) or 'mcq' (larger, topical).
        source_id: Document identifier.

    Returns:
        List of chunks with detailed page and source attributions.
    """
    if not isinstance(pages, list):
        raise TypeError("pages must be a list of page dicts")
    if not pages:
        return []

    if target == "mcq":
        size = chunk_size or DEFAULT_MCQ_CHUNK_SIZE
        ov = overlap or DEFAULT_MCQ_OVERLAP
    else:
        size = chunk_size or DEFAULT_RAG_CHUNK_SIZE
        ov = overlap or DEFAULT_RAG_OVERLAP

    all_chunks: list[dict[str, Any]] = []
    chunk_counter = 0

    for page_dict in pages:
        page_num = page_dict.get("page", 1)
        page_text = page_dict.get("text", "").strip()
        tables = page_dict.get("tables", [])

        table_blocks: list[str] = []
        for tbl in tables:
            if tbl:
                lines = ["[TABLE]"]
                lines.extend(" | ".join(str(cell or "") for cell in row) for row in tbl)
                lines.append("[/TABLE]")
                table_blocks.append("\n".join(lines))

        combined_parts = []
        if page_text:
            combined_parts.append(page_text)
        combined_parts.extend(table_blocks)
        full_page_content = "\n\n".join(combined_parts).strip()

        if not full_page_content:
            continue

        page_chunks = chunk_text(
            text=full_page_content,
            chunk_size=size,
            overlap=ov,
            source_id=source_id,
            base_page=page_num,
        )

        for ch in page_chunks:
            ch["chunk_id"] = f"{source_id}_p{page_num:03d}_{chunk_counter:04d}"
            all_chunks.append(ch)
            chunk_counter += 1

    return all_chunks
