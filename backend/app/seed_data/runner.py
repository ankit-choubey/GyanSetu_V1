from __future__ import annotations

import json
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.user import User
from app.seed_data.competency_taxonomy import COMPETENCIES, DOMAIN_BY_COMPETENCY, ROLES
from app.seed_data.question_bank_loader import load_question_bank
from app.utils.security import hash_password


def seed_full_taxonomy(seed_password: str | None = None) -> None:
    seed_password = seed_password or os.getenv("SEED_PASSWORD")
    if not seed_password:
        raise ValueError("SEED_PASSWORD must be provided for local seed data")

    taxonomy_names = {item.name for item in COMPETENCIES}
    db = SessionLocal()
    try:
        with db.begin():
            role_map: dict[str, Role] = {}
            for role_spec in ROLES:
                role = db.execute(select(Role).where(Role.name == role_spec.name)).scalar_one_or_none()
                if role is None:
                    role = Role(name=role_spec.name, description="GyanSetu official-statistics workforce taxonomy role")
                    db.add(role)
                    db.flush()
                role_map[role_spec.name] = role

            existing_competencies = db.execute(select(Competency)).scalars().all()
            unknown = sorted({comp.name for comp in existing_competencies if comp.name not in taxonomy_names})
            if unknown:
                raise ValueError(
                    "Unexpected legacy competencies require explicit domain mapping before taxonomy seeding: "
                    + ", ".join(unknown)
                )

            competency_map: dict[str, Competency] = {}
            for competency_spec in COMPETENCIES:
                competency = db.execute(
                    select(Competency).where(Competency.name == competency_spec.name)
                ).scalar_one_or_none()
                if competency is None:
                    primary_role = role_map[next(role.name for role in ROLES if competency_spec.name in role.competency_names)]
                    competency = Competency(
                        role_id=primary_role.id,
                        name=competency_spec.name,
                        domain=competency_spec.domain,
                        description=f"Structured GyanSetu taxonomy competency in the {competency_spec.domain.value} domain.",
                    )
                    db.add(competency)
                    db.flush()
                elif competency.domain != competency_spec.domain:
                    competency.domain = competency_spec.domain
                competency_map[competency_spec.name] = competency

                for subskill_name in competency_spec.subskills:
                    subskill = db.execute(
                        select(SubSkill).where(
                            SubSkill.competency_id == competency.id,
                            SubSkill.name == subskill_name,
                        )
                    ).scalar_one_or_none()
                    if subskill is None:
                        db.add(
                            SubSkill(
                                competency_id=competency.id,
                                name=subskill_name,
                                description=f"Assessment-ready subskill for {competency_spec.name}.",
                            )
                        )
                db.flush()

            for role_spec in ROLES:
                role = role_map[role_spec.name]
                for competency_name in role_spec.competency_names:
                    competency = competency_map[competency_name]
                    link = db.execute(
                        select(RoleCompetency).where(
                            RoleCompetency.role_id == role.id,
                            RoleCompetency.competency_id == competency.id,
                        )
                    ).scalar_one_or_none()
                    if link is None:
                        db.add(RoleCompetency(role_id=role.id, competency_id=competency.id))

            statistical_officer = role_map["Statistical Officer"]
            learner = db.execute(select(User).where(User.email == "learner@example.com")).scalar_one_or_none()
            if learner is None:
                learner = User(
                    email="learner@example.com",
                    full_name="Sample Learner",
                    password_hash=hash_password(seed_password),
                    role_id=statistical_officer.id,
                    is_active=True,
                )
                db.add(learner)
                db.flush()
            elif learner.role_id != statistical_officer.id:
                learner.role_id = statistical_officer.id

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

            sandbox_user = db.execute(
                select(User).where(User.email == "sandbox.analyst@example.com")
            ).scalar_one_or_none()
            if sandbox_user is None:
                sandbox_user = User(
                    email="sandbox.analyst@example.com",
                    full_name="Sandbox Analyst",
                    password_hash=hash_password(seed_password),
                    role_id=statistical_officer.id,
                    is_active=True,
                )
                db.add(sandbox_user)
                db.flush()

            for competency in competency_map.values():
                state = db.execute(
                    select(CompetencyState).where(
                        CompetencyState.user_id == learner.id,
                        CompetencyState.competency_id == competency.id,
                    )
                ).scalar_one_or_none()
                if state is None:
                    db.add(CompetencyState(user_id=learner.id, competency_id=competency.id))

            sampling = competency_map["Sampling Design"]
            sampling_subskill = db.execute(
                select(SubSkill).where(SubSkill.competency_id == sampling.id).order_by(SubSkill.id)
            ).scalars().first()
            evidence = db.execute(
                select(Evidence).where(
                    Evidence.user_id == learner.id,
                    Evidence.competency_id == sampling.id,
                    Evidence.title == "Sample training history",
                )
            ).scalar_one_or_none()
            if evidence is None:
                db.add(
                    Evidence(
                        user_id=learner.id,
                        competency_id=sampling.id,
                        subskill_id=sampling_subskill.id if sampling_subskill else None,
                        evidence_type=EvidenceType.TRAINING_HISTORY,
                        title="Sample training history",
                        description="Synthetic sandbox training evidence.",
                        score=1.0,
                        weight=0.1,
                        evidence_metadata=json.dumps({"source": "sandbox"}),
                    )
                )

            data_quality = competency_map["Data Quality"]
            bank_item = db.execute(
                select(AssessmentItem).where(
                    AssessmentItem.source_reference == "sample-data-quality",
                    AssessmentItem.user_id.is_(None),
                )
            ).scalar_one_or_none()
            if bank_item is None:
                subskill = db.execute(
                    select(SubSkill).where(SubSkill.competency_id == data_quality.id).order_by(SubSkill.id)
                ).scalars().first()
                db.add(
                    AssessmentItem(
                        user_id=None,
                        competency_id=data_quality.id,
                        subskill_id=subskill.id if subskill else None,
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

            load_question_bank(db)

            for competency in competency_map.values():
                subskill = db.execute(
                    select(SubSkill).where(SubSkill.competency_id == competency.id).order_by(SubSkill.id)
                ).scalars().first()
                intervention_title = f"{competency.name} development practice"
                existing = db.execute(
                    select(Intervention).where(
                        Intervention.competency_id == competency.id,
                        Intervention.title == intervention_title,
                    )
                ).scalar_one_or_none()
                if existing is None:
                    db.add(
                        Intervention(
                            user_id=None,
                            competency_id=competency.id,
                            subskill_id=subskill.id if subskill else None,
                            title=intervention_title,
                            description="Synthetic sandbox development intervention.",
                            intervention_type="PRACTICE",
                            priority=1,
                        )
                    )
    finally:
        db.close()
