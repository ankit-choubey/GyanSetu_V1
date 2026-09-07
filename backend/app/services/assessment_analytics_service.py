from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, SubSkill


class AssessmentAnalyticsService:
    """Psychometric item response analysis, distractor diagnostic, and lifecycle governance service."""

    MIN_SAMPLE_FOR_DISCRIMINATION = 10
    MIN_SAMPLE_FOR_FLAGS = 5

    @classmethod
    def get_item_statistics(cls, db: Session, item_id: int) -> dict[str, Any]:
        """Calculates empirical response metrics, difficulty, distractor utilization, and discrimination for an item."""
        item = db.execute(select(AssessmentItem).where(AssessmentItem.id == item_id)).scalar_one_or_none()
        if not item:
            return {"error": f"Assessment item {item_id} not found."}

        responses = db.execute(
            select(AssessmentResponse).where(AssessmentResponse.assessment_item_id == item_id)
        ).scalars().all()

        total_attempts = len(responses)
        if total_attempts == 0:
            return {
                "item_id": item.id,
                "question_text": item.question_text,
                "competency_id": item.competency_id,
                "subskill_id": item.subskill_id,
                "status": "INSUFFICIENT_DATA",
                "sample_size": 0,
                "difficulty_index": None,
                "discrimination_index": None,
                "distractor_analysis": {},
                "quality_flags": ["INSUFFICIENT_DATA", "NEVER_ATTEMPTED"],
                "lifecycle_recommendation": "REVIEW",
                "provenance": "[ITEM_ANALYTICS:COLD_START]",
            }

        correct_count = sum(1 for r in responses if r.is_correct)
        incorrect_count = total_attempts - correct_count
        difficulty_p = round(correct_count / total_attempts, 4)

        # Parse options
        try:
            options_dict = json.loads(item.options_json) if item.options_json else {}
        except Exception:
            options_dict = {}

        # Distractor utilization
        selected_counter = Counter(r.selected_option for r in responses)
        option_distribution: dict[str, Any] = {}
        for opt_key in options_dict.keys():
            count = selected_counter.get(opt_key, 0)
            option_distribution[opt_key] = {
                "count": count,
                "selection_rate": round(count / total_attempts, 4),
                "is_correct": (opt_key == item.correct_option),
            }

        # Discrimination Index (Point-Biserial Correlation if N >= 10)
        discrimination: float | None = None
        if total_attempts >= cls.MIN_SAMPLE_FOR_DISCRIMINATION:
            attempt_ids = [r.attempt_id for r in responses]
            attempts = db.execute(
                select(AssessmentAttempt).where(AssessmentAttempt.id.in_(attempt_ids))
            ).scalars().all()
            score_by_attempt = {a.id: (a.score or 0.0) for a in attempts}

            # Learners who got this item right vs wrong
            correct_scores = [score_by_attempt.get(r.attempt_id, 0.0) for r in responses if r.is_correct]
            all_scores = [score_by_attempt.get(r.attempt_id, 0.0) for r in responses]

            if len(all_scores) > 1:
                mean_total = sum(all_scores) / len(all_scores)
                variance = sum((s - mean_total) ** 2 for s in all_scores) / len(all_scores)
                std_dev = math.sqrt(variance)

                if std_dev > 0.001 and correct_scores:
                    mean_correct = sum(correct_scores) / len(correct_scores)
                    p = correct_count / total_attempts
                    q = 1.0 - p
                    if p * q > 0:
                        r_pb = ((mean_correct - mean_total) / std_dev) * math.sqrt(p * q)
                        discrimination = round(r_pb, 4)

        # Quality Flags
        quality_flags: list[str] = []
        if total_attempts < cls.MIN_SAMPLE_FOR_FLAGS:
            quality_flags.append("INSUFFICIENT_DATA")
        else:
            if difficulty_p > 0.95:
                quality_flags.append("EXTREMELY_EASY")
            elif difficulty_p < 0.20:
                quality_flags.append("EXTREMELY_HARD")

            if discrimination is not None and discrimination < 0.15:
                quality_flags.append("LOW_DISCRIMINATION")

            # Check distractor anomalies
            correct_opt = item.correct_option
            correct_opt_count = selected_counter.get(correct_opt, 0)
            for opt_k, dist_data in option_distribution.items():
                if not dist_data["is_correct"]:
                    if total_attempts >= 10 and dist_data["count"] == 0:
                        quality_flags.append("DISTRACTOR_UNUSED")
                    if dist_data["count"] > correct_opt_count:
                        quality_flags.append("DISTRACTOR_DOMINANT")

        # Lifecycle recommendation
        if "EXTREMELY_HARD" in quality_flags or "LOW_DISCRIMINATION" in quality_flags or "DISTRACTOR_DOMINANT" in quality_flags:
            lifecycle_rec = "REVIEW"
        elif "INSUFFICIENT_DATA" in quality_flags:
            lifecycle_rec = "PERFORMANCE_MONITORED"
        else:
            lifecycle_rec = "RETAIN"

        return {
            "item_id": item.id,
            "question_text": item.question_text,
            "competency_id": item.competency_id,
            "subskill_id": item.subskill_id,
            "difficulty_assigned": item.difficulty,
            "status": "EVALUATED" if total_attempts >= cls.MIN_SAMPLE_FOR_FLAGS else "INSUFFICIENT_DATA",
            "sample_size": total_attempts,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "difficulty_index": difficulty_p,
            "discrimination_index": discrimination,
            "option_distribution": option_distribution,
            "quality_flags": sorted(list(set(quality_flags))),
            "lifecycle_recommendation": lifecycle_rec,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "provenance": "[PSYCHOMETRIC_ITEM_ANALYTICS:OBSERVED_RESPONSES]",
        }

    @classmethod
    def get_question_bank_analytics(
        cls,
        db: Session,
        competency_id: int | None = None,
        subskill_id: int | None = None,
        quality_flag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Returns aggregated analytics across the question bank with optional filtering."""
        stmt = select(AssessmentItem)
        if competency_id is not None:
            stmt = stmt.where(AssessmentItem.competency_id == competency_id)
        if subskill_id is not None:
            stmt = stmt.where(AssessmentItem.subskill_id == subskill_id)

        items = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
        total_items = db.execute(select(func.count(AssessmentItem.id))).scalar_one() or 0

        analyzed_items: list[dict[str, Any]] = []
        for it in items:
            stat = cls.get_item_statistics(db, it.id)
            if quality_flag:
                if quality_flag in stat.get("quality_flags", []):
                    analyzed_items.append(stat)
            else:
                analyzed_items.append(stat)

        # Summary statistics
        total_evaluated = sum(1 for a in analyzed_items if a.get("status") == "EVALUATED")
        flagged_count = sum(1 for a in analyzed_items if a.get("quality_flags") and "INSUFFICIENT_DATA" not in a.get("quality_flags"))

        return {
            "total_items_in_catalog": total_items,
            "page_items_count": len(analyzed_items),
            "evaluated_count": total_evaluated,
            "flagged_for_review_count": flagged_count,
            "items": analyzed_items,
            "provenance": "[ASSESSMENT_ANALYTICS:CATALOG_OVERVIEW]",
        }
