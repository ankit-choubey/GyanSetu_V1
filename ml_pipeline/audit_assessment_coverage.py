"""
ml_pipeline/audit_assessment_coverage.py — Assessment Bank Coverage & Diagnostics Auditor.

Audits assessment-bank coverage against:
ROLE -> REQUIRED COMPETENCIES -> SUBSKILLS -> ASSESSMENT ITEMS

Calculates and reports:
- questions per competency
- questions per subskill
- questions per role
- uncovered subskills
- competencies with insufficient assessment coverage (<3 items)
- duplicate/near-duplicate questions
- Bloom-level distribution
- difficulty distribution
- source distribution
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ml_pipeline.canonical_taxonomy import (
    CANONICAL_COMPETENCIES,
    CANONICAL_SUBSKILLS,
)

# Canonical 8 Roles and their required competencies
ROLE_TAXONOMY: dict[str, tuple[str, ...]] = {
    "Statistical Officer": (
        "Sampling Design", "Data Quality", "Survey Methodology", "Estimation",
        "SDG Indicators", "Communication", "Professional Ethics"
    ),
    "Senior Statistical Officer": (
        "Sampling Design", "Data Quality", "Survey Methodology", "Statistical Modelling",
        "Time Series", "Estimation", "Training Delivery", "Stakeholder Engagement"
    ),
    "Assistant Director": (
        "Survey Methodology", "Statistical Modelling", "National Accounts", "Index Numbers",
        "Administrative Data", "Project Management", "Team Leadership", "Policy Coordination"
    ),
    "Deputy Director": (
        "National Accounts", "Index Numbers", "Time Series", "Administrative Data",
        "SDG Indicators", "Strategic Planning", "Performance Management", "Data Governance"
    ),
    "Director": (
        "Statistical Modelling", "National Accounts", "SDG Indicators", "Data Governance",
        "Data Ethics", "Technology Risk Management", "Strategic Planning", "Policy Coordination",
        "Stakeholder Engagement", "Change Management", "Professional Ethics"
    ),
    "Statistical Investigator": (
        "Sampling Design", "Data Quality", "Survey Methodology", "Administrative Data",
        "Python for Analytics", "Data Visualization", "Communication"
    ),
    "Data Analyst": (
        "Data Quality", "Python for Analytics", "Data Pipelines", "Database Management",
        "Data Visualization", "Data Science", "Statistical Computing", "Automation",
        "AI/ML Fundamentals", "Data Privacy", "Open Data Standards"
    ),
    "IT Officer": (
        "Database Management", "Data Pipelines", "Cloud and Infrastructure", "Automation",
        "Data Architecture", "Cybersecurity Awareness", "Government Cloud", "Open Data Standards",
        "Digital Records Management", "Digital Service Delivery", "Information Security Governance",
        "Technology Risk Management"
    ),
}


def audit_question_bank(
    questions: list[dict[str, Any]],
    min_items_per_competency: int = 3,
) -> dict[str, Any]:
    """
    Comprehensive audit of an assessment question bank against canonical taxonomy & roles.
    """
    total_questions = len(questions)

    # 1. Distributions
    difficulty_counts = Counter()
    bloom_counts = Counter()
    source_counts = Counter()
    provenance_state_counts = Counter()

    questions_by_competency: dict[str, list[dict]] = defaultdict(list)
    questions_by_subskill: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for q in questions:
        diff = q.get("difficulty", "unspecified")
        difficulty_counts[diff] += 1

        bloom = q.get("cognitive_level") or q.get("bloom_level") or "Recall"
        bloom_counts[bloom] += 1

        src = q.get("source")
        if isinstance(src, dict):
            src_name = src.get("document_id") or src.get("title") or "Unknown"
        else:
            src_name = str(src or q.get("provenance") or "Unknown")
        source_counts[src_name] += 1

        prov_state = q.get("provenance_state") or q.get("status") or "UNSPECIFIED"
        provenance_state_counts[prov_state] += 1

        comp = q.get("competency") or q.get("competency_name") or ""
        sub = q.get("subskill") or q.get("subskill_name") or ""
        questions_by_competency[comp].append(q)
        if comp and sub:
            questions_by_subskill[(comp, sub)].append(q)

    # 2. Competency coverage
    comp_coverage = {}
    insufficient_competencies = []
    for comp in CANONICAL_COMPETENCIES:
        count = len(questions_by_competency.get(comp, []))
        comp_coverage[comp] = count
        if count < min_items_per_competency:
            insufficient_competencies.append({"competency": comp, "count": count})

    # 3. Subskill coverage
    subskill_coverage = {}
    uncovered_subskills = []
    for comp, subskills in CANONICAL_SUBSKILLS.items():
        for sub in subskills:
            count = len(questions_by_subskill.get((comp, sub), []))
            subskill_coverage[f"{comp} -> {sub}"] = count
            if count == 0:
                uncovered_subskills.append({"competency": comp, "subskill": sub})

    # 4. Role coverage
    role_coverage = {}
    for role, required_comps in ROLE_TAXONOMY.items():
        role_questions = sum(len(questions_by_competency.get(comp, [])) for comp in required_comps)
        role_uncovered_comps = [comp for comp in required_comps if len(questions_by_competency.get(comp, [])) == 0]
        role_coverage[role] = {
            "total_questions": role_questions,
            "required_competencies": len(required_comps),
            "covered_competencies": len(required_comps) - len(role_uncovered_comps),
            "uncovered_competencies": role_uncovered_comps,
        }

    # 5. Near-duplicate check
    duplicates = []
    q_texts = [q.get("question") or q.get("question_text") or "" for q in questions]
    for i in range(len(q_texts)):
        for j in range(i + 1, len(q_texts)):
            if not q_texts[i] or not q_texts[j]:
                continue
            ratio = SequenceMatcher(None, q_texts[i].lower(), q_texts[j].lower()).ratio()
            if ratio >= 0.88:
                duplicates.append({
                    "index_1": i,
                    "index_2": j,
                    "similarity": round(ratio, 3),
                    "q1": q_texts[i][:80],
                    "q2": q_texts[j][:80],
                })

    report = {
        "total_questions": total_questions,
        "difficulty_distribution": dict(difficulty_counts),
        "bloom_level_distribution": dict(bloom_counts),
        "source_distribution": dict(source_counts),
        "provenance_state_distribution": dict(provenance_state_counts),
        "competencies_total": len(CANONICAL_COMPETENCIES),
        "competencies_covered": len([c for c, count in comp_coverage.items() if count > 0]),
        "competencies_insufficient": insufficient_competencies,
        "subskills_total": sum(len(subs) for subs in CANONICAL_SUBSKILLS.values()),
        "subskills_covered": len(subskill_coverage) - len(uncovered_subskills),
        "uncovered_subskills": uncovered_subskills,
        "role_coverage": role_coverage,
        "near_duplicate_count": len(duplicates),
        "near_duplicates": duplicates,
    }
    return report


def print_audit_report(report: dict[str, Any]) -> None:
    print("=" * 60)
    print("GYANSETU ASSESSMENT BANK COVERAGE AUDIT")
    print("=" * 60)
    print(f"Total Questions: {report['total_questions']}")
    print(f"Difficulty: {report['difficulty_distribution']}")
    print(f"Bloom Levels: {report['bloom_level_distribution']}")
    print(f"Provenance States: {report['provenance_state_distribution']}")
    print(f"Competencies Covered: {report['competencies_covered']} / {report['competencies_total']}")
    print(f"Subskills Covered: {report['subskills_covered']} / {report['subskills_total']}")
    print(f"Near Duplicates: {report['near_duplicate_count']}")
    print("-" * 60)
    print("ROLE COVERAGE:")
    for role, data in report["role_coverage"].items():
        print(f"  - {role:28s}: {data['total_questions']:3d} questions | {data['covered_competencies']}/{data['required_competencies']} comps")
    print("-" * 60)
    if report["uncovered_subskills"]:
        print(f"UNCOVERED SUBSKILLS ({len(report['uncovered_subskills'])}):")
        for item in report["uncovered_subskills"][:10]:
            print(f"  - {item['competency']} -> {item['subskill']}")
        if len(report["uncovered_subskills"]) > 10:
            print(f"  ... and {len(report['uncovered_subskills']) - 10} more")
    else:
        print("ALL SUBSKILLS 100% COVERED!")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ml_pipeline/seed_content/question_bank.json")
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        qs = data if isinstance(data, list) else data.get("questions", [])
        rep = audit_question_bank(qs)
        print_audit_report(rep)
    else:
        print(f"File not found: {target_path}")
