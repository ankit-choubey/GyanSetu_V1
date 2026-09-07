import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.models.scenario import ScenarioItem
from app.models.scenario_attempt import ScenarioAttempt


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return engine


def create_scenario(session):
    scenario = ScenarioItem(
        competency_id=1,
        title="Test Scenario",
        scenario_text="Test scenario context.",
        context_data="{}",
        question="What should the learner do?",
        response_type="structured_text",
        instructions="Explain your reasoning.",
        expected_reasoning='{"key_points":["Test point"]}',
        rubric='{"criteria":[],"max_score":10}',
        difficulty="medium",
        cognitive_level="application",
    )
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario


@pytest.mark.parametrize(
    "score",
    [-1, 11],
)
def test_invalid_score_rejected(engine, score):
    with Session(engine) as session:
        scenario = create_scenario(session)

        attempt = ScenarioAttempt(
            user_id=1,
            scenario_id=scenario.id,
            response_text="Test response",
            score=score,
        )

        session.add(attempt)

        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize(
    "percentage",
    [-1, 101],
)
def test_invalid_percentage_rejected(engine, percentage):
    with Session(engine) as session:
        scenario = create_scenario(session)

        attempt = ScenarioAttempt(
            user_id=1,
            scenario_id=scenario.id,
            response_text="Test response",
            percentage=percentage,
        )

        session.add(attempt)

        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize(
    "confidence",
    [-0.1, 1.1],
)
def test_invalid_confidence_rejected(engine, confidence):
    with Session(engine) as session:
        scenario = create_scenario(session)

        attempt = ScenarioAttempt(
            user_id=1,
            scenario_id=scenario.id,
            response_text="Test response",
            confidence=confidence,
        )

        session.add(attempt)

        with pytest.raises(IntegrityError):
            session.commit()