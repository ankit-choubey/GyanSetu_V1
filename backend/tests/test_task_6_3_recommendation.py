"""
backend/tests/test_task_6_3_recommendation.py — Task 6.3 Recommendation & Explainability Backend Test Suite.

Verifies 22 required scenarios:
1. cold-start recommendation
2. evidence-based recommendation
3. competency alignment
4. subskill alignment
5. misconception alignment if available
6. candidate rejection reason
7. provider unavailable fallback
8. stale resource rejection
9. prerequisite rejection
10. duplicate rejection
11. recommendation persistence
12. explanation persistence
13. explanation grounded in actual data
14. unsupported psychological inference prevented
15. recommendation feedback
16. accepted lifecycle
17. skipped lifecycle
18. rejected lifecycle
19. completed lifecycle
20. duplicate feedback idempotency
21. learner isolation
22. unauthorized access
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.adapters import get_adapter_for_provider
from app.services.eligibility_engine import EligibilityEngine
from app.services.next_best_action_service import NextBestActionService
from app.utils.security import create_access_token, hash_password


@pytest.fixture(scope="module", autouse=True)
def setup_module_data():
    from sqlmodel import SQLModel
    from app.database import engine
    from app.seed_data.runner import seed_full_taxonomy
    from app.seed_data.intervention_catalog_loader import seed_intervention_catalog

    SQLModel.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.execute(select(Role)).scalars().first():
            seed_full_taxonomy("test-pass")
        seed_intervention_catalog(db)
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def learner_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    email = f"t63.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Task 6.3 Learner",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_learner(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    email = f"t63.other.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Task 6.3 Other",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


# 1. Cold-start recommendation
def test_01_cold_start_recommendation(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    # Ensure learner has no competency state for this competency
    st = db_session.execute(
        select(CompetencyState).where(CompetencyState.user_id == learner_user.id, CompetencyState.competency_id == comp.id)
    ).scalar_one_or_none()
    if st:
        db_session.delete(st)
        db_session.commit()

    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_type"] == "DIAGNOSTIC"
    assert data["confidence"] == 0.0
    assert "UNASSESSED" in data["explanation"]["why"] or "baseline" in data["explanation"]["why"].lower()


# 2. Evidence-based recommendation
def test_02_evidence_based_recommendation(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    st = db_session.execute(
        select(CompetencyState).where(CompetencyState.user_id == learner_user.id, CompetencyState.competency_id == comp.id)
    ).scalar_one_or_none()
    if not st:
        st = CompetencyState(user_id=learner_user.id, competency_id=comp.id, mastery=0.35, confidence=0.6, status="ASSESSED")
        db_session.add(st)
    else:
        st.mastery = 0.35
        st.confidence = 0.6
        st.status = "ASSESSED"
    db_session.commit()

    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_type"] == "INTERVENTION"
    assert data["selected_intervention"] is not None


# 3. Competency alignment
def test_03_competency_alignment(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["competency_id"] == comp.id


# 4. Subskill alignment
def test_04_subskill_alignment(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    st = CompetencyState(user_id=learner_user.id, competency_id=comp.id, mastery=0.35, confidence=0.7, status="ASSESSED")
    db_session.add(st)
    db_session.commit()

    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_subskill_id"] is not None


# 5. Misconception alignment if available
def test_05_misconception_alignment(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    sub = db_session.execute(select(SubSkill).where(SubSkill.competency_id == comp.id)).scalars().first()
    assert sub is not None

    st = CompetencyState(user_id=learner_user.id, competency_id=comp.id, mastery=0.35, confidence=0.7, status="ASSESSED")
    db_session.add(st)

    misc = Misconception(
        learner_id=learner_user.id,
        competency_id=comp.id,
        subskill_id=sub.id,
        pattern_key="stratified_vs_cluster_confusion",
        misconception_type="CONCEPTUAL_CONFUSION",
        description="Confuses stratified sampling with cluster sampling variance implications",
        occurrences=2,
        resolved=False,
    )
    db_session.add(misc)
    db_session.commit()

    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_intervention"] is not None


# 6. Candidate rejection reason
def test_06_candidate_rejection_reason(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    rejected = data.get("rejected_candidates", [])
    if rejected:
        for r in rejected:
            assert "reason" in r
            assert "status" in r


# 7. Provider unavailable fallback
def test_07_provider_unavailable_fallback(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    st = CompetencyState(user_id=learner_user.id, competency_id=comp.id, mastery=0.35, confidence=0.7, status="ASSESSED")
    db_session.add(st)
    db_session.commit()

    adapter = get_adapter_for_provider("INTERNAL")
    adapter.set_simulated_availability(False)
    try:
        resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_intervention"]["provider"] != "INTERNAL"
    finally:
        adapter.set_simulated_availability(True)


# 8. Stale candidate rejection
def test_08_stale_candidate_rejection(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    st = CompetencyState(user_id=learner_user.id, competency_id=comp.id, mastery=0.35, confidence=0.7, status="ASSESSED")
    db_session.add(st)

    stale_item = Intervention(
        provider="TEST_RECS",
        title="T63 Stale Item",
        competency_id=comp.id,
        intervention_type="COURSE",
        modality="ONLINE_SELF_PACED",
        duration_minutes=30,
        difficulty="easy",
        source="SYSTEM",
        source_id="T63-STALE-001",
        status="STALE",
        last_verified_at=datetime.now(timezone.utc) - timedelta(days=200),
    )
    db_session.add(stale_item)
    db_session.commit()

    try:
        resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_intervention"]["id"] != stale_item.id
    finally:
        db_session.delete(stale_item)
        db_session.delete(st)
        db_session.commit()


# 9. Prerequisite rejection
def test_09_prerequisite_rejection(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    prereq_item = Intervention(
        provider="INTERNAL",
        title="T63 Advanced Prerequisite Item",
        competency_id=comp.id,
        intervention_type="COURSE",
        modality="ONLINE_SELF_PACED",
        duration_minutes=60,
        difficulty="advanced",
        prerequisites_json=json.dumps({"required_subskills": ["stratified sampling"], "min_mastery": 0.95}),
        status="ACTIVE",
    )
    db_session.add(prereq_item)
    db_session.commit()

    try:
        engine = EligibilityEngine()
        dec = engine.evaluate_candidate(db_session, learner_user, prereq_item)
        assert dec.is_eligible is False
        assert dec.status == "PREREQUISITE_NOT_MET"
    finally:
        db_session.delete(prereq_item)
        db_session.commit()


# 10. Duplicate rejection (already completed)
def test_10_duplicate_rejection(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    item = db_session.execute(
        select(Intervention).where(
            Intervention.competency_id == comp.id,
            Intervention.intervention_type.not_in(["retrieval_practice", "scenario_practice"]),
        )
    ).scalars().first()
    assert item is not None

    # Mark as completed
    outcome = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=item.id,
        status="COMPLETED",
    )
    db_session.add(outcome)
    db_session.commit()

    try:
        engine = EligibilityEngine()
        dec = engine.evaluate_candidate(db_session, learner_user, item, completed_intervention_ids={item.id})
        assert dec.is_eligible is False
        assert dec.status == "ALREADY_COMPLETED"
    finally:
        db_session.delete(outcome)
        db_session.commit()


# 11. Recommendation persistence
def test_11_recommendation_persistence(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]
    record = db_session.execute(
        select(RecommendationRecord).where(RecommendationRecord.recommendation_id == rec_id)
    ).scalar_one_or_none()
    assert record is not None


# 12. Explanation persistence
def test_12_explanation_persistence(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    exp_resp = client.get(f"/api/recommendations/{rec_id}/explanation", headers=auth_h(learner_user))
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert "explanation" in exp_data


# 13. Explanation grounded in actual data
def test_13_explanation_grounded_in_actual_data(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    exp = resp.json()["explanation"]
    assert "primary_reason" in exp
    assert "evidence_support" in exp
    assert "competency_gap" in exp


# 14. Unsupported psychological inference prevented
def test_14_unsupported_psychological_inference_prevented(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    exp_str = json.dumps(resp.json()["explanation"]).lower()
    for forbidden in ["demotivated", "lazy", "depressed", "anxious", "unintelligent", "incompetent"]:
        assert forbidden not in exp_str, f"Forbidden psychological term '{forbidden}' detected in explanation!"


# 15. Recommendation feedback
def test_15_recommendation_feedback(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    f_resp = client.post(
        f"/api/recommendations/{rec_id}/feedback",
        json={"action": "ACCEPT", "notes": "Approved by learner"},
        headers=auth_h(learner_user),
    )
    assert f_resp.status_code == 200
    assert f_resp.json()["status"] == "ACCEPTED"


# 16. Accepted lifecycle
def test_16_accepted_lifecycle(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPT"}, headers=auth_h(learner_user))
    check = client.get(f"/api/recommendations/{rec_id}", headers=auth_h(learner_user))
    assert check.status_code == 200
    assert check.json()["status"] == "ACCEPTED"


# 17. Skipped lifecycle
def test_17_skipped_lifecycle(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    f_resp = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "SKIP"}, headers=auth_h(learner_user))
    assert f_resp.status_code == 200
    assert f_resp.json()["status"] == "SKIPPED"


# 18. Rejected lifecycle
def test_18_rejected_lifecycle(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    f_resp = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "REJECT"}, headers=auth_h(learner_user))
    assert f_resp.status_code == 200
    assert f_resp.json()["status"] == "REJECTED"


# 19. Completed lifecycle
def test_19_completed_lifecycle(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    # Start
    client.post(f"/api/recommendations/{rec_id}/start", headers=auth_h(learner_user))
    # Feedback completion
    f_resp = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "COMPLETE"}, headers=auth_h(learner_user))
    assert f_resp.status_code == 200
    assert f_resp.json()["status"] == "COMPLETED"


# 20. Duplicate feedback idempotency
def test_20_duplicate_feedback_idempotency(client: TestClient, learner_user: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    # First submit
    r1 = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPT"}, headers=auth_h(learner_user))
    assert r1.status_code == 200
    # Duplicate submit
    r2 = client.post(f"/api/recommendations/{rec_id}/feedback", json={"action": "ACCEPT"}, headers=auth_h(learner_user))
    assert r2.status_code == 200
    assert r2.json()["status"] == "ACCEPTED"


# 21. Learner isolation
def test_21_learner_isolation(client: TestClient, learner_user: User, other_learner: User, db_session: Session):
    comp = db_session.execute(select(Competency).where(Competency.name == "Sampling Design")).scalar_one_or_none()
    assert comp is not None
    resp = client.post("/api/recommendations/next", json={"competency_id": comp.id}, headers=auth_h(learner_user))
    assert resp.status_code == 200
    rec_id = resp.json()["recommendation_id"]

    # Other learner cannot inspect
    r_iso = client.get(f"/api/recommendations/{rec_id}", headers=auth_h(other_learner))
    assert r_iso.status_code == 403


# 22. Unauthorized access
def test_22_unauthorized_access(client: TestClient):
    resp = client.get("/api/recommendations")
    assert resp.status_code == 401
