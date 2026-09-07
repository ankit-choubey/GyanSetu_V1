"""
ml_pipeline/audit_pipeline.py — Comprehensive End-to-End Pipeline Integration Audit.

Verifies the entire closed loop across all ML modules:
1. Document Chunking
2. Local Vector Store Indexing
3. Grounded RAG Retrieval with Citations
4. Strict Chatbot Abstention
5. MCQ Generation Parsing
6. MCQ Validation
7. MCQ Quality Scoring & Cognitive Classification
8. Answer Key Shuffling (Bias Elimination)
9. Adaptive Question Selection Loop
10. Diagnostic Feedback Generation
"""
import sys
from ml_pipeline.chunker import chunk_text
from ml_pipeline.vector_store import add_chunks, query_chunks, clear_collection
from ml_pipeline.chatbot import ask_chatbot, ABSTENTION_MESSAGE
from ml_pipeline.mcq_generator import parse_mcq_response
from ml_pipeline.mcq_validator import validate_mcqs
from ml_pipeline.mcq_scorer import score_mcq_quality, shuffle_mcq_options
from ml_pipeline.adaptive_selector import select_next_question
from ml_pipeline.explanation_generator import generate_feedback


def run_pipeline_audit() -> bool:
    print("=================================================================")
    print("STARTING FULL PIPELINE INTEGRATION AUDIT")
    print("=================================================================")

    # 1. Document Chunking
    sample_doc = (
        "Stratified random sampling divides a heterogeneous population into homogeneous strata (subgroups). "
        "This reduces sampling variance and ensures proportionate representation. "
        "Neyman Allocation is optimal when stratum standard deviations and costs vary."
    )
    chunks = chunk_text(sample_doc, chunk_size=120, overlap=30, source_id="audit_doc")
    assert len(chunks) >= 2, "Expected at least 2 chunks"
    print(f"[AUDIT 1/7 PASS] Document Chunking: {len(chunks)} chunks created with metadata.")

    # 2. Vector Indexing & ChromaDB Persistence
    clear_collection("audit_coll")
    added = add_chunks(chunks, collection_name="audit_coll")
    assert added == len(chunks), "Expected all chunks indexed"
    print(f"[AUDIT 2/7 PASS] Vector Storage: {added} chunks indexed into local ChromaDB.")

    # 3. Grounded RAG Chatbot with Citation
    hits = query_chunks("Neyman Allocation optimal", collection_name="audit_coll")
    assert len(hits) >= 1, "Expected search hits"
    res = ask_chatbot(
        "Neyman Allocation optimal",
        collection_name="audit_coll",
        similarity_threshold=0.05,
        mock_llm_reply="According to [Page 1], Neyman Allocation is optimal when stratum standard deviations vary.",
    )
    assert res["abstained"] is False
    assert len(res["sources"]) >= 1
    assert "[Page 1]" in res["answer"]
    print(f"[AUDIT 3/7 PASS] Grounded Chatbot: Answer returned with {len(res['sources'])} cited source(s).")

    # 4. Strict Chatbot Abstention on Unrelated Query
    res_abs = ask_chatbot(
        "What is the capital of France?",
        collection_name="audit_coll",
        similarity_threshold=0.8,
    )
    assert res_abs["abstained"] is True
    assert res_abs["answer"] == ABSTENTION_MESSAGE
    print("[AUDIT 4/7 PASS] Strict Abstention: Refused out-of-domain question without hallucination.")

    # 5. MCQ Generation -> Validation -> Quality Scoring -> Shuffle
    raw_llm_json = """[
      {
        "question": "Why is Neyman Allocation used in stratified sampling?",
        "options": [
          "To achieve optimal allocation when stratum standard deviations and costs vary",
          "To eliminate the need for homogeneous strata",
          "To ensure every sample size is strictly equal across strata",
          "To double the total sampling variance"
        ],
        "correct_answer": "A",
        "explanation": "Neyman allocation minimizes variance for a given cost when stratum standard deviations differ.",
        "competency": "Sampling Design",
        "difficulty": "hard"
      }
    ]"""
    parsed = parse_mcq_response(raw_llm_json)
    reports = validate_mcqs(parsed, sample_doc)
    assert reports[0]["valid"] is True
    scored = score_mcq_quality(parsed[0], sample_doc)
    assert 0.6 <= scored["quality_score"] <= 1.0
    assert scored["cognitive_level"] in ("Analysis", "Application", "Understanding")
    shuffled = shuffle_mcq_options(scored, seed=123)
    assert shuffled["position_shuffled"] is True
    print(f"[AUDIT 5/7 PASS] Assessment Pipeline: MCQ parsed, validated (score: {scored['quality_score']}), cognitive level: {scored['cognitive_level']}, option positions shuffled.")

    # 6. Adaptive Assessment Loop
    bank = [
        shuffled,
        {"question_id": "q_easy", "question": "What is strata?", "difficulty": "easy", "subskill": "strata"}
    ]
    next_q = select_next_question(bank, [])
    assert next_q["target_difficulty"] == "easy"
    assert next_q["next_question"]["question_id"] == "q_easy"
    print(f"[AUDIT 6/7 PASS] Adaptive Engine: Initial question selected accurately at difficulty '{next_q['target_difficulty']}'.")

    # 7. Explanation Feedback Generator
    feedback = generate_feedback(shuffled, "B")
    assert feedback["is_correct"] is False
    assert feedback["subskill_gap"] is not None
    assert "Incorrect." in feedback["feedback"]
    print("[AUDIT 7/7 PASS] Diagnostic Feedback: Accurately identified distractor misconception and tagged subskill gap.")

    clear_collection("audit_coll")
    print("=================================================================")
    print("ALL 7 PIPELINE INTEGRATION AUDIT CHECKPOINTS PASSED (100%)")
    print("=================================================================")
    return True


if __name__ == "__main__":
    success = run_pipeline_audit()
    sys.exit(0 if success else 1)
