from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.competency import Competency, Role, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.user import User
from app.services.competency_engine import CompetencyCalculation
from app.services.diagnostic_agent import DiagnosticAgent
from app.services.intervention_agent import InterventionAgent
from app.services.ml_interfaces import ProposedQuestion, QuestionSelectionRequest
from app.services.orchestrator import coordinate_diagnostic, coordinate_intervention


@dataclass
class SelectorDouble:
    response: object
    calls: int = 0
    request: QuestionSelectionRequest | None = None

    def select_next_question(self, request: QuestionSelectionRequest):
        self.calls += 1
        self.request = request
        return self.response


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    role = Role(name="Afternoon Role")
    session.add(role)
    session.flush()
    user = User(email="afternoon@example.com", full_name="Afternoon User", password_hash="hashed", role_id=role.id)
    competency = Competency(role_id=role.id, name="Data Quality")
    session.add_all([user, competency])
    session.flush()
    subskill = SubSkill(competency_id=competency.id, name="Validation")
    session.add(subskill)
    session.commit()
    yield session, user, competency, subskill
    session.close()
    engine.dispose()


def calculation(status="developing", gaps=(), evidence_count=1, evidence_diversity=1):
    return CompetencyCalculation(
        mastery=0.4,
        confidence=0.2,
        coverage=1 / 6,
        evidence_count=evidence_count,
        evidence_diversity=evidence_diversity,
        status=status,
        gaps=tuple(gaps),
    )


def valid_question(competency_id: int, subskill_id: int) -> ProposedQuestion:
    return ProposedQuestion(
        question_id=7,
        competency_id=competency_id,
        subskill_id=subskill_id,
        question_text="Which validation step protects data quality?",
        options=("A. Validate fields", "B. Ignore errors", "C. Delete metadata", "D. Skip review"),
        difficulty="medium",
        source_reference="test-double",
    )


def test_sufficient_evidence_stops_without_calling_ml():
    selector = SelectorDouble(response=None)
    decision = DiagnosticAgent().decide(1, calculation(status="verified", evidence_count=5), selector)
    assert decision.sufficient_evidence is True
    assert decision.next_question is None
    assert selector.calls == 0


def test_insufficient_evidence_requests_question_for_gap():
    gap = {"subskill_id": 4, "subskill_name": "Validation", "reason": "low_mastery", "severity": 0.6}
    selector = SelectorDouble(response=valid_question(1, 4))
    decision = DiagnosticAgent().decide(1, calculation(gaps=(gap,)), selector)
    assert decision.sufficient_evidence is False
    assert decision.target_subskill_id == 4
    assert decision.next_question.question_id == 7
    assert selector.calls == 1
    assert selector.request.subskill_id == 4
    assert selector.request.constraints


def test_diagnostic_does_not_choose_difficulty_or_recalculate():
    gap = {"subskill_id": 4, "subskill_name": "Validation", "reason": "insufficient_evidence", "severity": 1.0}
    selector = SelectorDouble(response=valid_question(1, 4))
    decision = DiagnosticAgent().decide(1, calculation(gaps=(gap,)), selector)
    assert decision.next_question.difficulty == "medium"
    assert not hasattr(selector.request, "selected_difficulty")


def test_malformed_ml_response_is_rejected():
    gap = {"subskill_id": 4, "subskill_name": "Validation", "reason": "low_mastery", "severity": 0.6}
    selector = SelectorDouble(response={"question_id": 7, "competency_id": 1, "options": ["only one"]})
    with pytest.raises(ValueError, match="malformed|exactly four"):
        DiagnosticAgent().decide(1, calculation(gaps=(gap,)), selector)


def test_intervention_ranking_is_deterministic_and_explainable(db):
    session, user, competency, subskill = db
    session.add_all([
        Intervention(
            user_id=None,
            competency_id=competency.id,
            subskill_id=subskill.id,
            title="Validation exercise",
            description="Practice validation decisions.",
            intervention_type="PRACTICE",
            priority=2,
        ),
        Intervention(
            user_id=None,
            competency_id=competency.id,
            title="Data quality module",
            description="Review data quality foundations.",
            intervention_type="TRAINING",
            priority=1,
        ),
    ])
    session.commit()
    gap = {"subskill_id": subskill.id, "reason": "low_mastery"}
    result = InterventionAgent().rank(session, user.id, competency.id, gap)
    assert result.selected.title == "Validation exercise"
    assert result.selected.relevance == 1.0
    assert result.selected.reason == "Directly targets the identified subskill gap."
    assert len(result.ranked_options) == 2


def test_no_suitable_intervention_is_explicit(db):
    session, user, competency, subskill = db
    result = InterventionAgent().rank(
        session,
        user.id,
        competency.id,
        {"subskill_id": subskill.id, "reason": "insufficient_evidence"},
    )
    assert result.selected is None
    assert result.ranked_options == ()
    assert result.uncertainty is not None


def test_assessment_to_diagnostic_and_intervention_integration(db):
    session, user, competency, subskill = db
    session.add(
        Evidence(
            user_id=user.id,
            competency_id=competency.id,
            subskill_id=subskill.id,
            evidence_type=EvidenceType.KNOWLEDGE_ASSESSMENT,
            title="Diagnostic evidence",
            score=0.4,
        )
    )
    session.add(
        Intervention(
            user_id=None,
            competency_id=competency.id,
            subskill_id=subskill.id,
            title="Targeted validation practice",
            description="Practice validation decisions.",
            intervention_type="PRACTICE",
            priority=1,
        )
    )
    session.commit()

    gap = {"subskill_id": subskill.id, "subskill_name": subskill.name, "reason": "low_mastery", "severity": 0.6}
    selector = SelectorDouble(response=valid_question(competency.id, subskill.id))
    orchestration, diagnostic = coordinate_diagnostic(session, user.id, competency.id, selector)
    assert orchestration.calculation.gaps
    assert diagnostic.target_subskill_id == subskill.id

    action = coordinate_intervention(session, user.id, orchestration)
    assert action.selected.title == "Targeted validation practice"
    assert action.competency_id == competency.id
