"""
ml_pipeline/canonical_question.py — Canonical Intermediate Assessment Item Contract.

Defines the single source-of-truth intermediate assessment question contract
shared between the ML/LLM generation pipeline, quality validation gate,
and backend ingestion loader.

Contract satisfies Phase 1 Section 4:
- question ID
- question text
- options (exactly 4)
- correct answer / option (A-D)
- competency (canonical 40 competencies)
- subskill (canonical 160 subskills)
- cognitive level (Bloom's taxonomy: Recall, Understanding, Application, Analysis)
- difficulty (easy, medium, hard)
- explanation
- source reference / document info
- provenance
- generation / version metadata
- validation status & quality gate scores
- sandbox / live provenance state
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
VALID_COGNITIVE_LEVELS = frozenset({"Recall", "Understanding", "Application", "Analysis"})
VALID_PROVENANCE_STATES = frozenset({"LIVE INTEGRATION", "SANDBOX DATA", "CURATED", "REPLAY"})
OPTION_LABELS = ("A", "B", "C", "D")


@dataclass
class CanonicalSourceInfo:
    document_id: str
    title: str
    source_org: str
    page_number: int | None = None
    chunk_id: str | None = None
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalValidationInfo:
    valid: bool
    quality_score: float
    structural_ok: bool
    grounding_ok: bool
    distractor_ok: bool
    duplicate_ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalQuestion:
    question_id: str
    question_text: str
    options: list[str]
    correct_option: str
    competency: str
    subskill: str
    cognitive_level: str
    difficulty: str
    explanation: str
    source: dict[str, Any]
    source_reference: str
    provenance: str
    provenance_state: str = "CURATED"
    metadata: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate options length
        if len(self.options) != 4:
            raise ValueError(f"Options must contain exactly 4 items (got {len(self.options)})")

        # Validate correct option
        self.correct_option = self.correct_option.strip().upper()
        if self.correct_option not in OPTION_LABELS:
            raise ValueError(f"correct_option must be one of {OPTION_LABELS} (got {self.correct_option})")

        # Validate difficulty
        self.difficulty = self.difficulty.strip().lower()
        if self.difficulty not in VALID_DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {sorted(VALID_DIFFICULTIES)} (got {self.difficulty})")

        # Validate cognitive level
        if self.cognitive_level not in VALID_COGNITIVE_LEVELS:
            # Fallback to Recall if unknown
            self.cognitive_level = "Recall"

        # Validate provenance state
        if self.provenance_state not in VALID_PROVENANCE_STATES:
            self.provenance_state = "SANDBOX DATA"

        # Generate fingerprint if source_reference is missing
        if not self.source_reference:
            self.source_reference = self.compute_fingerprint()

    def compute_fingerprint(self) -> str:
        canonical = "\0".join((self.competency, self.subskill, self.question_text))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return f"gyansetu-qb:{digest}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_backend_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching backend question_bank_loader requirements."""
        return {
            "competency_name": self.competency,
            "subskill_name": self.subskill,
            "question_text": self.question_text,
            "options": self.options,
            "correct_option": self.correct_option,
            "difficulty": self.difficulty,
            "source_reference": self.source_reference,
            "explanation": self.explanation,
            "cognitive_level": self.cognitive_level,
            "provenance": self.provenance,
            "provenance_state": self.provenance_state,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalQuestion:
        # Normalize alias fields
        q_text = data.get("question_text") or data.get("question") or ""
        corr = data.get("correct_option") or data.get("correct_answer") or "A"
        comp = data.get("competency_name") or data.get("competency") or ""
        sub = data.get("subskill_name") or data.get("subskill") or ""

        # Normalize options
        opts = data.get("options") or []
        cleaned_opts: list[str] = []
        for opt in opts:
            text = str(opt).strip()
            if len(text) > 3 and text[0] in "ABCD" and text[1] in ".):" and text[2] == " ":
                text = text[3:].strip()
            elif len(text) > 4 and text.startswith("(") and text[1] in "ABCD" and text[2] == ")" and text[3] == " ":
                text = text[4:].strip()
            cleaned_opts.append(text)

        # Normalize correct_option label
        corr_label = str(corr).strip().upper()
        if len(corr_label) > 1 and corr_label[0] in OPTION_LABELS:
            corr_label = corr_label[0]

        qid = str(data.get("question_id") or data.get("id") or "")
        if not qid:
            digest = hashlib.sha256(f"{comp}:{sub}:{q_text}".encode("utf-8")).hexdigest()[:12]
            qid = f"Q-{digest}"

        diff = str(data.get("difficulty") or "medium").lower()
        cog = str(data.get("cognitive_level") or "Recall")
        if cog not in VALID_COGNITIVE_LEVELS:
            cog = "Understanding" if diff == "medium" else ("Application" if diff == "hard" else "Recall")

        exp = str(data.get("explanation") or f"Correct answer is {corr_label}.")
        src = data.get("source") or {}
        if isinstance(src, str):
            src = {"document_id": src, "title": src, "source_org": "Official Statistics"}

        src_ref = str(data.get("source_reference") or "")
        prov = str(data.get("provenance") or src.get("source_org") or "Official Statistics")
        prov_state = str(data.get("provenance_state") or data.get("status") or "CURATED")
        meta = data.get("metadata") or {}
        val = data.get("validation") or {}

        return cls(
            question_id=qid,
            question_text=q_text,
            options=cleaned_opts,
            correct_option=corr_label,
            competency=comp,
            subskill=sub,
            cognitive_level=cog,
            difficulty=diff,
            explanation=exp,
            source=src,
            source_reference=src_ref,
            provenance=prov,
            provenance_state=prov_state,
            metadata=meta,
            validation=val,
        )
