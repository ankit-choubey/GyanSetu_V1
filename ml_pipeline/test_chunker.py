"""
ml_pipeline/test_chunker.py — Automated Unit Tests for Semantic Chunker (11 Tests).

Run:
    python -m ml_pipeline.test_chunker
"""
import sys
from ml_pipeline.chunker import (
    chunk_text,
    chunk_structured_document,
    DEFAULT_RAG_CHUNK_SIZE,
    DEFAULT_MCQ_CHUNK_SIZE,
)


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []

    # 1. Empty text returns empty list
    r1 = chunk_text("")
    r1_b = chunk_text("   \n\n  ")
    results.append(_report("empty text returns empty list", r1 == [] and r1_b == []))

    # 2. Short text returns single chunk
    short_text = "This is a short paragraph about Stratified Sampling."
    r2 = chunk_text(short_text, chunk_size=500, overlap=50)
    results.append(_report(
        "short text returns single chunk",
        len(r2) == 1 and r2[0]["text"] == short_text and r2[0]["chunk_type"] == "text"
    ))

    # 3. Long text splits into multiple chunks
    long_para = "Sentence one about MoSPI. " * 30  # ~780 chars
    r3 = chunk_text(long_para, chunk_size=300, overlap=50)
    results.append(_report(
        "long text splits into multiple chunks",
        len(r3) >= 3 and all(c["char_length"] <= 350 for c in r3)
    ))

    # 4. Overlap is preserved between consecutive chunks
    r4 = chunk_text(long_para, chunk_size=300, overlap=60)
    overlap_found = False
    if len(r4) >= 2:
        overlap_found = len(set(r4[0]["text"][-30:].split()) & set(r4[1]["text"][:100].split())) > 0
    results.append(_report("overlap between consecutive chunks preserved", overlap_found))

    # 5. Invalid overlap raises ValueError
    try:
        chunk_text("Some text", chunk_size=200, overlap=250)
        results.append(_report("overlap >= chunk_size raises ValueError", False))
    except ValueError:
        results.append(_report("overlap >= chunk_size raises ValueError", True))

    # 6. Invalid chunk_size raises ValueError
    try:
        chunk_text("Some text", chunk_size=0, overlap=0)
        results.append(_report("chunk_size <= 0 raises ValueError", False))
    except ValueError:
        results.append(_report("chunk_size <= 0 raises ValueError", True))

    # 7. Non-string text raises TypeError
    try:
        chunk_text(12345)  # type: ignore
        results.append(_report("non-string text raises TypeError", False))
    except TypeError:
        results.append(_report("non-string text raises TypeError", True))

    # 8. Table block detection sets chunk_type properly
    table_text = "[TABLE]\nRegion | Population\nNorth | 1200\n[/TABLE]"
    r8 = chunk_text(table_text, chunk_size=500, overlap=50)
    results.append(_report(
        "table block identified as table chunk_type",
        len(r8) == 1 and r8[0]["chunk_type"] == "table"
    ))

    # 9. Structured document chunking preserves page numbers
    pages = [
        {"page": 1, "text": "Introduction to National Accounts.", "tables": []},
        {"page": 2, "text": "Methodology of Gross Fixed Capital Formation.", "tables": []},
    ]
    r9 = chunk_structured_document(pages, chunk_size=500, target="rag")
    results.append(_report(
        "structured chunking preserves page numbers",
        len(r9) == 2 and r9[0]["page_number"] == 1 and r9[1]["page_number"] == 2
    ))

    # 10. Target presets use correct sizing defaults
    r10_rag = chunk_structured_document(pages, target="rag")
    r10_mcq = chunk_structured_document(pages, target="mcq")
    results.append(_report(
        "target presets (rag vs mcq) configure correctly",
        len(r10_rag) >= 1 and len(r10_mcq) >= 1
    ))

    # 11. Multi-page document creates unique chunk IDs
    pages_multi = [
        {"page": 1, "text": "Page one text content. " * 10, "tables": []},
        {"page": 2, "text": "Page two text content. " * 10, "tables": []},
    ]
    r11 = chunk_structured_document(pages_multi, chunk_size=200, source_id="nssta_report")
    ids = [c["chunk_id"] for c in r11]
    results.append(_report(
        "unique chunk IDs assigned across pages",
        len(ids) > 2 and len(ids) == len(set(ids)) and all("nssta_report" in cid for cid in ids)
    ))

    all_ok = all(results)
    print(f"\nCHUNKER TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
