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


# Subskill aliases for cross-competency mismatch validation
CURATED_SUB_ALIASES: dict[str, tuple[str, str | None]] = {
    "cpi compilation": ("Index Numbers", "Price relatives"),
    "consumer price index compilation": ("Index Numbers", "Price relatives"),
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

        # Helper to validate subskill belongs to competency
        def _resolve_subskill(comp_id: int, sub_name_clean: str | None) -> tuple[int | None, str | None, bool]:
            if not sub_name_clean:
                return None, None, True
            s_obj = self._subskills.get(sub_name_clean)
            if not s_obj:
                # Subskill name not directly in dictionary; check partial
                for s_key, s_val in self._subskills.items():
                    if sub_name_clean in s_key or s_key in sub_name_clean:
                        s_obj = s_val
                        break
            if s_obj:
                if s_obj.competency_id == comp_id:
                    return s_obj.id, s_obj.name, True
                else:
                    # Mismatch: subskill belongs to a DIFFERENT competency!
                    return None, None, False

            # Check curated subskill aliases
            if sub_name_clean in CURATED_SUB_ALIASES:
                target_comp_name, canonical_sub = CURATED_SUB_ALIASES[sub_name_clean]
                target_comp = self._competencies.get(target_comp_name.lower())
                if target_comp:
                    if target_comp.id == comp_id:
                        sub_resolved = self._subskills.get(canonical_sub.lower()) if canonical_sub else None
                        return sub_resolved.id if sub_resolved else None, canonical_sub, True
                    else:
                        # Mismatch: subskill alias belongs to another competency!
                        return None, None, False

            return None, None, False

        # 1. Exact Match against Canonical Competencies
        if clean_comp in self._competencies:
            comp_obj = self._competencies[clean_comp]
            sub_id, sub_name, sub_valid = _resolve_subskill(comp_obj.id, clean_sub)
            if not sub_valid:
                return MappingResolution(
                    competency_id=comp_obj.id,
                    subskill_id=None,
                    competency_name=comp_obj.name,
                    subskill_name=subskill_hint,
                    status="UNDER_REVIEW",
                    confidence=0.30,
                    reason=f"Invalid mapping: subskill '{subskill_hint}' does not belong to competency '{comp_obj.name}'",
                )
            return MappingResolution(
                competency_id=comp_obj.id,
                subskill_id=sub_id,
                competency_name=comp_obj.name,
                subskill_name=sub_name,
                status="VERIFIED",
                confidence=1.0,
                reason=f"Exact match against canonical MoSPI competency '{comp_obj.name}'",
            )

        # 2. Curated Synonym & Cross-Agency Mapping
        if clean_comp in CURATED_TAXONOMY_ALIASES:
            canonical_comp_name, canonical_sub_name = CURATED_TAXONOMY_ALIASES[clean_comp]
            comp_obj = self._competencies.get(canonical_comp_name.lower())
            if comp_obj:
                effective_sub = clean_sub or (canonical_sub_name.lower() if canonical_sub_name else None)
                sub_id, sub_name, sub_valid = _resolve_subskill(comp_obj.id, effective_sub)
                if not sub_valid:
                    return MappingResolution(
                        competency_id=comp_obj.id,
                        subskill_id=None,
                        competency_name=comp_obj.name,
                        subskill_name=subskill_hint,
                        status="UNDER_REVIEW",
                        confidence=0.30,
                        reason=f"Invalid mapping: subskill '{subskill_hint}' does not belong to competency '{comp_obj.name}'",
                    )
                return MappingResolution(
                    competency_id=comp_obj.id,
                    subskill_id=sub_id,
                    competency_name=comp_obj.name,
                    subskill_name=sub_name,
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

    def validate_mapping(self, competency_id: int | None, subskill_id: int | None = None) -> tuple[bool, str]:
        """Strictly validate whether a competency exists and whether subskill belongs to it."""
        if competency_id is None:
            return False, "Competency ID is None (does not exist)"
        comp = self.db.get(Competency, competency_id)
        if not comp:
            return False, f"Competency ID {competency_id} does not exist in canonical taxonomy"
        if subskill_id is not None:
            sub = self.db.get(SubSkill, subskill_id)
            if not sub:
                return False, f"SubSkill ID {subskill_id} does not exist in canonical taxonomy"
            if sub.competency_id != competency_id:
                return False, f"SubSkill ID {subskill_id} belongs to Competency ID {sub.competency_id}, not {competency_id}"
        return True, "Mapping is valid"
