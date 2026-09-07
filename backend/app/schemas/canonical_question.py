"""
backend/app/schemas/canonical_question.py — Canonical Assessment Item API & Data Schema.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class CanonicalQuestionSchema(BaseModel):
    question_id: str = Field(description="Unique question identifier")
    question_text: str = Field(description="Question stem text")
    options: list[str] = Field(description="List of exactly 4 options", min_length=4, max_length=4)
    correct_option: str = Field(description="Correct option key ('A', 'B', 'C', or 'D')", pattern=r"^[A-D]$")
    competency: str = Field(description="Canonical competency name")
    subskill: str = Field(description="Canonical subskill name")
    cognitive_level: str = Field(default="Recall", description="Bloom's taxonomy cognitive level")
    difficulty: str = Field(default="medium", description="Item difficulty ('easy', 'medium', 'hard')")
    explanation: str = Field(default="", description="Explanation of the correct answer")
    source: dict[str, Any] = Field(default_factory=dict, description="Grounding source document information")
    source_reference: str | None = Field(default=None, description="Source fingerprint or chunk ID")
    provenance: str = Field(default="Official Statistics", description="Authoritative source origin")
    provenance_state: str = Field(default="CURATED", description="Provenance state ('CURATED', 'SANDBOX DATA', 'LIVE INTEGRATION')")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Generation / model version metadata")
    validation: dict[str, Any] = Field(default_factory=dict, description="Quality validation metrics")


class CanonicalQuestionBankFile(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    questions: list[CanonicalQuestionSchema] = Field(default_factory=list)
