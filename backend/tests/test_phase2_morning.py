from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy.pool import StaticPool

from app.models.competency import Competency, Role, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User
from app.services.competency_engine import calculate_competency_state
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
    role = Role(name="Test Role")
    session.add(role)
    session.flush()
    user = User(email="engine@example.com", full_name="Engine User", password_hash="hashed", role_id=role.id)
    competency = Competency(role_id=role.id, name="Sampling Design")
    session.add_all([user, competency])
    session.flush()
    subskill = SubSkill(competency_id=competency.id, name="Variance Estimation")
    other_subskill = SubSkill(competency_id=competency.id, name="Stratified Sampling")
    session.add_all([subskill, other_subskill])
    session.commit()
    yield session, user, competency, subskill, other_subskill
    session.close()
    engine.dispose()


def evidence(score, evidence_type, subskill_id, observed_at=None):
    return SimpleNamespace(
        score=score,
        evidence_type=evidence_type,
        subskill_id=subskill_id,
        observed_at=observed_at or datetime(2026, 9, 5, tzinfo=timezone.utc),
    )


def test_no_evidence_is_unassessed():
    result = calculate_competency_state([], total_subskills=2)
    assert result.mastery is None
    assert result.confidence == 0.0
    assert result.coverage == 0.0
    assert result.evidence_count == 0
    assert result.evidence_diversity == 0
    assert result.status == "UNASSESSED"
    assert result.gaps == ()


def test_single_evidence_uses_build_guide_baseline():
    result = calculate_competency_state(
        [evidence(0.8, EvidenceType.KNOWLEDGE_ASSESSMENT, 1)],
        total_subskills=2,
        now=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    assert result.mastery == 0.8
    assert result.confidence == 0.2
    assert result.coverage == pytest.approx(1 / 6)
    assert result.evidence_count == 1
    assert result.evidence_diversity == 1
    assert result.status == "developing"


def test_multiple_evidence_fuses_weighted_scores_and_diversity():
    result = calculate_competency_state(
        [
            evidence(1.0, EvidenceType.APPLICATION_SCENARIO, 1),
            evidence(0.5, EvidenceType.KNOWLEDGE_ASSESSMENT, 2),
        ],
        total_subskills=2,
        now=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    expected = (1.0 * 0.35 + 0.5 * 0.20) / (0.35 + 0.20)
    assert result.mastery == round(expected, 2)
    assert result.confidence == 0.4
    assert result.coverage == pytest.approx(2 / 6)
    assert result.evidence_diversity == 2


def test_gap_detection_identifies_low_and_uncovered_subskills(db):
    session, _, competency, subskill, other_subskill = db
    low = Evidence(
        user_id=1,
        competency_id=competency.id,
        subskill_id=subskill.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Low assessment",
        score=0.2,
    )
    session.add(low)
    session.commit()
    result = recalculate_competency_state(session, 1, competency.id)
    reasons = {gap["reason"] for gap in result.calculation.gaps}
    assert reasons == {"low_mastery", "insufficient_evidence"}
    gaps_by_subskill = {gap["subskill_id"]: gap for gap in result.calculation.gaps}
    assert gaps_by_subskill[subskill.id]["reason"] == "low_mastery"
    assert gaps_by_subskill[other_subskill.id]["reason"] == "insufficient_evidence"


def test_orchestrator_updates_state_from_stored_evidence(db):
    session, user, competency, subskill, _ = db
    session.add(
        Evidence(
            user_id=user.id,
            competency_id=competency.id,
            subskill_id=subskill.id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Assessment evidence",
            score=0.9,
        )
    )
    session.commit()
    result = recalculate_competency_state(session, user.id, competency.id)
    session.commit()
    state = session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == user.id,
            CompetencyState.competency_id == competency.id,
        )
    ).scalar_one()
    assert result.state.id == state.id
    assert state.mastery == 0.9
    assert state.evidence_count == 1
    assert state.status == "ASSESSED"


def test_orchestrator_caller_transaction_rolls_back_evidence_and_state(db):
    session, user, competency, subskill, _ = db
    with pytest.raises(RuntimeError):
        with session.begin():
            session.add(
                Evidence(
                    user_id=user.id,
                    competency_id=competency.id,
                    subskill_id=subskill.id,
                    evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
                    title="Rolled back evidence",
                    score=1.0,
                )
            )
            session.flush()
            recalculate_competency_state(session, user.id, competency.id)
            raise RuntimeError("forced orchestration failure")

    assert session.execute(
        select(Evidence).where(Evidence.title == "Rolled back evidence")
    ).scalar_one_or_none() is None
    assert session.execute(
        select(CompetencyState).where(
            CompetencyState.user_id == user.id,
            CompetencyState.competency_id == competency.id,
        )
    ).scalar_one_or_none() is None


def test_conflicting_evidence_is_flagged():
    result = calculate_competency_state(
        [
            evidence(0.95, EvidenceType.KNOWLEDGE_ASSESSMENT, 1),
            evidence(0.4, EvidenceType.APPLICATION_SCENARIO, 1),
        ],
        total_subskills=1,
        now=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    assert result.status == "CONFLICTING_EVIDENCE"
