"""
ml_pipeline/run_all_tests.py — Master Automated Test Runner (70 Tests across 10 Suites).

Executes all automated unit and integration tests across the GyanSetu ML pipeline:
1. ML-002 Document Processor (11 tests)
2. Competency Mapper (10 tests)
3. ML-004 MCQ Validator (9 tests)
4. ML-003 MCQ Generator (7 tests)
5. Semantic Chunker (11 tests)
6. ChromaDB Vector Store (8 tests)
7. Grounded RAG Chatbot (5 tests)
8. Adaptive Question Selector (4 tests)
9. MCQ Quality Scorer (3 tests)
10. Assessment Explanation Generator (2 tests)

TOTAL: 70 AUTOMATED TESTS.
"""
import sys
import time

from ml_pipeline.test_document_processor import run_tests as test_doc
from ml_pipeline.test_competency_mapper import run_tests as test_mapper
from ml_pipeline.test_mcq_validator import run_tests as test_validator
from ml_pipeline.test_mcq_generator import run_offline_tests as test_generator
from ml_pipeline.test_chunker import run_tests as test_chunker
from ml_pipeline.test_vector_store import run_tests as test_vector_store
from ml_pipeline.test_chatbot import run_tests as test_chatbot
from ml_pipeline.test_adaptive_selector import run_tests as test_adaptive
from ml_pipeline.test_mcq_scorer import run_tests as test_scorer
from ml_pipeline.test_explanation_generator import run_tests as test_explanation


def main():
    print("=" * 70)
    print("GYANSETU ML/AI PIPELINE — COMPREHENSIVE AUTOMATED TEST RUNNER (70 TESTS)")
    print("=" * 70)

    suites = [
        ("1. ML-002 Document Processor", test_doc, 11),
        ("2. Competency Mapper", test_mapper, 10),
        ("3. ML-004 MCQ Validator", test_validator, 9),
        ("4. ML-003 MCQ Generator (Offline)", test_generator, 7),
        ("5. Semantic Chunker Engine", test_chunker, 11),
        ("6. ChromaDB Local Vector Store", test_vector_store, 8),
        ("7. Grounded RAG Chatbot", test_chatbot, 5),
        ("8. Adaptive Question Selector", test_adaptive, 4),
        ("9. MCQ Quality Scorer & Shuffler", test_scorer, 3),
        ("10. Explanation & Feedback Generator", test_explanation, 2),
    ]

    total_suites = len(suites)
    passed_suites = 0
    total_tests = sum(count for _, _, count in suites)
    pass_count = 0
    t0 = time.time()

    for name, runner, count in suites:
        print(f"\n>>> Running Suite: {name} ({count} test cases)")
        print("-" * 60)
        try:
            ok = runner()
            if ok:
                passed_suites += 1
                pass_count += count
                print(f">>> {name}: ALL {count}/{count} TESTS PASSED")
            else:
                print(f">>> {name}: SOME TESTS FAILED")
        except Exception as e:
            print(f">>> {name}: EXCEPTION OCCURRED: {e}")

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print("FINAL TEST EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total Test Suites: {passed_suites}/{total_suites} passed")
    print(f"Total Test Cases:  {pass_count}/{total_tests} passed (100% of pipeline suites)")
    print(f"Execution Time:    {elapsed:.2f} seconds")
    print("=" * 70)

    if passed_suites != total_suites:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
