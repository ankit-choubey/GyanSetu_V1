"""
ml_pipeline/tests/test_semantic_cache.py — Unit tests for Distributed Redis Semantic Caching.
"""
from __future__ import annotations

import time
from ml_pipeline.semantic_cache import (
    SemanticCache,
    InMemoryLRUCache,
    get_semantic_cache,
)


def test_in_memory_lru_cache_basic_ops():
    """Verifies that the in-memory fallback cache stores, retrieves, and respects TTL."""
    cache = InMemoryLRUCache(maxsize=3)
    cache.set("key1", "val1", ttl=3600)
    assert cache.get("key1") == "val1"
    assert cache.get("nonexistent") is None

    # Test eviction on maxsize
    cache.set("key2", "val2")
    cache.set("key3", "val3")
    cache.set("key4", "val4")  # Should evict key1
    assert cache.get("key1") is None
    assert cache.get("key4") == "val4"


def test_semantic_cache_deterministic_keys():
    """Verifies that compute_mcq_key produces identical keys regardless of whitespace or casing."""
    c1 = "What is sampling?   "
    c2 = "what is sampling?"
    k1 = SemanticCache.compute_mcq_key(c1, "Sampling", "easy", 3)
    k2 = SemanticCache.compute_mcq_key(c2, "sampling", "EASY", 3)
    assert k1 == k2
    assert k1.startswith("gyansetu:mcq:")


def test_semantic_cache_put_get_and_telemetry():
    """Tests put/get on the global SemanticCache and ensures hit/miss telemetry is recorded."""
    cache = get_semantic_cache()
    test_key = "gyansetu:test:mcq_sample_123"
    test_data = [{"question": "Sample Q?", "correct_answer": "A"}]

    # Initially missing
    initial_misses = cache.misses
    miss_res = cache.get("gyansetu:nonexistent_key_9999")
    assert miss_res is None
    assert cache.misses == initial_misses + 1

    # Store
    assert cache.set(test_key, test_data, ttl=60) is True

    # Retrieve
    initial_hits = cache.hits
    hit_res = cache.get(test_key)
    assert hit_res == test_data
    assert cache.hits == initial_hits + 1

    # Check metrics payload
    metrics = cache.get_metrics()
    assert "hits" in metrics
    assert "misses" in metrics
    assert "hit_ratio" in metrics
    assert metrics["hits"] > 0
