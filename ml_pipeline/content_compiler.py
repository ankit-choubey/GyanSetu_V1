"""
Content-to-Competency Compiler — Full E2E ML Pipeline (Phase 5.3).

Wires document processing, concept extraction, competency mapping,
MCQ generation, validation, and scoring into a unified compiler.

Flow:
    Document (PDF / PPTX / Text)
        ↓
    Structured Document Processing & Chunker
        ↓
    Concept Extractor (LLM)
        ↓
    Competency Mapper (LLM)
        ↓
    MCQ Generator (LLM)
        ↓
    MCQ Validator & Quality Scorer
        ↓
    Compiled Assessment Bank Artifact
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ml_pipeline.competency_mapper import map_competencies
from ml_pipeline.concept_extractor import extract_concepts
from ml_pipeline.document_processor import process_document_structured
from ml_pipeline.generate_question_bank import QUALITY_THRESHOLD
from ml_pipeline.mcq_generator import generate_mcqs
from ml_pipeline.mcq_scorer import score_mcq_quality
from ml_pipeline.mcq_validator import validate_mcqs


class ContentCompilerResult:
    """Structured result of the content-to-competency compiler."""

    def __init__(
        self,
        *,
        source_id: str,
        text_length: int,
        concepts: List[str],
        competency_mappings: List[Dict[str, Any]],
        generated_mcqs: List[Dict[str, Any]],
        valid_mcqs: List[Dict[str, Any]],
        quality_scored_mcqs: List[Dict[str, Any]],
        rejection_count: int,
    ):
        self.source_id = source_id
        self.text_length = text_length
        self.concepts = concepts
        self.competency_mappings = competency_mappings
        self.generated_mcqs = generated_mcqs
        self.valid_mcqs = valid_mcqs
        self.quality_scored_mcqs = quality_scored_mcqs
        self.rejection_count = rejection_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "text_length": self.text_length,
            "concept_count": len(self.concepts),
            "concepts": self.concepts,
            "competency_count": len(self.competency_mappings),
            "competency_mappings": self.competency_mappings,
            "total_generated_mcqs": len(self.generated_mcqs),
            "valid_mcq_count": len(self.valid_mcqs),
            "quality_mcq_count": len(self.quality_scored_mcqs),
            "rejections": self.rejection_count,
            "items": self.quality_scored_mcqs,
            "sandbox_data": True,
        }


def compile_content_to_assessments(
    source: Union[str, Path],
    *,
    num_questions_per_competency: int = 3,
    difficulty: str = "medium",
    quality_threshold: float = QUALITY_THRESHOLD,
) -> ContentCompilerResult:
    """
    Compiles raw content or document file into validated, scored assessment items.

    Args:
        source: File path (.pdf, .pptx) or raw text string.
        num_questions_per_competency: Number of MCQs to generate per mapped competency.
        difficulty: Desired difficulty tier ('easy', 'medium', 'hard').
        quality_threshold: Minimum quality score threshold to retain items.

    Returns:
        ContentCompilerResult containing extracted concepts, mappings, and scored MCQs.
    """
    source_str = str(source)
    source_id = Path(source_str).name if os.path.exists(source_str) else "raw_text_input"

    # 1. Document Extraction
    if os.path.exists(source_str) and Path(source_str).suffix.lower() in {".pdf", ".pptx"}:
        pages = process_document_structured(source_str)
        extracted_text = " ".join(
            p.get("text", "")
            for p in pages
            if p.get("status") == "success" and p.get("text")
        )
    else:
        extracted_text = source_str.strip()

    if not extracted_text:
        raise ValueError("No extractable textual content found in source.")

    # 2. Concept Extraction
    concepts = extract_concepts(extracted_text)
    if not concepts:
        return ContentCompilerResult(
            source_id=source_id,
            text_length=len(extracted_text),
            concepts=[],
            competency_mappings=[],
            generated_mcqs=[],
            valid_mcqs=[],
            quality_scored_mcqs=[],
            rejection_count=0,
        )

    # 3. Competency Mapping
    mappings = map_competencies(concepts)
    if not mappings:
        return ContentCompilerResult(
            source_id=source_id,
            text_length=len(extracted_text),
            concepts=concepts,
            competency_mappings=[],
            generated_mcqs=[],
            valid_mcqs=[],
            quality_scored_mcqs=[],
            rejection_count=0,
        )

    all_generated: List[Dict[str, Any]] = []
    all_valid: List[Dict[str, Any]] = []
    all_scored: List[Dict[str, Any]] = []
    rejections = 0

    # 4. MCQ Generation & Validation per Competency Target
    seen_competencies = set()
    for mapping in mappings:
        comp_name = mapping.get("competency", "").strip()
        if not comp_name or comp_name in seen_competencies:
            continue
        seen_competencies.add(comp_name)

        try:
            mcqs = generate_mcqs(
                extracted_text,
                comp_name,
                num_questions_per_competency,
                difficulty,
            )
        except Exception:
            continue

        all_generated.extend(mcqs)
        reports = validate_mcqs(mcqs, extracted_text)

        for mcq, rep in zip(mcqs, reports):
            if not rep.get("valid"):
                rejections += 1
                continue
            all_valid.append(mcq)

            scored = score_mcq_quality(mcq, extracted_text)
            if float(scored.get("quality_score", 0.0)) >= quality_threshold:
                scored["competency"] = comp_name
                scored["source_id"] = source_id
                all_scored.append(scored)
            else:
                rejections += 1

    return ContentCompilerResult(
        source_id=source_id,
        text_length=len(extracted_text),
        concepts=concepts,
        competency_mappings=mappings,
        generated_mcqs=all_generated,
        valid_mcqs=all_valid,
        quality_scored_mcqs=all_scored,
        rejection_count=rejections,
    )
