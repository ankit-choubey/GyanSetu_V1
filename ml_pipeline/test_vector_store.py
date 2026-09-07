"""
ml_pipeline/test_vector_store.py — Automated Unit Tests for ChromaDB Vector Store (8 Tests).

Run:
    python -m ml_pipeline.test_vector_store
"""
import os
import sys

from ml_pipeline.vector_store import (
    add_chunks,
    query_chunks,
    count_chunks,
    clear_collection,
)

TEST_COLL = "test_chroma_suite"


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []
    clear_collection(TEST_COLL)

    # 1. Empty chunks returns 0
    r1 = add_chunks([], collection_name=TEST_COLL)
    results.append(_report("adding empty chunks list returns 0", r1 == 0 and count_chunks(TEST_COLL) == 0))

    # 2. Add valid chunks increases count
    sample_chunks = [
        {
            "chunk_id": "test_chunk_001",
            "text": "Stratified sampling divides population into homogeneous strata to minimize variance.",
            "page_number": 4,
            "chunk_type": "text",
            "char_length": 80,
            "competency": "Sampling Design",
        },
        {
            "chunk_id": "test_chunk_002",
            "text": "Gross Domestic Product (GDP) is compiled quarterly following National Accounts Statistics.",
            "page_number": 12,
            "chunk_type": "text",
            "char_length": 85,
            "competency": "National Accounts",
        },
        {
            "chunk_id": "test_chunk_003",
            "text": "Paasche and Laspeyres price indices are used in Consumer Price Index calculations.",
            "page_number": 25,
            "chunk_type": "text",
            "char_length": 80,
            "competency": "Price Statistics",
        },
    ]
    added = add_chunks(sample_chunks, collection_name=TEST_COLL)
    results.append(_report("adding valid chunks increases count", added == 3 and count_chunks(TEST_COLL) == 3))

    # 3. Querying with keywords retrieves correct matching chunk
    hits = query_chunks("stratified sampling variance", n_results=1, collection_name=TEST_COLL)
    match_ok = len(hits) == 1 and hits[0]["chunk_id"] == "test_chunk_001" and hits[0]["similarity_score"] > 0.0
    results.append(_report("semantic query retrieves top relevant chunk", match_ok))

    # 4. Respects n_results limit
    hits_two = query_chunks("statistics calculation", n_results=2, collection_name=TEST_COLL)
    results.append(_report("query respects n_results limit", len(hits_two) == 2))

    # 5. Respects metadata where_filter
    hits_filtered = query_chunks(
        "sampling calculation",
        n_results=3,
        where_filter={"competency": "National Accounts"},
        collection_name=TEST_COLL,
    )
    filter_ok = len(hits_filtered) == 1 and hits_filtered[0]["chunk_id"] == "test_chunk_002"
    results.append(_report("metadata where_filter filters correctly", filter_ok))

    # 6. Page number and metadata preserved in output
    if hits:
        page_ok = hits[0]["metadata"].get("page_number") == 4
        results.append(_report("metadata fields (e.g. page_number) preserved in search hit", page_ok))
    else:
        results.append(_report("metadata fields preserved in search hit", False))

    # 7. Empty query returns empty list
    r7 = query_chunks("", collection_name=TEST_COLL)
    results.append(_report("empty query string returns empty list", r7 == []))

    # 8. Clear collection resets count
    clear_collection(TEST_COLL)
    results.append(_report("clear_collection resets count to 0", count_chunks(TEST_COLL) == 0))

    all_ok = all(results)
    print(f"\nVECTOR STORE TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
