from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.intervention import Intervention

BASE_DIR = Path(__file__).resolve().parents[3]
REAL_DATA_DIR = BASE_DIR / "real_data" / "data"


def seed_intervention_catalog(db: Session) -> dict[str, int]:
    """Seed canonical interventions from real public sources and curated statistical exercises.

    Idempotently populates the Intervention table with:
    - Real public iGOT courses (REPLAY mode)
    - Real public NSSTA TPAC programmes (REPLAY mode)
    - Curated statistical practice drills, virtual labs, and scenario simulations
    - Explicit misconception remediation interventions
    - Test fixtures for STALE and UNAVAILABLE resources to verify failure filtering.
    """
    counts = {"igot": 0, "nssta": 0, "curated": 0, "remediation": 0, "total": 0}

    # Fetch competencies and subskills maps
    competencies = {c.name.strip(): c for c in db.execute(select(Competency)).scalars().all()}
    subskills = {s.name.strip(): s for s in db.execute(select(SubSkill)).scalars().all()}

    def get_or_create(
        source_id: str,
        title: str,
        competency_name: str | None,
        subskill_name: str | None,
        intervention_type: str,
        provider: str,
        modality: str,
        duration_minutes: int,
        difficulty: str,
        source: str,
        source_url: str | None,
        provenance: str,
        status: str = "ACTIVE",
        availability: str = "ALWAYS_AVAILABLE",
        prerequisites_json: str | None = None,
        target_misconception_pattern: str | None = None,
        description: str | None = None,
        priority: int = 1,
        last_verified_at: datetime | None = None,
    ) -> Intervention:
        existing = db.execute(
            select(Intervention).where(Intervention.source_id == source_id)
        ).scalar_one_or_none()

        comp = competencies.get(competency_name) if competency_name else None
        sub = subskills.get(subskill_name) if subskill_name else None

        if last_verified_at is None:
            last_verified_at = datetime.now(timezone.utc)

        if existing:
            # Update existing
            existing.title = title
            existing.competency_id = comp.id if comp else None
            existing.subskill_id = sub.id if sub else None
            existing.intervention_type = intervention_type
            existing.provider = provider
            existing.modality = modality
            existing.duration_minutes = duration_minutes
            existing.difficulty = difficulty
            existing.source = source
            existing.source_url = source_url
            existing.provenance = provenance
            existing.status = status
            existing.availability = availability
            existing.prerequisites_json = prerequisites_json
            existing.target_misconception_pattern = target_misconception_pattern
            existing.description = description
            existing.priority = priority
            existing.last_verified_at = last_verified_at
            return existing

        new_item = Intervention(
            source_id=source_id,
            title=title,
            competency_id=comp.id if comp else None,
            subskill_id=sub.id if sub else None,
            intervention_type=intervention_type,
            provider=provider,
            modality=modality,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            source=source,
            source_url=source_url,
            provenance=provenance,
            status=status,
            availability=availability,
            prerequisites_json=prerequisites_json,
            target_misconception_pattern=target_misconception_pattern,
            description=description,
            priority=priority,
            last_verified_at=last_verified_at,
        )
        db.add(new_item)
        return new_item

    # 1. Seed Real iGOT Courses
    igot_path = REAL_DATA_DIR / "igot_course_catalog.json"
    if igot_path.exists():
        with open(igot_path, "r", encoding="utf-8") as f:
            igot_data = json.load(f)
            for c in igot_data.get("courses", []):
                cid = c.get("catalogue_id")
                ctitle = c.get("course_title")
                # Map known iGOT courses to official competencies
                comp_name = None
                sub_name = None
                if cid == "IGOT-PUBLIC-001":
                    comp_name = "Administrative Data"
                    sub_name = "Registry data integration"
                elif cid == "IGOT-PUBLIC-002":
                    comp_name = "Python for Analytics"
                    sub_name = "Data cleaning with pandas"
                elif cid == "IGOT-PUBLIC-004":
                    comp_name = "Data Ethics"
                    sub_name = "Ethical guidelines"
                elif cid == "IGOT-PUBLIC-005":
                    comp_name = "Cybersecurity Awareness"
                    sub_name = "Threat identification"

                get_or_create(
                    source_id=cid,
                    title=ctitle,
                    competency_name=comp_name,
                    subskill_name=sub_name,
                    intervention_type="igot_resource",
                    provider="iGOT",
                    modality="ONLINE_SELF_PACED",
                    duration_minutes=150 if "2h" in str(c.get("duration")) else 60,
                    difficulty="intermediate",
                    source="iGOT Karmayogi",
                    source_url=c.get("course_url"),
                    provenance="[REAL/PUBLIC DATA]",
                    description=c.get("description") or f"Official iGOT course: {ctitle}",
                )
                counts["igot"] += 1

    # 2. Seed Real NSSTA TPAC Programmes
    nssta_path = REAL_DATA_DIR / "nssta_tpac_programmes.json"
    if nssta_path.exists():
        with open(nssta_path, "r", encoding="utf-8") as f:
            nssta_data = json.load(f)
            for idx, prog in enumerate(nssta_data, start=1):
                prog_id = f"NSSTA-PROG-{idx:03d}"
                ptitle = prog.get("programme_title")
                comp_name = None
                sub_name = None
                if "Machine Learning" in ptitle:
                    comp_name = "AI/ML Fundamentals"
                    sub_name = "Supervised learning models"
                elif "Cyber Security" in ptitle:
                    comp_name = "Cybersecurity Awareness"
                    sub_name = "Threat identification"
                elif "remote sensing" in ptitle.lower():
                    comp_name = "Survey Methodology"
                    sub_name = "Questionnaire design"
                elif "Data security and appropriate use of AI" in ptitle:
                    comp_name = "Data Ethics"
                    sub_name = "Bias detection"

                get_or_create(
                    source_id=prog_id,
                    title=f"NSSTA: {ptitle}",
                    competency_name=comp_name,
                    subskill_name=sub_name,
                    intervention_type="nssta_programme",
                    provider="NSSTA",
                    modality="CLASSROOM_RESIDENTIAL",
                    duration_minutes=2400,  # 1 week residential
                    difficulty="advanced",
                    source="NSSTA TPAC FY 2026-27",
                    source_url=prog.get("source_url"),
                    provenance="[REAL/PUBLIC DATA]",
                    description=prog.get("content"),
                )
                counts["nssta"] += 1

    # 3. Seed Curated Targeted Practices, Scenarios, Virtual Labs for Core Statistical Competencies
    curated_items = [
        {
            "source_id": "CURATED-SCENARIO-001",
            "title": "MoSPI Field Survey Simulation: Stratified Household Sampling",
            "competency_name": "Sampling Design",
            "subskill_name": "Stratified sampling",
            "intervention_type": "scenario_practice",
            "provider": "INTERNAL",
            "modality": "PRACTICE_SCENARIO",
            "duration_minutes": 45,
            "difficulty": "intermediate",
            "description": "Interactive scenario establishing stratum boundaries for urban/rural NSS consumer expenditure surveys.",
            "priority": 1,
        },
        {
            "source_id": "CURATED-LAB-001",
            "title": "Virtual Lab: Probability Sampling & Weight Adjustment Workbench",
            "competency_name": "Sampling Design",
            "subskill_name": "Probability sampling",
            "intervention_type": "virtual_lab",
            "provider": "VIRTUAL_LAB",
            "modality": "VIRTUAL_LAB",
            "duration_minutes": 60,
            "difficulty": "intermediate",
            "description": "Interactive sandbox simulation calculating inclusion probabilities and design effects.",
            "priority": 2,
        },
        {
            "source_id": "CURATED-PRACTICE-001",
            "title": "Targeted Retrieval Practice: Sample Size & Power Calculations",
            "competency_name": "Sampling Design",
            "subskill_name": "Sample size determination",
            "intervention_type": "retrieval_practice",
            "provider": "INTERNAL",
            "modality": "ASSESSMENT",
            "duration_minutes": 30,
            "difficulty": "hard",
            "description": "Targeted problem set computing sample size under margin of error and non-response constraints.",
            "priority": 3,
        },
        {
            "source_id": "CURATED-ASSESSMENT-001",
            "title": "Diagnostic Assessment Drill: Cluster Sampling Efficiency",
            "competency_name": "Sampling Design",
            "subskill_name": "Cluster sampling",
            "intervention_type": "targeted_assessment",
            "provider": "INTERNAL",
            "modality": "ASSESSMENT",
            "duration_minutes": 25,
            "difficulty": "intermediate",
            "description": "Formative assessment testing intra-cluster correlation and design effect adjustments.",
            "priority": 2,
        },
        {
            "source_id": "CURATED-SCENARIO-002",
            "title": "Data Quality Audit: Validating Survey Outliers and Missingness",
            "competency_name": "Data Quality",
            "subskill_name": "Validation rules",
            "intervention_type": "scenario_practice",
            "provider": "INTERNAL",
            "modality": "PRACTICE_SCENARIO",
            "duration_minutes": 40,
            "difficulty": "intermediate",
            "description": "Simulated field data audit applying deterministic edit rules and logical consistency checks.",
            "priority": 1,
        },
    ]

    for item in curated_items:
        get_or_create(
            source_id=item["source_id"],
            title=item["title"],
            competency_name=item["competency_name"],
            subskill_name=item["subskill_name"],
            intervention_type=item["intervention_type"],
            provider=item["provider"],
            modality=item["modality"],
            duration_minutes=item["duration_minutes"],
            difficulty=item["difficulty"],
            source="MoSPI Training Framework",
            source_url=None,
            provenance="[CURATED]",
            description=item["description"],
            priority=item["priority"],
        )
        counts["curated"] += 1

    # 4. Seed Misconception Remediation Interventions
    remediations = [
        {
            "source_id": "REMEDIATION-MISC-001",
            "title": "Contrastive Remediation: Stratified Sampling vs Cluster Sampling",
            "competency_name": "Sampling Design",
            "subskill_name": "Stratified sampling",
            "intervention_type": "remediation",
            "provider": "INTERNAL",
            "modality": "PRACTICE_SCENARIO",
            "duration_minutes": 30,
            "difficulty": "easy",
            "description": "Direct contrastive drill highlighting homogeneity within strata vs heterogeneity within clusters.",
            "target_misconception_pattern": "CONFUSED_STRATIFIED_WITH_CLUSTER",
            "priority": 1,
        },
        {
            "source_id": "REMEDIATION-MISC-002",
            "title": "Clarifying Randomization: Haphazard vs Strict Probability Sampling",
            "competency_name": "Sampling Design",
            "subskill_name": "Probability sampling",
            "intervention_type": "remediation",
            "provider": "INTERNAL",
            "modality": "ASSESSMENT",
            "duration_minutes": 20,
            "difficulty": "easy",
            "description": "Concept repair module resolving the misconception that haphazard selection is equivalent to random sampling.",
            "target_misconception_pattern": "CONFUSED_CONVENIENCE_WITH_RANDOM",
            "priority": 1,
        },
    ]

    for item in remediations:
        get_or_create(
            source_id=item["source_id"],
            title=item["title"],
            competency_name=item["competency_name"],
            subskill_name=item["subskill_name"],
            intervention_type=item["intervention_type"],
            provider=item["provider"],
            modality=item["modality"],
            duration_minutes=item["duration_minutes"],
            difficulty=item["difficulty"],
            source="GyanSetu Remediation Engine",
            source_url=None,
            provenance="[CURATED]",
            description=item["description"],
            target_misconception_pattern=item["target_misconception_pattern"],
            priority=1,
        )
        counts["remediation"] += 1

    # 5. Seed Test Boundary Fixtures: STALE resource, UNAVAILABLE resource, MISSING_PREREQUISITE
    # STALE resource fixture
    stale_date = datetime.now(timezone.utc) - timedelta(days=200)
    get_or_create(
        source_id="TEST-FIXTURE-STALE-001",
        title="Archived 2018 Sampling Reference (Expired Verification)",
        competency_name="Sampling Design",
        subskill_name="Stratified sampling",
        intervention_type="targeted_practice",
        provider="INTERNAL",
        modality="ONLINE_SELF_PACED",
        duration_minutes=45,
        difficulty="intermediate",
        source="Legacy Archive",
        source_url=None,
        provenance="[CURATED]",
        status="STALE",
        last_verified_at=stale_date,
        description="Legacy resource past verification validity period.",
    )

    # UNAVAILABLE resource fixture
    get_or_create(
        source_id="TEST-FIXTURE-UNAVAIL-001",
        title="Offline High Performance Computing Cluster Lab",
        competency_name="Sampling Design",
        subskill_name="Stratified sampling",
        intervention_type="virtual_lab",
        provider="VIRTUAL_LAB",
        modality="VIRTUAL_LAB",
        duration_minutes=90,
        difficulty="advanced",
        source="Specialized Hardware Cluster",
        source_url=None,
        provenance="[SANDBOX DATA]",
        status="UNAVAILABLE",
        availability="UNAVAILABLE",
        description="High-compute lab currently under scheduled maintenance.",
    )

    # PREREQUISITE restricted fixture
    prereq_meta = json.dumps({"required_subskills": ["Sample size determination"], "min_mastery": 0.70})
    get_or_create(
        source_id="TEST-FIXTURE-PREREQ-001",
        title="Advanced Optimal Sample Allocation for Multi-Stage Surveys",
        competency_name="Sampling Design",
        subskill_name="Stratified sampling",
        intervention_type="scenario_practice",
        provider="INTERNAL",
        modality="PRACTICE_SCENARIO",
        duration_minutes=75,
        difficulty="advanced",
        source="Advanced Survey Analytics",
        source_url=None,
        provenance="[CURATED]",
        status="ACTIVE",
        prerequisites_json=prereq_meta,
        description="Advanced optimization requiring prior verified sample size mastery.",
    )

    db.commit()
    counts["total"] = sum(counts.values())
    return counts
