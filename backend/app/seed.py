from __future__ import annotations

import json
import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.user import User
from app.utils.security import hash_password


def seed_data(seed_password: str | None = None) -> None:
    seed_password = seed_password or os.getenv("SEED_PASSWORD")
    if not seed_password:
        raise ValueError("SEED_PASSWORD must be provided for local seed data")

    db = SessionLocal()
    try:
        with db.begin():
            role = db.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
            if role is None:
                role = Role(name="Statistical Officer", description="Sample role for official statistics workflows")
                db.add(role)
                db.flush()

            competency_names = ["Sampling Design", "Data Quality", "Python for Analytics"]
            comp_map: dict[str, Competency] = {}
            for name in competency_names:
                comp = db.execute(
                    select(Competency).where(Competency.role_id == role.id, Competency.name == name)
                ).scalar_one_or_none()
                if comp is None:
                    comp = Competency(role_id=role.id, name=name, description=f"Sample competency: {name}")
                    db.add(comp)
                    db.flush()
                comp_map[name] = comp

            subskill_map: dict[str, SubSkill] = {}
            for name, comp in comp_map.items():
                subskill_name = f"{name} fundamentals"
                sub = db.execute(
                    select(SubSkill).where(SubSkill.competency_id == comp.id, SubSkill.name == subskill_name)
                ).scalar_one_or_none()
                if sub is None:
                    sub = SubSkill(competency_id=comp.id, name=subskill_name, description=f"Sample subskill for {name}")
                    db.add(sub)
                    db.flush()
                subskill_map[f"{name}-fundamentals"] = sub

            user = db.execute(select(User).where(User.email == "learner@example.com")).scalar_one_or_none()
            if user is None:
                user = User(
                    email="learner@example.com",
                    full_name="Sample Learner",
                    password_hash=hash_password(seed_password),
                    role_id=role.id,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            elif user.role_id != role.id:
                user.role_id = role.id

            for comp in comp_map.values():
                state = db.execute(
                    select(CompetencyState).where(
                        CompetencyState.user_id == user.id,
                        CompetencyState.competency_id == comp.id,
                    )
                ).scalar_one_or_none()
                if state is None:
                    db.add(CompetencyState(user_id=user.id, competency_id=comp.id))

            evidence = db.execute(
                select(Evidence).where(
                    Evidence.user_id == user.id,
                    Evidence.competency_id == comp_map["Sampling Design"].id,
                    Evidence.evidence_type == EvidenceType.TRAINING_HISTORY,
                    Evidence.title.in_(["Sample training history", "Profile evidence"]),
                )
            ).scalar_one_or_none()
            if evidence is None:
                evidence = Evidence(
                    user_id=user.id,
                    competency_id=comp_map["Sampling Design"].id,
                    subskill_id=subskill_map["Sampling Design-fundamentals"].id,
                    evidence_type=EvidenceType.TRAINING_HISTORY,
                    title="Sample training history",
                )
                db.add(evidence)
            evidence.evidence_type = EvidenceType.TRAINING_HISTORY
            evidence.title = "Sample training history"
            evidence.description = "Sample verified training record."
            evidence.score = 1.0
            evidence.weight = 0.1
            evidence.evidence_metadata = json.dumps({"source": "sample"})
            db.flush()

            state = db.execute(
                select(CompetencyState).where(
                    CompetencyState.user_id == user.id,
                    CompetencyState.competency_id == comp_map["Sampling Design"].id,
                )
            ).scalar_one()
            sampling_evidence = db.execute(
                select(Evidence).where(
                    Evidence.user_id == user.id,
                    Evidence.competency_id == comp_map["Sampling Design"].id,
                )
            ).scalars().all()
            scored_evidence = [entry.score for entry in sampling_evidence if entry.score is not None]
            state.mastery = sum(scored_evidence) / len(scored_evidence) if scored_evidence else None
            state.confidence = min(1.0, len(sampling_evidence) / 5) if sampling_evidence else 0.0
            state.coverage = min(1.0, len({entry.evidence_type for entry in sampling_evidence}) / 6) if sampling_evidence else 0.0
            state.evidence_count = len(sampling_evidence)
            state.evidence_diversity = len({entry.evidence_type for entry in sampling_evidence})
            state.status = "ASSESSED" if sampling_evidence else "UNASSESSED"

            bank_item = db.execute(
                select(AssessmentItem).where(
                    AssessmentItem.source_reference == "sample-data-quality",
                    AssessmentItem.user_id.is_(None),
                )
            ).scalar_one_or_none()
            if bank_item is None:
                db.add(
                    AssessmentItem(
                        user_id=None,
                        competency_id=comp_map["Data Quality"].id,
                        subskill_id=subskill_map["Data Quality-fundamentals"].id,
                        question_text="Which validation step is essential for a statistical dataset?",
                        options_json=json.dumps([
                            "A. Ignore missing values",
                            "B. Validate field consistency",
                            "C. Share raw CSV without checks",
                            "D. Delete all metadata",
                        ]),
                        correct_option="B",
                        difficulty="easy",
                        source_reference="sample-data-quality",
                    )
                )
            elif bank_item.user_id is not None:
                bank_item.user_id = None

            admin_role = db.execute(select(Role).where(Role.name == "Administrator")).scalar_one_or_none()
            if admin_role is None:
                admin_role = Role(name="Administrator", description="Sandbox administrator role")
                db.add(admin_role)
                db.flush()
            admin_user = db.execute(select(User).where(User.email == "admin@example.com")).scalar_one_or_none()
            if admin_user is None:
                db.add(
                    User(
                        email="admin@example.com",
                        full_name="Sandbox Administrator",
                        password_hash=hash_password(seed_password),
                        role_id=admin_role.id,
                        is_active=True,
                    )
                )

            sandbox_user = db.execute(select(User).where(User.email == "sandbox.analyst@example.com")).scalar_one_or_none()
            if sandbox_user is None:
                sandbox_user = User(
                    email="sandbox.analyst@example.com",
                    full_name="Sandbox Analyst",
                    password_hash=hash_password(seed_password),
                    role_id=role.id,
                    is_active=True,
                )
                db.add(sandbox_user)
                db.flush()
            for comp in comp_map.values():
                state = db.execute(
                    select(CompetencyState).where(
                        CompetencyState.user_id == sandbox_user.id,
                        CompetencyState.competency_id == comp.id,
                    )
                ).scalar_one_or_none()
                if state is None:
                    db.add(CompetencyState(user_id=sandbox_user.id, competency_id=comp.id))

            sandbox_evidence = [
                ("Data Quality", EvidenceType.KNOWLEDGE_ASSESSMENT, 0.75),
                ("Python for Analytics", EvidenceType.SELF_REPORT, 0.5),
            ]
            for competency_name, evidence_type, score in sandbox_evidence:
                competency = comp_map[competency_name]
                title = f"Sandbox {evidence_type.value} evidence"
                evidence = db.execute(
                    select(Evidence).where(
                        Evidence.user_id == sandbox_user.id,
                        Evidence.competency_id == competency.id,
                        Evidence.evidence_type == evidence_type,
                        Evidence.title == title,
                    )
                ).scalar_one_or_none()
                if evidence is None:
                    db.add(
                        Evidence(
                            user_id=sandbox_user.id,
                            competency_id=competency.id,
                            subskill_id=subskill_map[f"{competency_name}-fundamentals"].id,
                            evidence_type=evidence_type,
                            title=title,
                            description="Synthetic sandbox evidence for Phase 2 integration testing.",
                            score=score,
                            weight=1.0,
                            evidence_metadata=json.dumps({"source": "sandbox"}),
                        )
                    )

            db.flush()
            for competency in comp_map.values():
                state = db.execute(
                    select(CompetencyState).where(
                        CompetencyState.user_id == sandbox_user.id,
                        CompetencyState.competency_id == competency.id,
                    )
                ).scalar_one()
                evidence_rows = db.execute(
                    select(Evidence).where(
                        Evidence.user_id == sandbox_user.id,
                        Evidence.competency_id == competency.id,
                    )
                ).scalars().all()
                scores = [entry.score for entry in evidence_rows if entry.score is not None]
                state.mastery = sum(scores) / len(scores) if scores else None
                state.confidence = min(0.95, len(evidence_rows) / 5) if evidence_rows else 0.0
                state.coverage = min(1.0, len({entry.evidence_type for entry in evidence_rows}) / 6) if evidence_rows else 0.0
                state.evidence_count = len(evidence_rows)
                state.evidence_diversity = len({entry.evidence_type for entry in evidence_rows})
                state.status = "ASSESSED" if evidence_rows else "UNASSESSED"

            intervention_specs = [
                ("Sampling Design", "Sampling practice task", "PRACTICE", 1),
                ("Data Quality", "Data validation workshop", "TRAINING", 1),
                ("Python for Analytics", "Python analytics lab", "PRACTICE", 2),
            ]
            for competency_name, title, intervention_type, priority in intervention_specs:
                competency = comp_map[competency_name]
                existing_intervention = db.execute(
                    select(Intervention).where(
                        Intervention.competency_id == competency.id,
                        Intervention.title == title,
                    )
                ).scalar_one_or_none()
                if existing_intervention is None:
                    db.add(
                        Intervention(
                            user_id=None,
                            competency_id=competency.id,
                            subskill_id=subskill_map[f"{competency_name}-fundamentals"].id,
                            title=title,
                            description="Synthetic sandbox learning intervention.",
                            intervention_type=intervention_type,
                            priority=priority,
                        )
                    )
    finally:
        db.close()
