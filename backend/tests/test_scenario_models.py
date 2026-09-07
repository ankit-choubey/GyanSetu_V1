from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.scenario import ScenarioItem
from app.models.scenario_attempt import ScenarioAttempt


def test_scenario_item_and_attempt_persist():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        scenario = ScenarioItem(
            competency_id=1,
            subskill_id=2,
            title="Sampling Design Scenario",
            scenario_text=(
                "A statistical team needs to select a sampling "
                "method based on the training material."
            ),
            context_data="{}",
            question=(
                "Which approach would you choose and why?"
            ),
            response_type="structured_text",
            instructions=(
                "Explain your reasoning using the concepts "
                "from the training material."
            ),
            expected_reasoning=(
                '{"key_points":["Identify the appropriate '
                'sampling concept"]}'
            ),
            rubric=(
                '{"criteria":[{"criterion_id":"C1",'
                '"description":"Explains the reasoning",'
                '"max_score":10}],"max_score":10}'
            ),
            difficulty="medium",
            cognitive_level="application",
            source_reference="training material",
        )

        session.add(scenario)
        session.commit()
        session.refresh(scenario)

        assert scenario.id is not None

        attempt = ScenarioAttempt(
            user_id=1,
            scenario_id=scenario.id,
            response_text=(
                "I would choose the approach that matches "
                "the sampling concept described in the material."
            ),
            score=8,
            percentage=80.0,
            overall_result="partially_correct",
            evaluation_feedback='{"summary":"Good reasoning"}',
            evaluation_criterion_results=(
                '[{"criterion_id":"C1","score":8}]'
            ),
            confidence=0.8,
            demonstrated_competency=True,
            submitted_at=datetime.now(timezone.utc),
            evaluated_at=datetime.now(timezone.utc),
        )

        session.add(attempt)
        session.commit()
        session.refresh(attempt)

        assert attempt.id is not None
        assert attempt.scenario_id == scenario.id
        assert attempt.score == 8
        assert attempt.percentage == 80.0

        stored = session.exec(
            select(ScenarioAttempt).where(
                ScenarioAttempt.id == attempt.id
            )
        ).one()

        assert stored.response_text == attempt.response_text
        assert stored.overall_result == "partially_correct"