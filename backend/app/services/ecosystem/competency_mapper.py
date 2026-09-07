from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill


@dataclass
class MappingResolution:
    competency_id: int | None
    subskill_id: int | None
    competency_name: str | None
    subskill_name: str | None
    status: str  # VERIFIED, CURATED, PROVISIONAL, UNDER_REVIEW
    confidence: float
    reason: str


# Canonical MoSPI taxonomy aliases and curated mappings
CURATED_TAXONOMY_ALIASES: dict[str, tuple[str, str | None]] = {
    # iGOT / NSSTA course terminology -> (Canonical Competency, Canonical Subskill)
    "sampling techniques": ("Sampling Design", "Stratified sampling"),
    "sample survey design": ("Sampling Design", "Probability sampling"),
    "stratified sampling": ("Sampling Design", "Stratified sampling"),
    "cluster sampling": ("Sampling Design", "Cluster sampling"),
    "consumer price index": ("Index Numbers", "Price relatives"),
    "index numbers compilation": ("Index Numbers", "Index rebasing"),
    "national accounts compilation": ("National Accounts", "SNA 2008 framework"),
    "data quality validation": ("Data Quality & Validation", "Logical consistency checks"),
    "household survey enumeration": ("Survey Operations & Field Management", "Household listing"),
    "cpi data collection": ("Price Statistics Operations", "Market quotation collection"),
}


class CompetencyMappingService:
    """Service to normalize and validate external provider competency terminology into GyanSetu system-of-record."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._competencies: dict[str, Competency] = {
            c.name.lower().strip(): c for c in db.execute(select(Competency)).scalars().all()
        }
        self._subskills: dict[str, SubSkill] = {
            s.name.lower().strip(): s for s in db.execute(select(SubSkill)).scalars().all()
        }

    def resolve_mapping(
        self,
        competency_hint: str | None,
        subskill_hint: str | None = None,
        provider: str = "EXTERNAL",
    ) -> MappingResolution:
        if not competency_hint or not competency_hint.strip():
            return MappingResolution(
                competency_id=None,
                subskill_id=None,
                competency_name=None,
                subskill_name=None,
                status="UNDER_REVIEW",
                confidence=0.0,
                reason="No competency hint provided by external provider",
            )

        clean_comp = competency_hint.strip().lower()
        clean_sub = subskill_hint.strip().lower() if subskill_hint else None

        # 1. Exact Match against Canonical Competencies
        if clean_comp in self._competencies:
            comp_obj = self._competencies[clean_comp]
            sub_obj = self._subskills.get(clean_sub) if clean_sub else None
            return MappingResolution(
                competency_id=comp_obj.id,
                subskill_id=sub_obj.id if sub_obj else None,
                competency_name=comp_obj.name,
                subskill_name=sub_obj.name if sub_obj else None,
                status="VERIFIED",
                confidence=1.0,
                reason=f"Exact match against canonical MoSPI competency '{comp_obj.name}'",
            )

        # 2. Curated Synonym & Cross-Agency Mapping
        if clean_comp in CURATED_TAXONOMY_ALIASES:
            canonical_comp_name, canonical_sub_name = CURATED_TAXONOMY_ALIASES[clean_comp]
            comp_obj = self._competencies.get(canonical_comp_name.lower())
            sub_obj = self._subskills.get(canonical_sub_name.lower()) if canonical_sub_name else None
            if comp_obj:
                return MappingResolution(
                    competency_id=comp_obj.id,
                    subskill_id=sub_obj.id if sub_obj else None,
                    competency_name=comp_obj.name,
                    subskill_name=sub_obj.name if sub_obj else None,
                    status="CURATED",
                    confidence=0.95,
                    reason=f"Resolved via curated synonym alias: '{competency_hint}' -> '{canonical_comp_name}'",
                )

        # 3. Fuzzy / Partial Substring & Token Overlap Search
        tokens = set(clean_comp.split())
        stop_words = {
            "and", "for", "in", "of", "the", "with", "to", "on", "a", "an",
            "methods", "techniques", "advanced", "data", "collection", "system", "systems",
        }
        meaningful_tokens = {t for t in tokens if len(t) > 3 and t not in stop_words}

        for canonical_name, comp_obj in self._competencies.items():
            if clean_comp in canonical_name or canonical_name in clean_comp:
                sub_obj = self._subskills.get(clean_sub) if clean_sub else None
                return MappingResolution(
                    competency_id=comp_obj.id,
                    subskill_id=sub_obj.id if sub_obj else None,
                    competency_name=comp_obj.name,
                    subskill_name=sub_obj.name if sub_obj else None,
                    status="PROVISIONAL",
                    confidence=0.75,
                    reason=f"Partial keyword match against '{comp_obj.name}'",
                )
            c_tokens = set(canonical_name.split())
            if meaningful_tokens & c_tokens:
                sub_obj = self._subskills.get(clean_sub) if clean_sub else None
                return MappingResolution(
                    competency_id=comp_obj.id,
                    subskill_id=sub_obj.id if sub_obj else None,
                    competency_name=comp_obj.name,
                    subskill_name=sub_obj.name if sub_obj else None,
                    status="PROVISIONAL",
                    confidence=0.70,
                    reason=f"Token overlap match against '{comp_obj.name}'",
                )

        # 4. Unknown / Malformed -> Safe Under-Review Isolation
        return MappingResolution(
            competency_id=None,
            subskill_id=None,
            competency_name=competency_hint,
            subskill_name=subskill_hint,
            status="UNDER_REVIEW",
            confidence=0.20,
            reason=f"Unrecognized provider taxonomy concept '{competency_hint}' quarantined under review",
        )
