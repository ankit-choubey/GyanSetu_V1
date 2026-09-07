from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.governance import CompetencyGovernance, ReviewStatus
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.user import User


class DataQualityService:
    """Comprehensive data quality, integrity, and structural consistency diagnostic engine."""

    STALE_CUTOFF_DAYS = 180

    @classmethod
    def audit_taxonomy_integrity(cls, db: Session) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        comps = db.execute(select(Competency)).scalars().all()
        comp_ids = {c.id for c in comps}

        # 1. Orphan subskills
        subskills = db.execute(select(SubSkill)).scalars().all()
        orphan_subskills = [s for s in subskills if s.competency_id not in comp_ids]
        if orphan_subskills:
            issues.append({
                "severity": "ERROR",
                "category": "taxonomy",
                "code": "ORPHAN_SUBSKILLS",
                "affected_count": len(orphan_subskills),
                "description": f"{len(orphan_subskills)} subskills reference non-existent competency IDs.",
                "remediation": "Reassign subskills to canonical competencies or purge orphan rows.",
            })

        # 2. Invalid role mappings
        roles = db.execute(select(Role)).scalars().all()
        role_ids = {r.id for r in roles}
        role_comps = db.execute(select(RoleCompetency)).scalars().all()
        invalid_role_links = [
            rc for rc in role_comps
            if rc.role_id not in role_ids or rc.competency_id not in comp_ids
        ]
        if invalid_role_links:
            issues.append({
                "severity": "ERROR",
                "category": "taxonomy",
                "code": "INVALID_ROLE_MAPPING",
                "affected_count": len(invalid_role_links),
                "description": f"{len(invalid_role_links)} role-competency mappings reference invalid role or competency IDs.",
                "remediation": "Remove invalid role-competency mapping links.",
            })

        # 3. Duplicate role-competency mappings
        seen_links = set()
        dup_links = 0
        for rc in role_comps:
            pair = (rc.role_id, rc.competency_id)
            if pair in seen_links:
                dup_links += 1
            else:
                seen_links.add(pair)
        if dup_links > 0:
            issues.append({
                "severity": "WARNING",
                "category": "taxonomy",
                "code": "DUPLICATE_ROLE_MAPPING",
                "affected_count": dup_links,
                "description": f"{dup_links} duplicate role-competency relational mappings detected.",
                "remediation": "Deduplicate role_competencies table rows.",
            })

        # 4. Under review or deprecated competencies
        gov_records = db.execute(select(CompetencyGovernance)).scalars().all()
        under_review = [g for g in gov_records if g.review_status == ReviewStatus.UNDER_REVIEW.value]
        deprecated = [g for g in gov_records if g.is_deprecated]
        if under_review:
            issues.append({
                "severity": "INFO",
                "category": "taxonomy",
                "code": "UNVERIFIED_COMPETENCY_MAPPING",
                "affected_count": len(under_review),
                "competency_ids": [g.competency_id for g in under_review],
                "description": f"{len(under_review)} competencies are currently marked UNDER_REVIEW by domain governance.",
                "remediation": "Expert psychometric validation review required.",
            })
        if deprecated:
            issues.append({
                "severity": "WARNING",
                "category": "taxonomy",
                "code": "DEPRECATED_COMPETENCY_MAPPING",
                "affected_count": len(deprecated),
                "competency_ids": [g.competency_id for g in deprecated],
                "description": f"{len(deprecated)} competencies are flagged as DEPRECATED.",
                "remediation": "Migrate learner evidence records to successor competencies.",
            })

        return issues

    @classmethod
    def audit_evidence_integrity(cls, db: Session) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(days=cls.STALE_CUTOFF_DAYS)
        future_cutoff = now + timedelta(minutes=5)

        all_evidence = db.execute(select(Evidence)).scalars().all()
        user_ids = set(db.execute(select(User.id)).scalars().all())
        comp_ids = set(db.execute(select(Competency.id)).scalars().all())

        orphan_user_ev = 0
        orphan_comp_ev = 0
        stale_ev = 0
        future_ev = 0
        missing_provenance = 0

        for ev in all_evidence:
            if ev.user_id not in user_ids:
                orphan_user_ev += 1
            if ev.competency_id not in comp_ids:
                orphan_comp_ev += 1
            if not ev.provenance:
                missing_provenance += 1

            obs = ev.observed_at
            if obs:
                if obs.tzinfo is None:
                    obs = obs.replace(tzinfo=timezone.utc)
                if obs > future_cutoff:
                    future_ev += 1
                elif obs < stale_cutoff:
                    stale_ev += 1

        if orphan_user_ev > 0:
            issues.append({
                "severity": "ERROR",
                "category": "evidence",
                "code": "ORPHAN_EVIDENCE_USER",
                "affected_count": orphan_user_ev,
                "description": f"{orphan_user_ev} evidence records reference non-existent user IDs.",
                "remediation": "Purge orphan evidence records or reassign to valid user accounts.",
            })
        if orphan_comp_ev > 0:
            issues.append({
                "severity": "ERROR",
                "category": "evidence",
                "code": "ORPHAN_EVIDENCE_COMPETENCY",
                "affected_count": orphan_comp_ev,
                "description": f"{orphan_comp_ev} evidence records reference non-existent competency IDs.",
                "remediation": "Map evidence records to active canonical competencies.",
            })
        if future_ev > 0:
            issues.append({
                "severity": "ERROR",
                "category": "evidence",
                "code": "IMPOSSIBLE_FUTURE_TIMESTAMP",
                "affected_count": future_ev,
                "description": f"{future_ev} evidence records have timestamps in the future.",
                "remediation": "Correct clock skew or observation timestamps.",
            })
        if stale_ev > 0:
            issues.append({
                "severity": "WARNING",
                "category": "evidence",
                "code": "STALE_EVIDENCE",
                "affected_count": stale_ev,
                "description": f"{stale_ev} evidence records observed more than {cls.STALE_CUTOFF_DAYS} days ago without verification.",
                "remediation": "Trigger automated spaced reassessment via MonitoringAgent.",
            })
        if missing_provenance > 0:
            issues.append({
                "severity": "INFO",
                "category": "evidence",
                "code": "MISSING_PROVENANCE",
                "affected_count": missing_provenance,
                "description": f"{missing_provenance} evidence records lack explicit provenance tags.",
                "remediation": "Populate default [CURATED:DIAGNOSTIC] provenance tags.",
            })

        return issues

    @classmethod
    def audit_assessment_integrity(cls, db: Session) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        items = db.execute(select(AssessmentItem)).scalars().all()
        comp_ids = set(db.execute(select(Competency.id)).scalars().all())

        orphan_comp_items = 0
        malformed_options = 0
        invalid_keys = 0
        normalized_texts: set[str] = set()
        duplicate_questions = 0

        for item in items:
            if item.competency_id not in comp_ids:
                orphan_comp_items += 1

            # Check duplicate question text
            norm_q = " ".join(item.question_text.lower().split()) if item.question_text else ""
            if norm_q in normalized_texts:
                duplicate_questions += 1
            else:
                normalized_texts.add(norm_q)

            # Check options JSON and correct key
            try:
                opts = json.loads(item.options_json) if item.options_json else None
                if not opts or not isinstance(opts, (dict, list)) or len(opts) < 2:
                    malformed_options += 1
                else:
                    if item.correct_option:
                        if isinstance(opts, dict) and item.correct_option not in opts:
                            invalid_keys += 1
                        elif isinstance(opts, list):
                            if item.correct_option not in opts and item.correct_option not in {"A", "B", "C", "D"}:
                                invalid_keys += 1
            except Exception:
                malformed_options += 1

        if orphan_comp_items > 0:
            issues.append({
                "severity": "ERROR",
                "category": "assessment",
                "code": "ORPHAN_ASSESSMENT_COMPETENCY",
                "affected_count": orphan_comp_items,
                "description": f"{orphan_comp_items} assessment items reference invalid competency IDs.",
                "remediation": "Reassign items to valid competencies.",
            })
        if malformed_options > 0:
            issues.append({
                "severity": "ERROR",
                "category": "assessment",
                "code": "MALFORMED_OPTIONS_JSON",
                "affected_count": malformed_options,
                "description": f"{malformed_options} assessment items have invalid or insufficient (< 2) options JSON.",
                "remediation": "Reformat options JSON into structured key-value dictionaries.",
            })
        if invalid_keys > 0:
            issues.append({
                "severity": "ERROR",
                "category": "assessment",
                "code": "INVALID_ANSWER_KEY",
                "affected_count": invalid_keys,
                "description": f"{invalid_keys} assessment items have correct_option keys not present in options.",
                "remediation": "Align correct_option values with options dictionary keys.",
            })
        if duplicate_questions > 0:
            issues.append({
                "severity": "WARNING",
                "category": "assessment",
                "code": "DUPLICATE_QUESTIONS",
                "affected_count": duplicate_questions,
                "description": f"{duplicate_questions} potential duplicate questions detected in assessment item bank.",
                "remediation": "Review question bank items for deduplication.",
            })

        return issues

    @classmethod
    def audit_intervention_integrity(cls, db: Session) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(days=cls.STALE_CUTOFF_DAYS)

        items = db.execute(select(Intervention)).scalars().all()
        comp_ids = set(db.execute(select(Competency.id)).scalars().all())

        stale_active_items = 0
        orphan_comp_interventions = 0
        seen_provider_sources = set()
        duplicate_sources = 0

        for it in items:
            if it.competency_id not in comp_ids:
                orphan_comp_interventions += 1

            key = (it.provider, it.source_id)
            if key in seen_provider_sources:
                duplicate_sources += 1
            else:
                seen_provider_sources.add(key)

            if it.status == "ACTIVE" and it.last_verified_at:
                lva = it.last_verified_at
                if lva.tzinfo is None:
                    lva = lva.replace(tzinfo=timezone.utc)
                if lva < stale_cutoff:
                    stale_active_items += 1

        if orphan_comp_interventions > 0:
            issues.append({
                "severity": "ERROR",
                "category": "intervention",
                "code": "ORPHAN_INTERVENTION_COMPETENCY",
                "affected_count": orphan_comp_interventions,
                "description": f"{orphan_comp_interventions} interventions reference non-existent competency IDs.",
                "remediation": "Re-map interventions via CompetencyMappingService.",
            })
        if duplicate_sources > 0:
            issues.append({
                "severity": "ERROR",
                "category": "intervention",
                "code": "DUPLICATE_PROVIDER_SOURCE_ID",
                "affected_count": duplicate_sources,
                "description": f"{duplicate_sources} duplicate interventions detected with identical (provider, source_id).",
                "remediation": "Run ecosystem deduplication script.",
            })
        if stale_active_items > 0:
            issues.append({
                "severity": "WARNING",
                "category": "intervention",
                "code": "STALE_ACTIVE_INTERVENTION",
                "affected_count": stale_active_items,
                "description": f"{stale_active_items} interventions marked ACTIVE have not been verified within {cls.STALE_CUTOFF_DAYS} days.",
                "remediation": "Run catalog synchronization or mark as STALE.",
            })

        return issues

    @classmethod
    def audit_competency_state_integrity(cls, db: Session) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        states = db.execute(select(CompetencyState)).scalars().all()
        user_ids = set(db.execute(select(User.id)).scalars().all())
        comp_ids = set(db.execute(select(Competency.id)).scalars().all())

        orphan_user_states = 0
        orphan_comp_states = 0
        out_of_bounds_mastery = 0
        out_of_bounds_confidence = 0
        invalid_uncertainty = 0
        conflicting_states = 0

        for st in states:
            if st.user_id not in user_ids:
                orphan_user_states += 1
            if st.competency_id not in comp_ids:
                orphan_comp_states += 1

            if st.mastery is not None and (st.mastery < 0.0 or st.mastery > 1.0):
                out_of_bounds_mastery += 1
            if st.confidence is not None and (st.confidence < 0.0 or st.confidence > 1.0):
                out_of_bounds_confidence += 1

            if st.confidence is not None:
                expected_u = round(1.0 - st.confidence, 4)
                actual_u = round(st.uncertainty, 4)
                if abs(expected_u - actual_u) > 0.01:
                    invalid_uncertainty += 1

            if st.status == "CONFLICTING_EVIDENCE":
                conflicting_states += 1

        if orphan_user_states > 0:
            issues.append({
                "severity": "ERROR",
                "category": "competency_state",
                "code": "ORPHAN_STATE_USER",
                "affected_count": orphan_user_states,
                "description": f"{orphan_user_states} competency states reference non-existent user IDs.",
                "remediation": "Purge orphan competency state records.",
            })
        if orphan_comp_states > 0:
            issues.append({
                "severity": "ERROR",
                "category": "competency_state",
                "code": "ORPHAN_STATE_COMPETENCY",
                "affected_count": orphan_comp_states,
                "description": f"{orphan_comp_states} competency states reference non-existent competency IDs.",
                "remediation": "Reassign states to active competencies.",
            })
        if out_of_bounds_mastery > 0:
            issues.append({
                "severity": "ERROR",
                "category": "competency_state",
                "code": "OUT_OF_BOUNDS_MASTERY",
                "affected_count": out_of_bounds_mastery,
                "description": f"{out_of_bounds_mastery} competency states have mastery outside [0.0, 1.0].",
                "remediation": "Clamp mastery scores to [0.0, 1.0].",
            })
        if out_of_bounds_confidence > 0:
            issues.append({
                "severity": "ERROR",
                "category": "competency_state",
                "code": "OUT_OF_BOUNDS_CONFIDENCE",
                "affected_count": out_of_bounds_confidence,
                "description": f"{out_of_bounds_confidence} competency states have confidence outside [0.0, 1.0].",
                "remediation": "Clamp confidence to [0.0, 1.0].",
            })
        if invalid_uncertainty > 0:
            issues.append({
                "severity": "WARNING",
                "category": "competency_state",
                "code": "UNCERTAINTY_INCONSISTENCY",
                "affected_count": invalid_uncertainty,
                "description": f"{invalid_uncertainty} states exhibit uncertainty != 1.0 - confidence.",
                "remediation": "Recalculate uncertainty property dynamically.",
            })
        if conflicting_states > 0:
            issues.append({
                "severity": "WARNING",
                "category": "competency_state",
                "code": "CONFLICTING_EVIDENCE_STATE",
                "affected_count": conflicting_states,
                "description": f"{conflicting_states} competency states are flagged with conflicting multi-source evidence.",
                "remediation": "Schedule supervised diagnostic or practical verification.",
            })

        return issues

    @classmethod
    def audit_data_quality(cls, db: Session) -> dict[str, Any]:
        """Runs the complete data quality audit across all operational domains."""
        all_issues: list[dict[str, Any]] = []
        all_issues.extend(cls.audit_taxonomy_integrity(db))
        all_issues.extend(cls.audit_evidence_integrity(db))
        all_issues.extend(cls.audit_assessment_integrity(db))
        all_issues.extend(cls.audit_intervention_integrity(db))
        all_issues.extend(cls.audit_competency_state_integrity(db))

        errors = [i for i in all_issues if i.get("severity") == "ERROR"]
        warnings = [i for i in all_issues if i.get("severity") == "WARNING"]
        info_items = [i for i in all_issues if i.get("severity") == "INFO"]

        # Health score calculation (1.00 base, deductions for errors and warnings)
        penalty = min(80, len(errors) * 20 + len(warnings) * 5)
        health_score = round(max(0.0, (100 - penalty) / 100.0), 2)
        status = "HEALTHY" if health_score >= 0.85 else ("ATTENTION_REQUIRED" if health_score >= 0.60 else "DEGRADED")

        return {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_data_health_score": health_score,
            "status": status,
            "total_issues_count": len(all_issues),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "info_count": len(info_items),
            "issues": all_issues,
            "provenance": "[DATA_QUALITY_AUDIT:FULL_SYSTEM_SCAN]",
        }

    @classmethod
    def get_summary(cls, db: Session) -> dict[str, Any]:
        """Provides a high-level summary scorecard of data quality and structural integrity."""
        full_audit = cls.audit_data_quality(db)
        issues = full_audit["issues"]

        category_breakdown: dict[str, dict[str, int]] = {}
        for item in issues:
            cat = item.get("category", "general")
            sev = item.get("severity", "INFO")
            if cat not in category_breakdown:
                category_breakdown[cat] = {"ERROR": 0, "WARNING": 0, "INFO": 0, "TOTAL": 0}
            category_breakdown[cat][sev] += 1
            category_breakdown[cat]["TOTAL"] += 1

        return {
            "audit_timestamp": full_audit["audit_timestamp"],
            "overall_data_health_score": full_audit["overall_data_health_score"],
            "status": full_audit["status"],
            "errors_count": full_audit["errors_count"],
            "warnings_count": full_audit["warnings_count"],
            "info_count": full_audit["info_count"],
            "category_breakdown": category_breakdown,
            "provenance": "[DATA_QUALITY_AUDIT:SUMMARY]",
        }

    @classmethod
    def audit_category(cls, db: Session, category: str) -> dict[str, Any]:
        """Runs targeted data quality diagnostics for a specific operational domain."""
        cat = category.lower().strip()
        issues: list[dict[str, Any]] = []

        if cat == "taxonomy":
            issues = cls.audit_taxonomy_integrity(db)
        elif cat == "evidence":
            issues = cls.audit_evidence_integrity(db)
        elif cat == "assessment":
            issues = cls.audit_assessment_integrity(db)
        elif cat == "intervention":
            issues = cls.audit_intervention_integrity(db)
        elif cat in {"competency_state", "competency"}:
            issues = cls.audit_competency_state_integrity(db)
        else:
            return {
                "category": category,
                "error": f"Unknown diagnostic category '{category}'. Allowed: taxonomy, evidence, assessment, intervention, competency_state",
            }

        return {
            "category": cat,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "issues_count": len(issues),
            "errors_count": sum(1 for i in issues if i.get("severity") == "ERROR"),
            "warnings_count": sum(1 for i in issues if i.get("severity") == "WARNING"),
            "info_count": sum(1 for i in issues if i.get("severity") == "INFO"),
            "issues": issues,
            "provenance": f"[DATA_QUALITY_AUDIT:{cat.upper()}]",
        }
