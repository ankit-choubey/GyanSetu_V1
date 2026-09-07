"""
ml_pipeline/tests/test_semantic_embeddings.py — Tests for Dense Semantic Embeddings.

Validates that:
- SentenceTransformer produces 384-dimensional normalized vectors.
- Semantic similarity accurately separates synonymous vs. unrelated concepts.
- ChromaDB indexing and semantic cosine retrieval function end-to-end.
- Fallback and migration mechanisms behave predictably.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from ml_pipeline.vector_store import (
    EMBEDDING_DIM,
    FastLocalEmbeddingFunction,
    FallbackEmbeddingFunction,
    SemanticEmbeddingFunction,
    create_embedding_function,
    migrate_to_semantic,
    add_chunks,
    query_chunks,
    clear_collection,
    count_chunks,
)


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def test_semantic_embedding_dimension():
    fn = SemanticEmbeddingFunction()
    res = fn(["Probability theory and statistical inference"])
    assert len(res) == 1
    assert len(res[0]) == EMBEDDING_DIM
    # Normalized embeddings should have L2 norm close to 1.0
    norm = math.sqrt(sum(x * x for x in res[0]))
    assert abs(norm - 1.0) < 1e-3


def test_semantic_similarity_discrimination():
    fn = SemanticEmbeddingFunction()
    texts = [
        "Probability is the numerical measurement of the likelihood of a random outcome.",
        "Likelihood of an uncertain event occurring can be represented quantitatively as a probability.",
        "Photosynthesis in green plants converts solar sunlight and water into glucose and oxygen.",
    ]
    vecs = fn(texts)
    sim_related = _cosine_similarity(vecs[0], vecs[1])
    sim_unrelated = _cosine_similarity(vecs[0], vecs[2])

    assert sim_related > 0.65, f"Expected high similarity for synonyms, got {sim_related}"
    assert sim_unrelated < 0.40, f"Expected low similarity for unrelated topics, got {sim_unrelated}"
    assert sim_related > sim_unrelated + 0.30


def test_fallback_embedding_function():
    fn = FallbackEmbeddingFunction()
    res = fn(["Testing local token projection fallback"])
    assert len(res) == 1
    assert len(res[0]) == EMBEDDING_DIM
    norm = math.sqrt(sum(x * x for x in res[0]))
    assert abs(norm - 1.0) < 1e-4


def test_create_embedding_function_factory():
    semantic_fn = create_embedding_function(prefer_semantic=True)
    assert isinstance(semantic_fn, SemanticEmbeddingFunction)

    fallback_fn = create_embedding_function(prefer_semantic=False)
    assert isinstance(fallback_fn, FastLocalEmbeddingFunction)


def test_chromadb_semantic_indexing_and_query():
    test_coll = "test_semantic_indexing_suite"
    clear_collection(test_coll)

    chunks = [
        {
            "chunk_id": "math_01",
            "text": "Bayesian probability updates prior beliefs using conditional likelihood and evidence.",
            "page_number": 1,
            "chunk_type": "text",
            "competency": "Bayesian Inference",
        },
        {
            "chunk_id": "econ_01",
            "text": "Consumer price index calculation using Laspeyres fixed-basket weighted averages.",
            "page_number": 5,
            "chunk_type": "text",
            "competency": "Price Statistics",
        },
    ]

    added = add_chunks(chunks, collection_name=test_coll)
    assert added == 2
    assert count_chunks(test_coll) == 2

    # Query with semantic synonym "prior updating given observed data"
    hits = query_chunks("prior updating given observed data", n_results=1, collection_name=test_coll)
    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "math_01"
    assert hits[0]["similarity_score"] > 0.50

    clear_collection(test_coll)


def test_migrate_to_semantic():
    test_coll = "test_migration_suite"
    clear_collection(test_coll)

    chunks = [
        {
            "chunk_id": "chunk_mig_1",
            "text": "The sample space S encompasses all exhaustive elementary outcomes of a random trial.",
            "page_number": 2,
            "chunk_type": "text",
        }
    ]

    # Add initial chunk
    add_chunks(chunks, collection_name=test_coll)
    assert count_chunks(test_coll) == 1

    # Run migration
    migrated_count = migrate_to_semantic(test_coll)
    assert migrated_count == 1
    assert count_chunks(test_coll) == 1

    hits = query_chunks("all exhaustive elementary outcomes of an experiment", n_results=1, collection_name=test_coll)
    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "chunk_mig_1"

    clear_collection(test_coll)
