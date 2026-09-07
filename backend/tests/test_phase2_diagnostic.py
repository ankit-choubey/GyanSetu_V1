import json
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.dependencies import get_current_user, get_db
from app.main import app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.user import User


@pytest.fixture
def diag_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    role = Role(name="Field Investigator")
    session.add(role)
    session.flush()

    user = User(id=201, email="diag_learner@example.com", full_name="Diag Learner", password_hash="hash", role_id=role.id)
    session.add(user)
    session.flush()

    comp = Competency(id=10, role_id=role.id, name="Field Enumeration Techniques")
    session.add(comp)
    session.flush()

    session.add(RoleCompetency(role_id=role.id, competency_id=comp.id))

    sub1 = SubSkill(id=101, competency_id=comp.id, name="Household Listing")
    sub2 = SubSkill(id=102, competency_id=comp.id, name="Non-response Handling")
    session.add_all([sub1, sub2])
    session.flush()

    # Seed assessment items across difficulties
    items = [
        AssessmentItem(
            id=1,
            competency_id=comp.id,
            subskill_id=sub1.id,
            question_text="What is the primary objective of household listing?",
            options_json=json.dumps(["A. Frame creation", "B. Taxation", "C. Voter id", "D. Police check"]),
            correct_option="A",
            difficulty="easy",
            source_reference="NSSTA/HL-01",
        ),
        AssessmentItem(
            id=2,
            competency_id=comp.id,
            subskill_id=sub1.id,
            question_text="How are multi-family households enumerated?",
            options_json=json.dumps(["A. Separate listing lines", "B. Ignore secondary", "C. Single combined entry", "D. Skip house"]),
            correct_option="A",
            difficulty="medium",
            source_reference="NSSTA/HL-02",
        ),
        AssessmentItem(
            id=3,
            competency_id=comp.id,
            subskill_id=sub1.id,
            question_text="Advanced boundary arbitration for split enumeration blocks?",
            options_json=json.dumps(["A. Consult supervisor map", "B. Guess", "C. Drop block", "D. Double count"]),
            correct_option="A",
            difficulty="hard",
            source_reference="NSSTA/HL-03",
        ),
        AssessmentItem(
            id=4,
            competency_id=comp.id,
            subskill_id=sub2.id,
            question_text="First step when respondent is temporarily absent?",
            options_json=json.dumps(["A. Revisit schedule", "B. Immediate replacement", "C. Record deceased", "D. Arbitrary entry"]),
            correct_option="A",
            difficulty="easy",
            source_reference="NSSTA/NR-01",
        ),
        AssessmentItem(
            id=5,
            competency_id=comp.id,
            subskill_id=sub2.id,
            question_text="Imputation procedure for item non-response?",
            options_json=json.dumps(["A. Hot deck donor", "B. Random zero", "C. Mean of all rows", "D. Ignore"]),
            correct_option="A",
            difficulty="medium",
            source_reference="NSSTA/NR-02",
        ),
    ]
    session.add_all(items)
    session.commit()

    yield session, user, comp, [sub1, sub2]

    session.close()
    engine.dispose()


def test_diagnostic_flow_end_to_end(diag_env):
    session, user, comp, _ = diag_env

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    try:
        # 1. Start diagnostic session
        start_resp = client.post("/api/diagnostic/start", json={"competency_id": comp.id, "max_questions": 3})
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        session_id = start_data["session_id"]
        assert start_data["status"] == "IN_PROGRESS"
        assert start_data["baseline_mastery"] is None  # Initially unassessed
        assert start_data["baseline_confidence"] == 0.0
        assert start_data["baseline_uncertainty"] == 1.0
        assert start_data["first_question"] is not None

        q1 = start_data["first_question"]
        q1_id = q1["question_id"]
        assert q1["difficulty"] == "easy"
        assert "Selected because" in q1["selection_rationale"]

        # 2. Submit correct answer to q1 -> difficulty should step up
        ans1_resp = client.post(
            "/api/diagnostic/respond",
            json={"session_id": session_id, "assessment_item_id": q1_id, "selected_option": "A"},
        )
        assert ans1_resp.status_code == 200
        ans1_data = ans1_resp.json()
        assert ans1_data["is_correct"] is True
        assert ans1_data["score"] == 1.0
        assert ans1_data["updated_mastery"] == 1.0
        assert ans1_data["updated_confidence"] > 0.0
        assert ans1_data["updated_uncertainty"] < 1.0
        assert ans1_data["is_complete"] is False
        assert ans1_data["next_question"] is not None

        # Next question difficulty stepped up
        q2 = ans1_data["next_question"]
        q2_id = q2["question_id"]
        assert q2_id != q1_id  # Anti-repetition guard
        assert q2["difficulty"] == "medium"

        # 3. Submit wrong answer to q2 -> tests misconception tracking & remediation
        ans2_resp = client.post(
            "/api/diagnostic/respond",
            json={"session_id": session_id, "assessment_item_id": q2_id, "selected_option": "B"},
        )
        assert ans2_resp.status_code == 200
        ans2_data = ans2_resp.json()
        assert ans2_data["is_correct"] is False
        assert ans2_data["score"] == 0.0
        assert ans2_data["misconception_flagged"] is True

        q3 = ans2_data["next_question"]
        assert q3 is not None
        assert q3["question_id"] not in (q1_id, q2_id)

        # 4. Submit answer to q3 (reaches max_questions = 3 -> session completes)
        ans3_resp = client.post(
            "/api/diagnostic/respond",
            json={"session_id": session_id, "assessment_item_id": q3["question_id"], "selected_option": "A"},
        )
        assert ans3_resp.status_code == 200
        ans3_data = ans3_resp.json()
        assert ans3_data["is_complete"] is True
        assert ans3_data["stop_reason"] == "MAX_QUESTIONS_REACHED"

        # 5. Check session status endpoint
        status_resp = client.get(f"/api/diagnostic/{session_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "COMPLETED"
        assert status_data["questions_asked"] == 3
        assert status_data["stop_reason"] == "MAX_QUESTIONS_REACHED"
        assert status_data["current_mastery"] is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
