from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill


def resolve_taxonomy(
    db: Session,
    competency_name: str,
    subskill_name: str,
) -> tuple[Competency, SubSkill]:
    """Resolve a competency and its competency-scoped subskill by name."""
    competency = db.execute(
        select(Competency).where(Competency.name == competency_name)
    ).scalar_one_or_none()
    if competency is None:
        raise ValueError(f"Invalid competency reference: {competency_name}")

    subskill = db.execute(
        select(SubSkill).where(
            SubSkill.competency_id == competency.id,
            SubSkill.name == subskill_name,
        )
    ).scalar_one_or_none()
    if subskill is not None:
        return competency, subskill

    elsewhere = db.execute(
        select(SubSkill.id).where(SubSkill.name == subskill_name)
    ).first()
    if elsewhere is not None:
        raise ValueError(
            f"Subskill '{subskill_name}' does not belong to "
            f"competency '{competency_name}'"
        )
    raise ValueError(f"Invalid subskill reference: {subskill_name}")