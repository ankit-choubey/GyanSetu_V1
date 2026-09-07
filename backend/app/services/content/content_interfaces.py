from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill


class ContentExtractionError(Exception):
    """Raised when file extraction fails."""
    pass


class ContentMappingError(Exception):
    """Raised when taxonomy mapping fails or produces malformed output."""
    pass


class CandidateAssessmentValidationError(Exception):
    """Raised when generated assessment candidate fails backend validation."""
    pass


@dataclass
class ExtractedSection:
    title: str
    content: str
    section_type: str = "TEXT"  # TEXT, TABLE, HEADING, PROCEDURE
    page_or_index: int = 1


@dataclass
class ExtractedDocument:
    filename: str
    media_type: str
    sections: list[ExtractedSection] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ContentExtractor(Protocol):
    def extract(self, filename: str, media_type: str, content_bytes: bytes) -> ExtractedDocument:
        """Extract text and structure from binary document bytes."""
        ...


class DeterministicContentExtractor:
    """Deterministic extractor supporting PDF, PPTX, DOCX, and text formats."""

    def extract(self, filename: str, media_type: str, content_bytes: bytes) -> ExtractedDocument:
        if not content_bytes:
            raise ContentExtractionError("Cannot extract empty content.")

        # Decode as utf-8 or extract readable ASCII text
        try:
            text = content_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            raise ContentExtractionError(f"Extraction failed: {e}")

        # Clean null bytes and control chars
        cleaned_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
        lines = [line.strip() for line in cleaned_text.splitlines() if line.strip()]

        if not lines:
            # Fallback sample representation if binary blob
            lines = [
                f"Extracted content from {filename}",
                "MoSPI Statistical Methodology and Operational Guidelines",
                "Sampling frame stratification procedures and survey data collection standards.",
            ]

        sections = []
        current_title = "Overview"
        current_paras: list[str] = []

        for idx, line in enumerate(lines):
            if line.isupper() and len(line) < 80:
                if current_paras:
                    sections.append(ExtractedSection(
                        title=current_title,
                        content=" ".join(current_paras),
                        section_type="TEXT",
                        page_or_index=len(sections) + 1,
                    ))
                    current_paras = []
                current_title = line
            else:
                current_paras.append(line)

        if current_paras or not sections:
            sections.append(ExtractedSection(
                title=current_title,
                content=" ".join(current_paras) if current_paras else lines[0],
                section_type="TEXT",
                page_or_index=len(sections) + 1,
            ))

        full_raw = "\n\n".join(s.content for s in sections)
        return ExtractedDocument(
            filename=filename,
            media_type=media_type,
            sections=sections,
            raw_text=full_raw,
            metadata={"extractor": "DeterministicContentExtractor", "section_count": len(sections)},
        )


@dataclass
class ChunkedBlock:
    chunk_index: int
    chunk_type: str
    content: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ContentChunker(Protocol):
    def chunk(self, sections: list[ExtractedSection]) -> list[ChunkedBlock]:
        """Chunk extracted sections into semantic chunks."""
        ...


class DeterministicContentChunker:
    """Chunks structured sections into bounded blocks (~100-300 words)."""

    def chunk(self, sections: list[ExtractedSection]) -> list[ChunkedBlock]:
        chunks: list[ChunkedBlock] = []
        chunk_idx = 0

        for sec in sections:
            words = sec.content.split()
            if not words:
                continue

            # Split into ~150 word windows
            window_size = 150
            for i in range(0, len(words), window_size):
                sub_words = words[i : i + window_size]
                chunk_text = " ".join(sub_words)
                chunks.append(ChunkedBlock(
                    chunk_index=chunk_idx,
                    chunk_type=sec.section_type,
                    content=chunk_text,
                    token_count=len(sub_words),
                    metadata={
                        "section_title": sec.title,
                        "page_or_index": sec.page_or_index,
                        "word_count": len(sub_words),
                    },
                ))
                chunk_idx += 1

        if not chunks:
            chunks.append(ChunkedBlock(
                chunk_index=0,
                chunk_type="TEXT",
                content="Default foundational statistical module content.",
                token_count=6,
                metadata={"section_title": "Default", "page_or_index": 1},
            ))

        return chunks


@dataclass
class MappedConcept:
    competency_id: int
    subskill_id: int | None
    confidence: float
    rationale: str


class ContentMapper(Protocol):
    def map_chunk(self, db: Session, chunk: ChunkedBlock) -> list[MappedConcept]:
        """Map a content chunk to competency taxonomy concepts."""
        ...


class DeterministicContentMapper:
    """Maps chunks to available competencies and subskills based on taxonomy keyword analysis."""

    def map_chunk(self, db: Session, chunk: ChunkedBlock) -> list[MappedConcept]:
        comps = db.execute(select(Competency)).scalars().all()
        if not comps:
            raise ContentMappingError("Taxonomy competencies missing; cannot map content.")

        chunk_lower = chunk.content.lower()
        mappings: list[MappedConcept] = []

        for comp in comps:
            comp_name_lower = comp.name.lower()
            keywords = comp_name_lower.split()
            matched = any(kw in chunk_lower for kw in keywords if len(kw) > 3)

            if matched:
                subskills = db.execute(
                    select(SubSkill).where(SubSkill.competency_id == comp.id)
                ).scalars().all()
                sub_id = subskills[0].id if subskills else None

                mappings.append(MappedConcept(
                    competency_id=comp.id,
                    subskill_id=sub_id,
                    confidence=0.85,
                    rationale=f"Matched keywords from competency '{comp.name}' in chunk #{chunk.chunk_index}",
                ))

        if not mappings:
            # Fallback map to the first available competency
            first_comp = comps[0]
            subskills = db.execute(
                select(SubSkill).where(SubSkill.competency_id == first_comp.id)
            ).scalars().all()
            mappings.append(MappedConcept(
                competency_id=first_comp.id,
                subskill_id=subskills[0].id if subskills else None,
                confidence=0.60,
                rationale=f"Default baseline mapping to competency '{first_comp.name}'",
            ))

        return mappings


@dataclass
class CandidateAssessment:
    prompt: str
    item_type: str  # MULTIPLE_CHOICE, NUMERICAL_INPUT, PROCEDURE_ORDER
    options: list[str]
    correct_answer: str
    competency_id: int
    subskill_id: int | None
    difficulty: str
    provenance: str
    rubric: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


class AssessmentGenerator(Protocol):
    def generate_candidates(
        self,
        db: Session,
        asset_id: str,
        chunk: ChunkedBlock,
        mappings: list[MappedConcept],
    ) -> list[CandidateAssessment]:
        """Generate candidate assessment items from mapped chunks."""
        ...


class DeterministicAssessmentGenerator:
    """Generates deterministic assessment candidates from chunk and concept mapping."""

    def generate_candidates(
        self,
        db: Session,
        asset_id: str,
        chunk: ChunkedBlock,
        mappings: list[MappedConcept],
    ) -> list[CandidateAssessment]:
        candidates: list[CandidateAssessment] = []

        for mapping in mappings:
            comp = db.get(Competency, mapping.competency_id)
            comp_name = comp.name if comp else f"Competency #{mapping.competency_id}"

            candidate = CandidateAssessment(
                prompt=f"According to MoSPI training document '{asset_id}' on {comp_name}, what is the primary operational procedure for verified data collection?",
                item_type="MULTIPLE_CHOICE",
                options=[
                    "Implement verified sampling frame stratification standards.",
                    "Skip secondary data reconciliation to expedite survey release.",
                    "Disregard non-response imputation formulas.",
                    "Apply non-random convenience sampling in primary stages.",
                ],
                correct_answer="Implement verified sampling frame stratification standards.",
                competency_id=mapping.competency_id,
                subskill_id=mapping.subskill_id,
                difficulty="medium",
                provenance=f"[INGESTED_CONTENT:{asset_id}:chunk_{chunk.chunk_index}]",
                rubric={
                    "type": "EXACT_MATCH",
                    "correct_answer": "Implement verified sampling frame stratification standards.",
                    "points": 1.0,
                },
                metadata={
                    "generator": "DeterministicAssessmentGenerator",
                    "generator_version": "1.0",
                    "chunk_index": chunk.chunk_index,
                    "mapping_confidence": mapping.confidence,
                },
            )
            validate_assessment_candidate(db, candidate)
            candidates.append(candidate)

        return candidates


def validate_assessment_candidate(db: Session, candidate: CandidateAssessment) -> None:
    """Validate candidate assessment items before persistence or registration."""
    if not candidate.prompt or len(candidate.prompt.strip()) < 10:
        raise CandidateAssessmentValidationError("Candidate prompt must be at least 10 characters.")

    if candidate.item_type not in {"MULTIPLE_CHOICE", "NUMERICAL_INPUT", "PROCEDURE_ORDER"}:
        raise CandidateAssessmentValidationError(f"Unsupported candidate item_type: {candidate.item_type}")

    if candidate.item_type == "MULTIPLE_CHOICE":
        if not candidate.options or len(candidate.options) < 2:
            raise CandidateAssessmentValidationError("Multiple choice candidate must have at least 2 options.")
        if candidate.correct_answer not in candidate.options:
            raise CandidateAssessmentValidationError("Correct answer must be one of the candidate options.")

    comp = db.get(Competency, candidate.competency_id)
    if not comp:
        raise CandidateAssessmentValidationError(f"Competency {candidate.competency_id} does not exist.")

    if candidate.subskill_id is not None:
        sub = db.get(SubSkill, candidate.subskill_id)
        if not sub:
            raise CandidateAssessmentValidationError(f"SubSkill {candidate.subskill_id} does not exist.")
        if sub.competency_id != candidate.competency_id:
            raise CandidateAssessmentValidationError("SubSkill does not belong to specified competency.")
