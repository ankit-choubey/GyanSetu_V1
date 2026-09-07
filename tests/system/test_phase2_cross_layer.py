import json
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.dependencies import get_current_user, get_db
from app.main import app
from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.misconception import Misconception
from app.models.user import User


@pytest.fixture
def system_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    # 1. Profile: Role and Learner
    role = Role(name="Senior Statistical Officer")
    session.add(role)
    session.flush()

    learner = User(
        id=501,
        email="sso_learner@mospi.gov.in",
        full_name="Senior Officer Ankit",
        password_hash="secure_hash",
        role_id=role.id,
    )
    session.add(learner)
    session.flush()

    # 2. Role Requirements: Competencies & Subskills
    comp1 = Competency(id=21, role_id=role.id, name="Index Numbers Compilation")
    comp2 = Competency(id=22, role_id=role.id, name="National Accounts Statistics")
    session.add_all([comp1, comp2])
    session.flush()

    session.add_all([
        RoleCompetency(role_id=role.id, competency_id=comp1.id),
        RoleCompetency(role_id=role.id, competency_id=comp2.id),
    ])

    sub1 = SubSkill(id=201, competency_id=comp1.id, name="Laspeyres vs Paasche Formulas")
    sub2 = SubSkill(id=202, competency_id=comp1.id, name="Base Year Revision")
    session.add_all([sub1, sub2])
    session.flush()

    # 3. Validated Item Bank
    items = [
        AssessmentItem(
            id=201,
            competency_id=comp1.id,
            subskill_id=sub1.id,
            question_text="Which formula uses base period quantities as weights?",
            options_json=json.dumps(["A. Laspeyres", "B. Paasche", "C. Fisher", "D. Marshall-Edgeworth"]),
            correct_option="A",
            difficulty="easy",
            source_reference="NSSTA/CPI-01",
        ),
        AssessmentItem(
            id=202,
            competency_id=comp1.id,
            subskill_id=sub1.id,
            question_text="Why does the Laspeyres index exhibit an upward bias?",
            options_json=json.dumps(["A. Substitution effect ignored", "B. Quality change overstated", "C. Negative weights", "D. Zero inflation"]),
            correct_option="A",
            difficulty="medium",
            source_reference="NSSTA/CPI-02",
        ),
        AssessmentItem(
            id=203,
            competency_id=comp1.id,
            subskill_id=sub2.id,
            question_text="Recommended interval for CPI base year revisions under UNSD standards?",
            options_json=json.dumps(["A. Every 5 to 10 years", "B. Every 50 years", "C. Never", "D. Annually"]),
            correct_option="A",
            difficulty="medium",
            source_reference="NSSTA/CPI-03",
        ),
    ]
    session.add_all(items)
    session.commit()

    yield session, learner, comp1, comp2

    session.close()
    engine.dispose()


def test_cross_layer_diagnostic_to_dashboard_loop(system_env):
    session, learner, comp1, comp2 = system_env

    app.dependency_overrides[get_current_user] = lambda: learner
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    try:
        # Step A: Inspect Dashboard before any evidence
        dash_init = client.get("/api/dashboard/learner")
        assert dash_init.status_code == 200
        dash_data = dash_init.json()
        assert dash_data["user_id"] == learner.id
        assert dash_data["total_competencies"] == 2
        for comp_summary in dash_data["competencies"]:
            assert comp_summary["status"] == "UNASSESSED"
            assert comp_summary["mastery"] is None
            assert comp_summary["confidence"] == 0.0

        # Step B: Start Adaptive Diagnostic for Competency 1
        start_res = client.post("/api/diagnostic/start", json={"competency_id": comp1.id, "max_questions": 2})
        assert start_res.status_code == 200
        session_info = start_res.json()
        session_id = session_info["session_id"]
        q1 = session_info["first_question"]
        assert q1 is not None
        assert q1["question_id"] == 201

        # Step C: Answer Q1 correctly
        ans1 = client.post(
            "/api/diagnostic/respond",
            json={"session_id": session_id, "assessment_item_id": 201, "selected_option": "A"},
        )
        assert ans1.status_code == 200
        ans1_data = ans1.json()
        assert ans1_data["is_correct"] is True
        assert ans1_data["updated_mastery"] == 1.0

        # Verify Evidence recorded in database
        ev_records = session.execute(
            select(Evidence).where(
                Evidence.user_id == learner.id,
                Evidence.competency_id == comp1.id,
            )
        ).scalars().all()
        assert len(ev_records) == 1
        assert ev_records[0].source == "ADAPTIVE_DIAGNOSTIC"
        assert ev_records[0].provenance == "[LIVE INTEGRATION]"
        assert ev_records[0].score == 1.0

        # Verify CompetencyHistory logged transition
        hist_records = session.execute(
            select(CompetencyHistory).where(
                CompetencyHistory.user_id == learner.id,
                CompetencyHistory.competency_id == comp1.id,
            ).order_by(CompetencyHistory.state_version)
        ).scalars().all()
        assert len(hist_records) == 1
        assert hist_records[0].new_mastery == 1.0
        assert hist_records[0].triggering_evidence_id == ev_records[0].id

        # Step D: Answer Q2 (final question for session)
        q2 = ans1_data["next_question"]
        assert q2 is not None
        ans2 = client.post(
            "/api/diagnostic/respond",
            json={"session_id": session_id, "assessment_item_id": q2["question_id"], "selected_option": "A"},
        )
        assert ans2.status_code == 200
        ans2_data = ans2.json()
        assert ans2_data["is_complete"] is True
        assert ans2_data["stop_reason"] == "MAX_QUESTIONS_REACHED"

        # Step E: Verify Evidence Ledger API reflects both items
        ev_api = client.get(f"/api/evidence?competency_id={comp1.id}")
        assert ev_api.status_code == 200
        assert ev_api.json()["total_records"] == 2

        # Step F: Verify Competency History API reflects state progression
        hist_api = client.get(f"/api/competency/history/{comp1.id}")
        assert hist_api.status_code == 200
        assert len(hist_api.json()) == 2

        # Step G: Verify Dashboard reflects updated mastery and confidence
        dash_final = client.get("/api/dashboard/learner")
        assert dash_final.status_code == 200
        final_comps = {c["competency_id"]: c for c in dash_final.json()["competencies"]}
        assert final_comps[comp1.id]["status"] == "ASSESSED"
        assert final_comps[comp1.id]["mastery"] == 1.0
        assert final_comps[comp1.id]["confidence"] > 0.0
        assert final_comps[comp1.id]["evidence_count"] == 2

        # Unassessed competency remains unassessed
        assert final_comps[comp2.id]["status"] == "UNASSESSED"
        assert final_comps[comp2.id]["mastery"] is None

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
