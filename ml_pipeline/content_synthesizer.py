"""
ml_pipeline/content_synthesizer.py — Cross-Modal Content Deduplication & Synthesis Engine.

Consolidates multi-modal learning materials (PDF documents, PPTX slides, YouTube transcripts,
MP4 audio transcriptions) into a unified, non-redundant chunk corpus:
1. Detects exact and high-similarity semantic duplicates within and across source streams.
2. Employs SemanticEmbeddingFunction for dense cosine similarity comparison.
3. Merges overlapping knowledge representations while preserving provenance metadata:
   - source_ids: list of all originating chunk IDs
   - source_types: list of all contributing modal formats (e.g. ['pdf', 'youtube'])
   - page_numbers: list of all referenced page/slide numbers
4. Produces clean SynthesisResult with audit statistics and dedup metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ml_pipeline.vector_store import (
    SemanticEmbeddingFunction,
    create_embedding_function,
)


@dataclass
class SynthesisResult:
    """Consolidated results of cross-modal content deduplication."""
    deduplicated_chunks: List[Dict[str, Any]]
    total_input_chunks: int
    total_output_chunks: int
    reduction_percentage: float
    overlap_pairs_count: int
    source_breakdown: Dict[str, int]
    overlap_log: List[Dict[str, Any]] = field(default_factory=list)


class ContentSynthesizer:
    """
    Cross-modal semantic deduplication and chunk consolidation engine.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.82,
        embedding_fn: Optional[Any] = None,
    ):
        """
        Args:
            similarity_threshold: Cosine similarity >= threshold triggers chunk consolidation.
            embedding_fn: Embedding function generating dense vectors (defaults to SemanticEmbeddingFunction).
        """
        self.similarity_threshold = similarity_threshold
        self.embedding_fn = embedding_fn or create_embedding_function(prefer_semantic=True)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Strips excessive whitespace, punctuation, and casing for lexical comparison."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(cleaned.split())

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Computes cosine similarity between two normalized or raw vectors."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _merge_two_chunks(self, primary: Dict[str, Any], secondary: Dict[str, Any], similarity: float) -> Dict[str, Any]:
        """
        Merges two overlapping chunks into a single consolidated representation.
        Chooses the richer text as primary base, concatenates complementary sentences if needed,
        and aggregates provenance metadata.
        """
        p_text = primary.get("text", "").strip()
        s_text = secondary.get("text", "").strip()

        # Decide which chunk text is base
        if len(s_text) > len(p_text):
            base_text = s_text
            supp_text = p_text
        else:
            base_text = p_text
            supp_text = s_text

        # Check for complementary distinct sentences
        supp_sentences = [s.strip() for s in re.split(r"[.!?]\s+", supp_text) if len(s.strip()) > 20]
        added_info = []
        for s in supp_sentences:
            norm_s = self._normalize_text(s)
            if norm_s not in self._normalize_text(base_text):
                added_info.append(s)

        if added_info and len(added_info) <= 3:
            combined_text = base_text.rstrip(".") + ". Additional source detail: " + "; ".join(added_info) + "."
        else:
            combined_text = base_text

        # Merge source_ids
        source_ids: list[str] = []
        for c in [primary, secondary]:
            if "source_ids" in c and isinstance(c["source_ids"], list):
                source_ids.extend(c["source_ids"])
            elif "chunk_id" in c:
                source_ids.append(str(c["chunk_id"]))
            elif "source_id" in c:
                source_ids.append(str(c["source_id"]))
        source_ids = sorted(list(set(source_ids)))

        # Merge source_types
        source_types: list[str] = []
        for c in [primary, secondary]:
            st = c.get("source_type") or c.get("chunk_type") or "text"
            if isinstance(st, list):
                source_types.extend(st)
            else:
                source_types.append(str(st))
            if "source_types" in c and isinstance(c["source_types"], list):
                source_types.extend(c["source_types"])
        source_types = sorted(list(set(source_types)))

        # Merge page numbers
        pages: list[int] = []
        for c in [primary, secondary]:
            p = c.get("page_number")
            if p is not None:
                pages.append(int(p))
            if "page_numbers" in c and isinstance(c["page_numbers"], list):
                pages.extend([int(x) for x in c["page_numbers"]])
        pages = sorted(list(set(pages)))

        # Competency resolution
        competency = primary.get("competency") or secondary.get("competency")

        return {
            "chunk_id": primary.get("chunk_id", "merged_chunk"),
            "text": combined_text,
            "page_number": pages[0] if pages else 1,
            "page_numbers": pages,
            "chunk_type": primary.get("chunk_type", "text"),
            "source_id": primary.get("source_id", "multi_source"),
            "source_ids": source_ids,
            "source_types": source_types,
            "char_length": len(combined_text),
            "competency": competency,
            "merged": True,
            "consolidation_similarity": round(similarity, 4),
        }

    def deduplicate_single_stream(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes exact and near-duplicate chunks within a single document stream."""
        if not chunks:
            return []

        unique_chunks: List[Dict[str, Any]] = []
        seen_texts: set[str] = set()

        for c in chunks:
            raw_text = c.get("text", "").strip()
            norm = self._normalize_text(raw_text)
            if not norm or norm in seen_texts:
                continue
            seen_texts.add(norm)
            unique_chunks.append(dict(c))

        return unique_chunks

    def synthesize(
        self,
        chunk_inputs: Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]],
    ) -> SynthesisResult:
        """
        Performs full cross-modal semantic deduplication.

        Args:
            chunk_inputs: Either a dictionary keyed by source type (e.g.
                          {"pdf": [...], "youtube": [...], "pptx": [...]})
                          or a unified list of chunk dictionaries.

        Returns:
            SynthesisResult with consolidated chunks and dedup metrics.
        """
        all_candidate_chunks: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}
        intra_suppressed = 0

        if isinstance(chunk_inputs, dict):
            total_input = sum(len(v) for v in chunk_inputs.values())
            for src_type, chunks in chunk_inputs.items():
                deduped_stream = self.deduplicate_single_stream(chunks)
                intra_suppressed += (len(chunks) - len(deduped_stream))
                for item in deduped_stream:
                    if "source_type" not in item:
                        item["source_type"] = src_type
                all_candidate_chunks.extend(deduped_stream)
                source_counts[src_type] = len(chunks)
        else:
            total_input = len(chunk_inputs)
            for c in chunk_inputs:
                st = c.get("source_type", "unknown")
                source_counts[st] = source_counts.get(st, 0) + 1
            all_candidate_chunks = self.deduplicate_single_stream(chunk_inputs)
            intra_suppressed = total_input - len(all_candidate_chunks)

        if not all_candidate_chunks:
            return SynthesisResult(
                deduplicated_chunks=[],
                total_input_chunks=total_input,
                total_output_chunks=0,
                reduction_percentage=100.0 if total_input > 0 else 0.0,
                overlap_pairs_count=intra_suppressed,
                source_breakdown=source_counts,
                overlap_log=[],
            )

        # Generate embeddings for all candidate chunks in one batch
        texts = [c.get("text", "") for c in all_candidate_chunks]
        embeddings = self.embedding_fn(texts)

        consolidated: List[Dict[str, Any]] = []
        consolidated_embeddings: List[list[float]] = []
        overlap_log: List[Dict[str, Any]] = []

        for i, (chunk, emb) in enumerate(zip(all_candidate_chunks, embeddings)):
            if not consolidated:
                consolidated.append(dict(chunk))
                consolidated_embeddings.append(emb)
                continue

            # Compare against existing consolidated chunks
            best_sim = -1.0
            best_idx = -1

            for j, c_emb in enumerate(consolidated_embeddings):
                sim = self._cosine_similarity(emb, c_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_idx = j

            if best_sim >= self.similarity_threshold:
                # Merge into consolidated[best_idx]
                merged_chunk = self._merge_two_chunks(consolidated[best_idx], chunk, best_sim)
                consolidated[best_idx] = merged_chunk
                # Update embedding to re-embed merged text or average embeddings
                overlap_log.append({
                    "primary_chunk_id": consolidated[best_idx].get("chunk_id"),
                    "secondary_chunk_id": chunk.get("chunk_id"),
                    "similarity": round(best_sim, 4),
                    "primary_source": consolidated[best_idx].get("source_type", "unknown"),
                    "secondary_source": chunk.get("source_type", "unknown"),
                })
            else:
                consolidated.append(dict(chunk))
                consolidated_embeddings.append(emb)

        total_output = len(consolidated)
        reduction = round((1.0 - (total_output / max(1, total_input))) * 100.0, 2)

        return SynthesisResult(
            deduplicated_chunks=consolidated,
            total_input_chunks=total_input,
            total_output_chunks=total_output,
            reduction_percentage=max(0.0, reduction),
            overlap_pairs_count=len(overlap_log) + intra_suppressed,
            source_breakdown=source_counts,
            overlap_log=overlap_log,
        )
