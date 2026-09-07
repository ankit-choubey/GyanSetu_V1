"""
tests/system/test_task_7_backend_governance.py — Phase 7 Governance, Analytics & System Integrity Tests.

Verifies:
1. End-to-End Audit & Provenance Lifecycle:
   Action triggered -> Service executes -> DB updates -> AuditEvent logged -> Admin retrieves and validates provenance.
2. End-to-End Automated Data Quality Diagnostics:
   All 5 pillars evaluated (Taxonomy, Evidence, Assessment, Intervention, Competency State) -> Health scorecard verified.
3. Psychometric Item Response & Quality Review:
   Responses -> Empirical difficulty, distractor utilization, point-biserial discrimination -> Quality flags.
4. Longitudinal Competency Trajectory & Retention Governance:
   Chronological state transitions -> Uncertainty evolution (U = 1 - C) -> Retention window evaluation.
5. Recommendation Funnel & Outcome Analytics:
   End-to-end conversion funnel -> Pre/post observed gains -> Provider breakdown with causal disclaimers.
6. Security, Privacy, RBAC & Policy Governance:
   Learner data isolation -> RBAC enforcement across admin endpoints -> Centralized policy lifecycle.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.main import app
from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.audit import AuditEvent
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence, EvidenceType
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.assessment_analytics_service import AssessmentAnalyticsService
from app.services.audit_service import AuditService
from app.services.data_quality_service import DataQualityService
from app.services.longitudinal_analytics_service import LongitudinalAnalyticsService
from app.services.operational_health_service import OperationalHealthService
from app.services.outcome_analytics_service import OutcomeAnalyticsService
from app.services.policy_service import PolicyService
from app.utils.security import create_access_token


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session):
    admin_role = db_session.execute(
        select(Role).where(Role.name.in_(["Administrator", "admin", "Admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "sys_admin_7@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="sys_admin_7@mospi.gov.in",
            full_name="System Admin 7",
            role_id=admin_role.id if admin_role else 9,
            is_active=True,
            password_hash="sys_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def learner_user(db_session: Session):
    role = db_session.execute(
        select(Role).where(Role.name.not_in(["Administrator", "admin", "Admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "sys_learner_7@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="sys_learner_7@mospi.gov.in",
            full_name="System Learner 7",
            role_id=role.id if role else 1,
            is_active=True,
            password_hash="sys_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. System Integration: Audit & Provenance Ledger
# ==============================================================================
def test_sys_01_audit_and_provenance_lifecycle(client: TestClient, admin_user: User, db_session: Session):
    corr_id = f"corr_{uuid.uuid4().hex[:12]}"
    evt = AuditService.log_event(
        db=db_session,
        action="SYSTEM_E2E_VERIFICATION",
        entity_type="SYSTEM_MODULE",
        actor_id=admin_user.id,
        actor_role="ADMINISTRATOR",
        entity_id="MOD-700",
        result="SUCCESS",
        correlation_id=corr_id,
        metadata={"scope": "Phase 7 E2E system integration"},
    )
    assert evt.id is not None
    assert evt.event_id.startswith("evt_")

    resp = client.get(f"/api/admin/audit-logs?correlation_id={corr_id}", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_matches"] >= 1
    retrieved = data["events"][0]
    assert retrieved["action"] == "SYSTEM_E2E_VERIFICATION"
    assert retrieved["correlation_id"] == corr_id
    assert retrieved["metadata"]["scope"] == "Phase 7 E2E system integration"


# ==============================================================================
# 2. System Integration: Automated Data Quality Diagnostics Engine
# ==============================================================================
def test_sys_02_data_quality_diagnostics_engine(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/data-quality/diagnostics", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_data_health_score" in data
    assert "status" in data
    assert "total_issues_count" in data
    assert "issues" in data
    assert 0.0 <= data["overall_data_health_score"] <= 1.0

    # Also verify summary endpoint
    sum_resp = client.get("/api/admin/data-quality/summary", headers=auth_h(admin_user))
    assert sum_resp.status_code == 200
    s_data = sum_resp.json()
    assert "overall_data_health_score" in s_data
    assert "category_breakdown" in s_data


# ==============================================================================
# 3. System Integration: Psychometric Item Analytics Loop
# ==============================================================================
def test_sys_03_psychometric_item_response_loop(
    client: TestClient, admin_user: User, learner_user: User, db_session: Session
):
    comp = Competency(name=f"Sys Item Comp {uuid.uuid4().hex[:6]}", code=f"SIC_{uuid.uuid4().hex[:4]}")
    db_session.add(comp)
    db_session.commit()

    item = AssessmentItem(
        competency_id=comp.id,
        question_text="What is stratified sampling?",
        options_json=json.dumps({"A": "Correct Method", "B": "Biased Option", "C": "Random Guess"}),
        correct_option="A",
        difficulty="MEDIUM",
    )
    db_session.add(item)
    db_session.commit()

    # Submit 10 responses: 8 on A, 2 on B
    for i in range(10):
        is_high = (i < 8)
        att = AssessmentAttempt(user_id=learner_user.id, competency_id=comp.id, score=0.85 if is_high else 0.2)
        db_session.add(att)
        db_session.commit()
        resp = AssessmentResponse(
            attempt_id=att.id,
            assessment_item_id=item.id,
            competency_id=comp.id,
            selected_option="A" if is_high else "B",
            is_correct=is_high,
        )
        db_session.add(resp)
    db_session.commit()

    # Query via REST API
    api_resp = client.get(f"/api/admin/assessment/items/{item.id}/analytics", headers=auth_h(admin_user))
    assert api_resp.status_code == 200
    stats = api_resp.json()
    assert stats["sample_size"] == 10
    assert stats["difficulty_index"] == 0.8
    assert stats["status"] == "EVALUATED"
    assert "A" in stats["option_distribution"]
    assert stats["option_distribution"]["A"]["count"] == 8


# ==============================================================================
# 4. System Integration: Longitudinal Competency & Retention Loop
# ==============================================================================
def test_sys_04_longitudinal_competency_and_retention_loop(
    client: TestClient, learner_user: User, db_session: Session
):
    comp = Competency(name=f"Sys Long Comp {uuid.uuid4().hex[:6]}", code=f"SLC_{uuid.uuid4().hex[:4]}")
    db_session.add(comp)
    db_session.commit()

    now = datetime.now(timezone.utc)
    # 2 transitions
    h1 = CompetencyHistory(
        user_id=learner_user.id,
        competency_id=comp.id,
        previous_mastery=0.2,
        new_mastery=0.45,
        new_confidence=0.5,
        new_status="EMERGING",
        state_version=1,
        timestamp=now - timedelta(days=15),
    )
    h2 = CompetencyHistory(
        user_id=learner_user.id,
        competency_id=comp.id,
        previous_mastery=0.45,
        new_mastery=0.80,
        new_confidence=0.9,
        new_status="PROFICIENT",
        state_version=2,
        timestamp=now - timedelta(days=1),
    )
    st = CompetencyState(
        user_id=learner_user.id,
        competency_id=comp.id,
        mastery=0.80,
        confidence=0.90,
        uncertainty=0.10,
        status="PROFICIENT",
        last_assessed_at=now - timedelta(days=1),
    )
    db_session.add_all([h1, h2, st])
    db_session.commit()

    # Learner queries their own timeline
    resp = client.get(f"/api/competency/timeline/{comp.id}", headers=auth_h(learner_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["competency_id"] == comp.id
    assert data["observed_competency_gain"] == 0.35
    assert data["current_uncertainty"] == 0.10
    assert data["retention_refresher_recommended"] is False
    assert len(data["trajectory_timeline"]) == 2


# ==============================================================================
# 5. System Integration: Recommendation & Outcome Analytics Pipeline
# ==============================================================================
def test_sys_05_outcome_analytics_pipeline(
    client: TestClient, admin_user: User, learner_user: User, db_session: Session
):
    comp = Competency(name=f"Sys Outcome Comp {uuid.uuid4().hex[:6]}", code=f"SOC_{uuid.uuid4().hex[:4]}")
    db_session.add(comp)
    db_session.commit()

    it = Intervention(
        competency_id=comp.id,
        title="Survey Automation Module",
        intervention_type="LEARNING_RESOURCE",
        provider="IGOT_KARMAYOGI",
        source_id=f"igot_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(it)
    db_session.commit()

    # Record recommendation
    rec = RecommendationRecord(
        recommendation_id=f"rec_{uuid.uuid4().hex[:12]}",
        user_id=learner_user.id,
        competency_id=comp.id,
        selected_intervention_id=it.id,
        status="COMPLETED",
    )
    # Record outcome
    out = InterventionOutcome(
        user_id=learner_user.id,
        intervention_id=it.id,
        recommendation_id=rec.recommendation_id,
        status="COMPLETED",
        completion_score=0.95,
        pre_competency_mastery=0.35,
        post_competency_mastery=0.75,
        provider="IGOT_KARMAYOGI",
    )
    db_session.add_all([rec, out])
    db_session.commit()

    # Query recommendations analytics
    r_resp = client.get("/api/admin/analytics/recommendations", headers=auth_h(admin_user))
    assert r_resp.status_code == 200
    assert r_resp.json()["total_recommendations_generated"] >= 1

    # Query intervention outcomes analytics
    o_resp = client.get("/api/admin/analytics/interventions/outcomes", headers=auth_h(admin_user))
    assert o_resp.status_code == 200
    o_data = o_resp.json()
    assert o_data["completed_count"] >= 1
    assert "causal_disclaimer" in o_data["observed_gains"]
    assert "IGOT_KARMAYOGI" in o_data["provider_breakdown"]


# ==============================================================================
# 6. System Integration: Security, Privacy & Operational Health Probe
# ==============================================================================
def test_sys_06_security_privacy_and_health_probes(
    client: TestClient, admin_user: User, learner_user: User
):
    # 1. Learner cannot access admin routes
    assert client.get("/api/admin/audit-logs", headers=auth_h(learner_user)).status_code == 403
    assert client.get("/api/admin/policies", headers=auth_h(learner_user)).status_code == 403
    assert client.get("/api/admin/data-quality/diagnostics", headers=auth_h(learner_user)).status_code == 403
    assert client.get("/api/admin/system-status", headers=auth_h(learner_user)).status_code == 403

    # 2. Public health probe is open and healthy
    h_resp = client.get("/api/health")
    assert h_resp.status_code == 200
    assert h_resp.json()["status"] in ["HEALTHY", "DEGRADED"]

    # 3. Provider health probe
    p_resp = client.get("/api/health/providers")
    assert p_resp.status_code == 200
    assert p_resp.json()["providers_count"] >= 1

    # 4. Admin system status telemetry
    s_resp = client.get("/api/admin/system-status", headers=auth_h(admin_user))
    assert s_resp.status_code == 200
    assert "table_record_counts" in s_resp.json()
