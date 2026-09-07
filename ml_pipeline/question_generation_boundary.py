"""
ml_pipeline/question_generation_boundary.py — End-to-End Question Generation & Quality Boundary.

Implements the explicit Phase 1 Section 5 pipeline:
LLM/content generator
        ↓
candidate question
        ↓
schema validation
        ↓
grounding validation
        ↓
answer validation
        ↓
distractor validation
        ↓
ambiguity/duplicate checks
        ↓
competency/subskill validation
        ↓
quality gate
        ↓
canonical question bank
        ↓
backend import
        ↓
AssessmentItem

Fallback hierarchy:
LIVE LLM -> VALIDATED CACHE -> CURATED QUESTION BANK -> DETERMINISTIC FALLBACK
"""
from __future__ import annotations

import logging
from typing import Any, Mapping

from ml_pipeline.canonical_question import CanonicalQuestion
from ml_pipeline.canonical_taxonomy import (
    CANONICAL_COMPETENCIES,
    CANONICAL_SUBSKILLS,
    is_canonical_competency,
    is_canonical_subskill,
)
from ml_pipeline.mcq_generator import generate_mcqs
from ml_pipeline.mcq_scorer import (
    classify_cognitive_level,
    compute_distractor_entropy,
    score_mcq_quality,
    shuffle_mcq_options,
)
from ml_pipeline.mcq_validator import validate_mcqs

logger = logging.getLogger(__name__)

DEFAULT_QUALITY_THRESHOLD = 0.55


# ---------------------------------------------------------------------------
# Fallback Store (Curated Seed Items)
# ---------------------------------------------------------------------------

CURATED_FALLBACK_ITEMS: list[dict[str, Any]] = [
    {
        "question": "Which action best implements a dataset validation rule before official publication?",
        "options": [
            "Release the raw dataset immediately after fieldwork",
            "Check that coded values fall strictly within the allowed classification domain",
            "Delete any records containing outliers without review",
            "Impute all missing cells with zero without flag documentation",
        ],
        "correct_answer": "B",
        "competency": "Data Quality",
        "subskill": "Validation rules",
        "difficulty": "easy",
        "explanation": "Validation rules ensure coded values adhere to the allowed domain and reference classifications.",
        "cognitive_level": "Recall",
        "provenance": "Curated Official Statistics Standard",
        "provenance_state": "CURATED",
        "source": {"document_id": "curated_dq", "title": "Official Statistics Quality Assurance Framework"},
    },
    {
        "question": "When designing a stratified random sample, what is the primary criterion for forming strata?",
        "options": [
            "Maximising heterogeneity within each stratum",
            "Ensuring homogeneity within strata and heterogeneity between strata",
            "Selecting sampling units that are geographically contiguous only",
            "Assigning equal sample sizes to all administrative regions regardless of population",
        ],
        "correct_answer": "B",
        "competency": "Sampling Design",
        "subskill": "Stratified sampling",
        "difficulty": "medium",
        "explanation": "Stratification achieves variance reduction when units within each stratum are relatively homogeneous.",
        "cognitive_level": "Understanding",
        "provenance": "Curated Official Statistics Standard",
        "provenance_state": "CURATED",
        "source": {"document_id": "curated_sampling", "title": "UNSD Household Survey Practical Guide"},
    },
    {
        "question": "In the compilation of National Accounts, what is the principal purpose of Supply and Use Tables (SUT)?",
        "options": [
            "Directly replacing consumer price index surveys",
            "Balancing product supply with use across institutional sectors at basic and purchaser prices",
            "Measuring high-frequency daily economic transactions",
            "Establishing the legal framework for tax collection",
        ],
        "correct_answer": "B",
        "competency": "National Accounts",
        "subskill": "Supply and use tables",
        "difficulty": "hard",
        "explanation": "Supply and Use Tables reconcile supply (output, imports) with use (intermediate, final consumption, gross capital formation, exports).",
        "cognitive_level": "Analysis",
        "provenance": "Curated Official Statistics Standard",
        "provenance_state": "CURATED",
        "source": {"document_id": "curated_sna", "title": "System of National Accounts 2008"},
    },
]


def deterministic_fallback_mcq(
    competency: str,
    subskill: str,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Deterministic fallback item when LLM, cache, and curated bank are exhausted."""
    return {
        "question": f"In official statistical operations, what is the foundational practice for {subskill} in {competency}?",
        "options": [
            f"Adhering to documented national and international guidelines for {subskill}",
            "Proceeding without standardized protocols to speed up delivery",
            "Omitting audit documentation to reduce reporting burden",
            "Relying solely on informal unvalidated assumptions",
        ],
        "correct_answer": "A",
        "competency": competency,
        "subskill": subskill,
        "difficulty": difficulty,
        "explanation": f"Official statistical standards require rigorous protocol adherence and documentation for {subskill}.",
        "cognitive_level": "Recall",
        "provenance": "Deterministic Protocol Fallback",
        "provenance_state": "CURATED",
        "source": {"document_id": "deterministic_fallback", "title": "Official Statistics Standard Operating Procedure"},
    }


# ---------------------------------------------------------------------------
# Pipeline Gatekeeper
# ---------------------------------------------------------------------------

def validate_and_gate_mcq(
    candidate: dict[str, Any],
    source_content: str,
    expected_competency: str | None = None,
    expected_subskill: str | None = None,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
) -> tuple[CanonicalQuestion | None, dict[str, Any]]:
    """
    Executes the multi-stage validation and quality gate:
    1. Structural validation
    2. Grounding validation
    3. Distractor validation
    4. Competency & Subskill taxonomy validation
    5. Continuous quality scoring
    6. Option shuffling (debiasing)
    7. Quality threshold gate
    """
    issues: list[str] = []

    # 1. Competency / Subskill taxonomy checks
    raw_comp = str(candidate.get("competency") or candidate.get("competency_name") or expected_competency or "").strip()
    raw_sub = str(candidate.get("subskill") or candidate.get("subskill_name") or expected_subskill or "").strip()

    if not raw_comp:
        issues.append("Missing competency")
    elif not is_canonical_competency(raw_comp):
        issues.append(f"Competency '{raw_comp}' is not canonical")

    if raw_comp and is_canonical_competency(raw_comp):
        if not raw_sub:
            # Pick first subskill of canonical competency if unspecified
            allowed = CANONICAL_SUBSKILLS[raw_comp]
            raw_sub = allowed[0]
        elif not is_canonical_subskill(raw_comp, raw_sub):
            issues.append(f"Subskill '{raw_sub}' does not belong to canonical competency '{raw_comp}'")

    # 2. Structural & Grounding validation via validate_mcqs
    validation_reports = validate_mcqs([candidate], source_content)
    report = validation_reports[0] if validation_reports else {"valid": False, "issues": ["No validation output"]}

    if not report.get("valid"):
        issues.extend(report.get("issues", []))

    # 3. Continuous Quality Scoring
    score_report = score_mcq_quality(candidate, source_content)
    quality_score = score_report.get("quality_score", 0.0)

    # 4. Gatekeeper threshold check
    passed_gate = (len(issues) == 0) and (quality_score >= quality_threshold)

    gate_result = {
        "passed": passed_gate,
        "quality_score": quality_score,
        "issues": issues,
        "checks": report.get("checks", {}),
    }

    if not passed_gate:
        return None, gate_result

    # 5. Option Shuffling (removes position bias)
    shuffled = shuffle_mcq_options(candidate)

    # 6. Build Canonical Question
    cog_level = candidate.get("cognitive_level") or classify_cognitive_level(shuffled.get("question", ""))
    source_meta = candidate.get("source") or {
        "document_id": "grounded_source",
        "title": "GyanSetu Ingested Official Document",
        "source_org": "Official Statistics",
    }
    prov = candidate.get("provenance") or "GyanSetu Live Pipeline"
    prov_state = candidate.get("provenance_state") or "LIVE INTEGRATION"

    canonical = CanonicalQuestion(
        question_id=str(candidate.get("question_id") or ""),
        question_text=shuffled["question"],
        options=shuffled["options"],
        correct_option=shuffled["correct_answer"],
        competency=raw_comp,
        subskill=raw_sub,
        cognitive_level=cog_level,
        difficulty=shuffled.get("difficulty", "medium"),
        explanation=shuffled.get("explanation", ""),
        source=source_meta,
        source_reference=candidate.get("source_reference", ""),
        provenance=prov,
        provenance_state=prov_state,
        metadata={
            "quality_score": quality_score,
            "metrics": score_report.get("metrics", {}),
        },
        validation=gate_result,
    )

    return canonical, gate_result


# ---------------------------------------------------------------------------
# Resilient Generator with Cascading Fallback
# ---------------------------------------------------------------------------

def generate_question_with_fallback(
    content: str,
    competency: str,
    subskill: str,
    difficulty: str = "medium",
    num_questions: int = 1,
    validated_cache: list[dict[str, Any]] | None = None,
) -> list[CanonicalQuestion]:
    """
    Generates assessment items traversing the fallback cascade:
    1. LIVE LLM
    2. VALIDATED CACHE
    3. CURATED QUESTION BANK
    4. DETERMINISTIC FALLBACK
    """
    accepted_items: list[CanonicalQuestion] = []

    # 1. LIVE LLM attempt
    try:
        raw_candidates = generate_mcqs(
            content=content,
            competency=competency,
            num_questions=num_questions,
            difficulty=difficulty,
        )
        for raw in raw_candidates:
            raw["subskill"] = subskill
            canonical, gate = validate_and_gate_mcq(
                candidate=raw,
                source_content=content,
                expected_competency=competency,
                expected_subskill=subskill,
            )
            if canonical is not None:
                canonical.provenance_state = "LIVE INTEGRATION"
                accepted_items.append(canonical)
    except Exception as exc:
        logger.warning("Live LLM generation failed (%s: %s); proceeding to fallback cascade.", type(exc).__name__, exc)

    if len(accepted_items) >= num_questions:
        return accepted_items[:num_questions]

    # 2. VALIDATED CACHE attempt
    if validated_cache:
        for cached in validated_cache:
            if cached.get("competency") == competency and (
                not cached.get("subskill") or cached.get("subskill") == subskill
            ):
                canonical, gate = validate_and_gate_mcq(
                    candidate=cached,
                    source_content=content or "official statistical content",
                    expected_competency=competency,
                    expected_subskill=subskill,
                )
                if canonical is not None:
                    canonical.provenance_state = "SANDBOX DATA"
                    accepted_items.append(canonical)
                    if len(accepted_items) >= num_questions:
                        return accepted_items[:num_questions]

    # 3. CURATED QUESTION BANK attempt
    for item in CURATED_FALLBACK_ITEMS:
        if item.get("competency") == competency:
            canonical, _ = validate_and_gate_mcq(
                candidate=item,
                source_content=item.get("explanation", "Curated official standard content"),
                expected_competency=competency,
                expected_subskill=subskill or item.get("subskill"),
                quality_threshold=0.40,
            )
            if canonical is not None:
                canonical.provenance_state = "CURATED"
                accepted_items.append(canonical)
                if len(accepted_items) >= num_questions:
                    return accepted_items[:num_questions]

    # 4. DETERMINISTIC FALLBACK
    while len(accepted_items) < num_questions:
        fallback_raw = deterministic_fallback_mcq(competency, subskill, difficulty)
        canonical, _ = validate_and_gate_mcq(
            candidate=fallback_raw,
            source_content=fallback_raw["explanation"],
            expected_competency=competency,
            expected_subskill=subskill,
            quality_threshold=0.30,
        )
        if canonical is not None:
            canonical.provenance_state = "CURATED"
            accepted_items.append(canonical)
        else:
            break

    return accepted_items[:num_questions]
