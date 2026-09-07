"""
Question Bank Quality and Coverage Analysis Report Generator (Phase 1.3).

Analyzes the generated assessment question bank across:
- Total question counts and status
- Difficulty distribution (Easy / Medium / Hard)
- Competency and domain coverage
- Cognitive taxonomy distribution (Recall, Application, Analysis, Evaluation)
- Quality score statistics (Mean, Min, Max, Grounding Overlap, Distractor Entropy)
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict


def generate_question_bank_report(
    bank_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Analyzes the question bank JSON artifact and returns structured summary metrics."""
    if bank_path is None:
        bank_path = Path(__file__).resolve().parent / "seed_content" / "question_bank.json"

    bank_path = Path(bank_path)
    if not bank_path.exists():
        raise FileNotFoundError(f"Question bank artifact not found at {bank_path}")

    with open(bank_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    total_questions = len(questions)

    difficulties = Counter(q.get("difficulty", "unknown") for q in questions)
    cognitive_levels = Counter(q.get("cognitive_level", "unknown") for q in questions)
    competencies = Counter(q.get("competency", "unassigned") for q in questions)

    quality_scores = [float(q.get("quality_score", 0.0)) for q in questions]
    grounding_overlaps = [
        float(q.get("metrics", {}).get("grounding_overlap", 0.0)) for q in questions
    ]

    mean_quality = round(sum(quality_scores) / total_questions, 4) if total_questions else 0.0
    mean_grounding = round(sum(grounding_overlaps) / total_questions, 4) if total_questions else 0.0

    report = {
        "dataset_name": data.get("metadata", {}).get("dataset_name", "GyanSetu Question Bank"),
        "sandbox_data": data.get("metadata", {}).get("sandbox_data", True),
        "status": data.get("metadata", {}).get("status", "SANDBOX DATA"),
        "total_questions": total_questions,
        "difficulty_distribution": dict(difficulties),
        "cognitive_level_distribution": dict(cognitive_levels),
        "competency_count": len(competencies),
        "competencies": dict(competencies.most_common(10)),
        "quality_metrics": {
            "mean_quality_score": mean_quality,
            "min_quality_score": min(quality_scores) if quality_scores else 0.0,
            "max_quality_score": max(quality_scores) if quality_scores else 0.0,
            "mean_grounding_overlap": mean_grounding,
        },
    }
    return report


def print_report():
    report = generate_question_bank_report()
    print("=" * 65)
    print(f"GYANSETU QUESTION BANK REPORT [{report['status']}]")
    print("=" * 65)
    print(f"Total Questions Generated : {report['total_questions']}")
    print(f"Competencies Covered      : {report['competency_count']}")
    print(f"Average Quality Score     : {report['quality_metrics']['mean_quality_score']}")
    print(f"Average Grounding Overlap : {report['quality_metrics']['mean_grounding_overlap']}")
    print("\nDifficulty Breakdown:")
    for diff, count in report["difficulty_distribution"].items():
        print(f"  - {diff.capitalize():<8}: {count}")
    print("\nCognitive Levels:")
    for level, count in report["cognitive_level_distribution"].items():
        print(f"  - {level:<12}: {count}")
    print("=" * 65)


if __name__ == "__main__":
    print_report()
