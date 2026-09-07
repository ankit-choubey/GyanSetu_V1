from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.competency import Competency, Role, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.services.orchestrator import recalculate_competency_state


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    role = Role(name="Analyst")
    session.add(role)
    session.flush()

    user = User(email="history_user@example.com", full_name="History User", password_hash="hash", role_id=role.id)
    comp = Competency(role_id=role.id, name="Survey Methodology")
    session.add_all([user, comp])
    session.flush()

    sub = SubSkill(competency_id=comp.id, name="Frame Construction")
    session.add(sub)
    session.commit()

    yield session, user, comp, sub

    session.close()
    engine.dispose()


def test_competency_history_records_state_transitions(db):
    session, user, comp, sub = db

    # Initial state calculation (no evidence -> UNASSESSED)
    res1 = recalculate_competency_state(session, user.id, comp.id)
    session.commit()

    hist1 = session.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == user.id,
            CompetencyHistory.competency_id == comp.id,
        ).order_by(CompetencyHistory.state_version)
    ).scalars().all()

    assert len(hist1) == 1
    assert hist1[0].previous_mastery is None
    assert hist1[0].new_mastery is None
    assert hist1[0].new_status == "UNASSESSED"
    assert hist1[0].state_version == 1

    # Add first evidence (Score 0.50)
    ev1 = Evidence(
        user_id=user.id,
        competency_id=comp.id,
        subskill_id=sub.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Quiz 1",
        score=0.50,
        weight=0.20,
    )
    session.add(ev1)
    session.commit()

    res2 = recalculate_competency_state(session, user.id, comp.id, triggering_evidence_id=ev1.id)
    session.commit()

    hist2 = session.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == user.id,
            CompetencyHistory.competency_id == comp.id,
        ).order_by(CompetencyHistory.state_version)
    ).scalars().all()

    assert len(hist2) == 2
    assert hist2[1].previous_mastery is None
    assert hist2[1].new_mastery == 0.50
    assert hist2[1].triggering_evidence_id == ev1.id
    assert hist2[1].state_version == 2
    assert hist2[1].new_status == "ASSESSED"

    # Add second evidence (Score 1.00)
    ev2 = Evidence(
        user_id=user.id,
        competency_id=comp.id,
        subskill_id=sub.id,
        evidence_type=EvidenceType.APPLICATION_SCENARIO,
        title="Scenario 1",
        score=1.00,
        weight=0.35,
    )
    session.add(ev2)
    session.commit()

    res3 = recalculate_competency_state(session, user.id, comp.id, triggering_evidence_id=ev2.id)
    session.commit()

    hist3 = session.execute(
        select(CompetencyHistory).where(
            CompetencyHistory.user_id == user.id,
            CompetencyHistory.competency_id == comp.id,
        ).order_by(CompetencyHistory.state_version)
    ).scalars().all()

    assert len(hist3) == 3
    assert hist3[2].previous_mastery == 0.50
    assert hist3[2].new_mastery > 0.70
    assert hist3[2].triggering_evidence_id == ev2.id
    assert hist3[2].state_version == 3


def test_competency_state_uncertainty_is_one_minus_confidence(db):
    session, user, comp, _ = db
    state = CompetencyState(user_id=user.id, competency_id=comp.id, mastery=0.8, confidence=0.65)
    assert state.uncertainty == 0.35

    state.confidence = 0.95
    assert state.uncertainty == 0.05

    state.confidence = 0.0
    assert state.uncertainty == 1.0
