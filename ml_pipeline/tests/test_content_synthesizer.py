"""
ml_pipeline/tests/test_content_synthesizer.py — Automated Unit Tests for Cross-Modal Content Synthesizer.

Tests:
1. Exact intra-source duplicate suppression.
2. Cross-modal semantic deduplication (PDF + YouTube transcript on same topic).
3. Preservation of distinct concepts across diverse topics.
4. Provenance aggregation (merged source_ids, source_types, and page_numbers).
5. Comprehensive metrics and reduction calculations.
"""
from __future__ import annotations

import pytest

from ml_pipeline.content_synthesizer import (
    ContentSynthesizer,
    SynthesisResult,
)


def test_intra_source_exact_duplicate_dedup():
    synthesizer = ContentSynthesizer(similarity_threshold=0.85)
    chunks = [
        {"chunk_id": "c1", "text": "The law of large numbers guarantees convergence of sample mean."},
        {"chunk_id": "c2", "text": "The law of large numbers guarantees convergence of sample mean."},  # Exact duplicate
        {"chunk_id": "c3", "text": "Central limit theorem describes the normal limiting distribution."},
    ]
    res = synthesizer.synthesize(chunks)
    assert res.total_input_chunks == 3
    assert res.total_output_chunks == 2
    assert res.reduction_percentage > 30.0


def test_cross_modal_semantic_dedup():
    synthesizer = ContentSynthesizer(similarity_threshold=0.75)

    multi_source_data = {
        "pdf": [
            {
                "chunk_id": "pdf_01",
                "text": "Stratified random sampling divides the total target population into homogeneous strata to decrease the variance of sample estimates.",
                "page_number": 3,
                "competency": "Sampling Design",
            },
            {
                "chunk_id": "pdf_02",
                "text": "Consumer price index measures the weighted average of prices of a fixed basket of consumer goods and services.",
                "page_number": 10,
                "competency": "Price Statistics",
            }
        ],
        "youtube": [
            {
                "chunk_id": "yt_01",
                "text": "In stratified sampling, we separate our population into distinct homogeneous groups or strata, which allows us to significantly reduce estimator variance.",
                "page_number": 1,
                "competency": "Sampling Design",
            }
        ]
    }

    res = synthesizer.synthesize(multi_source_data)

    # 3 inputs: 2 about stratified sampling (overlapping), 1 about CPI
    assert res.total_input_chunks == 3
    assert res.total_output_chunks == 2
    assert res.overlap_pairs_count >= 1

    # Check the merged chunk has both source types
    merged_strat = [c for c in res.deduplicated_chunks if "stratified" in c["text"].lower()][0]
    assert "pdf_01" in merged_strat["source_ids"]
    assert "yt_01" in merged_strat["source_ids"]
    assert "pdf" in merged_strat["source_types"]
    assert "youtube" in merged_strat["source_types"]


def test_preservation_of_unique_content():
    synthesizer = ContentSynthesizer(similarity_threshold=0.85)
    chunks = [
        {"chunk_id": "1", "text": "Linear regression models conditional expectations.", "source_type": "pdf"},
        {"chunk_id": "2", "text": "K-means clustering partitions observations into k distinct clusters.", "source_type": "pptx"},
        {"chunk_id": "3", "text": "Bayesian Markov Chain Monte Carlo generates posterior samples.", "source_type": "video"},
    ]
    res = synthesizer.synthesize(chunks)
    assert res.total_input_chunks == 3
    assert res.total_output_chunks == 3
    assert res.reduction_percentage == 0.0
    assert res.overlap_pairs_count == 0


def test_empty_input_handling():
    synthesizer = ContentSynthesizer()
    res = synthesizer.synthesize({})
    assert res.total_input_chunks == 0
    assert res.total_output_chunks == 0
    assert res.deduplicated_chunks == []
