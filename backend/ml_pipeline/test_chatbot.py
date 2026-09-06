"""
ml_pipeline/test_chatbot.py — Automated Unit Tests for RAG Chatbot (5 Tests).

Run:
    python -m ml_pipeline.test_chatbot
"""
import sys

from ml_pipeline.chatbot import (
    ask_chatbot,
    format_context,
    ABSTENTION_MESSAGE,
)
from ml_pipeline.vector_store import add_chunks, clear_collection

CHATBOT_TEST_COLL = "test_chatbot_collection"


def _report(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_tests() -> bool:
    results = []
    clear_collection(CHATBOT_TEST_COLL)

    # Ingest 2 verified test chunks
    test_chunks = [
        {
            "chunk_id": "cb_chunk_001",
            "text": "Neyman Allocation calculates sample size per stratum based on stratum population and standard deviation.",
            "page_number": 8,
            "chunk_type": "text",
            "char_length": 105,
            "competency": "Sampling Design",
        },
        {
            "chunk_id": "cb_chunk_002",
            "text": "The Laspeyres price index uses base period consumption baskets to measure inflation.",
            "page_number": 19,
            "chunk_type": "text",
            "char_length": 90,
            "competency": "Price Statistics",
        }
    ]
    add_chunks(test_chunks, collection_name=CHATBOT_TEST_COLL)

    # 1. Empty query triggers strict abstention immediately
    r1 = ask_chatbot("", collection_name=CHATBOT_TEST_COLL)
    results.append(_report(
        "empty query triggers strict abstention",
        r1["abstained"] is True and r1["answer"] == ABSTENTION_MESSAGE
    ))

    # 2. Out-of-domain query with high threshold triggers strict abstention
    r2 = ask_chatbot(
        "What is quantum entanglement in theoretical physics?",
        collection_name=CHATBOT_TEST_COLL,
        similarity_threshold=0.85,
    )
    results.append(_report(
        "unsupported topic triggers strict abstention",
        r2["abstained"] is True and r2["answer"] == ABSTENTION_MESSAGE
    ))

    # 3. Relevant query retrieves chunks and cites sources
    mock_reply = "According to [Page 8], Neyman Allocation allocates sample size proportional to stratum standard deviation."
    r3 = ask_chatbot(
        "Neyman Allocation standard deviation",
        collection_name=CHATBOT_TEST_COLL,
        similarity_threshold=0.05,
        mock_llm_reply=mock_reply,
    )
    r3_ok = (
        r3["abstained"] is False
        and len(r3["sources"]) >= 1
        and r3["sources"][0]["page_number"] == 8
        and "[Page 8]" in r3["answer"]
    )
    results.append(_report("grounded query returns citations and source metadata", r3_ok))

    # 4. Context formatting includes source and page markers
    hits = [
        {"text": "Sample text", "metadata": {"page_number": 12, "source_id": "NSS_68"}}
    ]
    formatted = format_context(hits)
    r4_ok = "[Source: NSS_68 | Page: 12]" in formatted and "Sample text" in formatted
    results.append(_report("context formatting contains source and page citations", r4_ok))

    # 5. Abstention message matches exact required string
    expected_msg = "I don't have enough verified information in the official training materials to answer this question accurately."
    results.append(_report(
        "abstention message strictly equals official specification",
        ABSTENTION_MESSAGE == expected_msg
    ))

    clear_collection(CHATBOT_TEST_COLL)
    all_ok = all(results)
    print(f"\nCHATBOT TEST SUITE: {'PASS' if all_ok else 'FAIL'} ({sum(results)}/{len(results)} passed)")
    return all_ok


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
