from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.misconception import Misconception
from app.models.user import User
from app.services.competency_engine import calculate_competency_state
from app.services.diagnostic_service import DiagnosticService
from app.services.misconception_tracker import resolve_misconception, track_response
from app.services.orchestrator import recalculate_competency_state


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()

    role = Role(name="Statistical Officer")
    db.add(role)
    db.flush()

    user = User(
        email="scenario_learner@example.com",
        full_name="Scenario Learner",
        password_hash="hashed_pw",
        role_id=role.id,
    )
    db.add(user)
    db.flush()

    # Create competencies
    comp_stat = Competency(role_id=role.id, name="Mathematical Statistics and Probability")
    comp_digital = Competency(role_id=role.id, name="Data Management and Processing")
    db.add_all([comp_stat, comp_digital])
    db.flush()

    db.add_all([
        RoleCompetency(role_id=role.id, competency_id=comp_stat.id),
        RoleCompetency(role_id=role.id, competency_id=comp_digital.id),
    ])

    sub_stat1 = SubSkill(competency_id=comp_stat.id, name="Probability Distributions")
    sub_stat2 = SubSkill(competency_id=comp_stat.id, name="Hypothesis Testing")
    sub_dig1 = SubSkill(competency_id=comp_digital.id, name="SQL Querying")
    sub_dig2 = SubSkill(competency_id=comp_digital.id, name="Data Pipeline Validation")
    db.add_all([sub_stat1, sub_stat2, sub_dig1, sub_dig2])
    db.commit()

    yield db, user, comp_stat, comp_digital, (sub_stat1, sub_stat2), (sub_dig1, sub_dig2)

    db.close()
    engine.dispose()


def test_scenario_a_strong_statistical_weak_digital(session):
    """Scenario A: Strong statistical / weak digital evidence."""
    db, user, comp_stat, comp_digital, (sub_s1, sub_s2), (sub_d1, sub_d2) = session

    # Add strong evidence for Statistical Competency
    db.add_all([
        Evidence(
            user_id=user.id,
            competency_id=comp_stat.id,
            subskill_id=sub_s1.id,
            evidence_type=EvidenceType.APPLICATION_SCENARIO,
            title="Advanced Probability Lab",
            score=0.90,
            weight=0.35,
        ),
        Evidence(
            user_id=user.id,
            competency_id=comp_stat.id,
            subskill_id=sub_s2.id,
            evidence_type=EvidenceType.PRACTICAL_TASK,
            title="Hypothesis Testing Task",
            score=0.85,
            weight=0.30,
        ),
    ])
    # Add weak evidence for Digital Competency
    db.add(
        Evidence(
            user_id=user.id,
            competency_id=comp_digital.id,
            subskill_id=sub_d1.id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Basic SQL Quiz",
            score=0.30,
            weight=0.20,
        )
    )
    db.commit()

    res_stat = recalculate_competency_state(db, user.id, comp_stat.id)
    res_digital = recalculate_competency_state(db, user.id, comp_digital.id)

    assert res_stat.state.mastery >= 0.85
    assert res_digital.state.mastery <= 0.40

    # Digital competency has high severity gaps
    assert len(res_digital.calculation.gaps) >= 1
    assert res_digital.calculation.gaps[0]["reason"] in ("low_mastery", "insufficient_evidence")


def test_scenario_b_strong_theory_weak_application(session):
    """Scenario B: Strong theory (knowledge) / weak application."""
    db, user, comp_stat, _, (sub_s1, sub_s2), _ = session

    db.add_all([
        Evidence(
            user_id=user.id,
            competency_id=comp_stat.id,
            subskill_id=sub_s1.id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Theory Exam",
            score=1.0,
            weight=0.20,
        ),
        Evidence(
            user_id=user.id,
            competency_id=comp_stat.id,
            subskill_id=sub_s1.id,
            evidence_type=EvidenceType.APPLICATION_SCENARIO,
            title="Field Scenario Test",
            score=0.40,
            weight=0.35,
        ),
    ])
    db.commit()

    res = recalculate_competency_state(db, user.id, comp_stat.id)
    # Must detect conflict and refuse to mark 'verified'
    assert res.state.status == "CONFLICTING_EVIDENCE"
    assert res.calculation.status == "CONFLICTING_EVIDENCE"


def test_scenario_c_little_or_no_evidence(session):
    """Scenario C: Little or no evidence (missing != low competency)."""
    db, user, comp_stat, _, _, _ = session

    # No evidence added
    res = recalculate_competency_state(db, user.id, comp_stat.id)

    assert res.state.mastery is None
    assert res.state.confidence == 0.0
    assert res.state.uncertainty == 1.0
    assert res.state.status == "UNASSESSED"
    assert res.state.evidence_count == 0


def test_scenario_d_conflicting_evidence_handling(session):
    """Scenario D: Conflicting evidence is flagged, not blindly averaged."""
    _, _, comp_stat, _, (sub_s1, _), _ = session

    # 0.98 Knowledge vs 0.35 Application Scenario
    ev1 = Evidence(
        user_id=1,
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Written Test",
        score=0.98,
    )
    ev2 = Evidence(
        user_id=1,
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        evidence_type=EvidenceType.APPLICATION_SCENARIO,
        title="Practical Execution",
        score=0.35,
    )
    calc = calculate_competency_state([ev1, ev2], total_subskills=2)

    assert calc.status == "CONFLICTING_EVIDENCE"
    assert calc.confidence <= 0.50


def test_scenario_e_stale_evidence_decay(session):
    """Scenario E: Stale evidence recency decay reduces effective weight."""
    now = datetime(2026, 9, 7, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(days=80)

    # 80 days old score of 0.20 vs recent score of 0.90
    ev_old = Evidence(
        user_id=1,
        competency_id=1,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Old quiz",
        score=0.20,
        observed_at=old_time,
    )
    ev_recent = Evidence(
        user_id=1,
        competency_id=1,
        evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
        title="Recent quiz",
        score=0.90,
        observed_at=now,
    )

    calc = calculate_competency_state([ev_old, ev_recent], total_subskills=1, now=now)
    # Without recency decay, average would be (0.2 + 0.9) / 2 = 0.55
    # With recency decay, old weight is 0.20 * (1 - 0.80) = 0.04, recent is 0.20 * 1.0 = 0.20
    # Expected weighted mastery > 0.75
    assert calc.mastery is not None
    assert calc.mastery > 0.70


def test_scenario_f_repeated_misconception_and_resolution(session):
    """Scenario F: Repeated misconception detection, tracking, and resolution."""
    db, user, comp_stat, _, (sub_s1, _), _ = session

    item = AssessmentItem(
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        question_text="What is the Central Limit Theorem?",
        options_json='["A. Sample means converge to normal", "B. Population is always normal", "C. Sample size does not matter", "D. Variance is zero"]',
        correct_option="A",
        difficulty="medium",
    )
    db.add(item)
    db.commit()

    attempt = AssessmentAttempt(user_id=user.id, competency_id=comp_stat.id)
    db.add(attempt)
    db.commit()

    # First wrong response: selected "B"
    resp1 = AssessmentResponse(
        attempt_id=attempt.id,
        assessment_item_id=item.id,
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        selected_option="B",
        is_correct=False,
    )
    res1 = track_response(db, resp1)
    assert res1.misconception is not None
    assert res1.misconception.occurrences == 1
    assert res1.misconception.resolved is False

    # Second wrong response: same error pattern
    resp2 = AssessmentResponse(
        attempt_id=attempt.id,
        assessment_item_id=item.id,
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        selected_option="B",
        is_correct=False,
    )
    res2 = track_response(db, resp2)
    assert res2.misconception.occurrences == 2

    # Follow-up remediation produces positive resolution evidence
    res_ev = Evidence(
        user_id=user.id,
        competency_id=comp_stat.id,
        subskill_id=sub_s1.id,
        evidence_type=EvidenceType.APPLICATION_SCENARIO,
        title="Remediation Scenario",
        score=1.0,
    )
    db.add(res_ev)
    db.commit()

    resolved = resolve_misconception(db, res2.misconception.id, resolution_evidence_id=res_ev.id, intervention_applied=True)
    assert resolved.resolved is True
    assert resolved.resolution_evidence_id == res_ev.id
    assert resolved.intervention_applied is True


def test_scenario_g_strong_performance_diverse_evidence(session):
    """Scenario G: Strong performance across diverse evidence achieves verified status."""
    db, user, comp_stat, _, (sub_s1, sub_s2), _ = session

    now = datetime.now(timezone.utc)
    evs = [
        Evidence(user_id=user.id, competency_id=comp_stat.id, subskill_id=sub_s1.id, evidence_type=EvidenceType.APPLICATION_SCENARIO, score=0.88, observed_at=now, title="Scenario 1"),
        Evidence(user_id=user.id, competency_id=comp_stat.id, subskill_id=sub_s2.id, evidence_type=EvidenceType.PRACTICAL_TASK, score=0.92, observed_at=now, title="Task 1"),
        Evidence(user_id=user.id, competency_id=comp_stat.id, subskill_id=sub_s1.id, evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT, score=0.85, observed_at=now, title="Quiz 1"),
        Evidence(user_id=user.id, competency_id=comp_stat.id, subskill_id=sub_s2.id, evidence_type=EvidenceType.TRAINING_HISTORY, score=0.95, observed_at=now, title="Course 1"),
        Evidence(user_id=user.id, competency_id=comp_stat.id, subskill_id=sub_s1.id, evidence_type=EvidenceType.WORKPLACE_SIGNAL, score=0.80, observed_at=now, title="Project 1"),
    ]
    db.add_all(evs)
    db.commit()

    res = recalculate_competency_state(db, user.id, comp_stat.id)

    assert res.state.mastery >= 0.85
    assert res.state.confidence >= 0.60
    assert res.state.uncertainty <= 0.40
    assert res.state.evidence_diversity == 5
    assert res.calculation.status == "verified"
