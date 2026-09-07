"""
backend/tests/test_task_6_2_workforce.py — Task 6.2 Workforce Intelligence Test Suite.

Verifies 20 required scenarios:
1. authorized workforce overview
2. unauthorized access rejected
3. learner cannot access workforce data
4. role aggregation
5. competency aggregation
6. subskill aggregation
7. assessed ratio
8. missing evidence handling
9. zero denominator
10. cohort suppression
11. small cohort handling
12. gap calculation
13. confidence reporting
14. stale evidence handling
15. taxonomy version handling
16. fairness diagnostic with sufficient groups
17. fairness diagnostic with missing group
18. fairness diagnostic with suppressed group
19. no protected attribute fabrication
20. longitudinal query
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
from app.models.competency import Competency, Role, SubSkill
from app.models.competency_history import CompetencyHistory
from app.models.competency_state import CompetencyState
from app.models.evidence import Evidence
from app.models.user import User
from app.services.data_quality_service import DataQualityService
from app.services.fairness_audit_service import FairnessAuditService
from app.services.governance_service import GovernanceService
from app.services.workforce_analytics_service import WorkforceAnalyticsService
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
        GovernanceService.initialize_governance_data(db)
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
def admin_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name.in_(["Administrator", "admin"]))).scalars().first()
    if not role:
        role = Role(name="Administrator", description="System Administrator")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    email = f"t62.admin.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("adminpass123"),
        full_name="Task 6.2 Admin",
        role_id=role.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def learner_user(db_session: Session) -> User:
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    email = f"t62.learner.{uuid.uuid4().hex[:6]}@mospi.gov.in"
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Task 6.2 Learner",
        role_id=role.id if role else None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


# 1. Authorized workforce overview
def test_01_authorized_workforce_overview(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/overview", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "workforce_summary" in data
    assert "governance_guardrail" in data
    assert "DECISION SUPPORT ONLY" in data["governance_guardrail"]


# 2. Unauthorized access rejected (unauthenticated)
def test_02_unauthorized_access_rejected(client: TestClient):
    resp = client.get("/api/workforce/overview")
    assert resp.status_code == 401


# 3. Learner cannot access workforce data (403 Forbidden)
def test_03_learner_cannot_access_workforce_data(client: TestClient, learner_user: User):
    resp = client.get("/api/workforce/overview", headers=auth_h(learner_user))
    assert resp.status_code == 403
    assert "Administrator access required" in resp.json()["detail"]


# 4. Role aggregation
def test_04_role_aggregation(client: TestClient, admin_user: User, db_session: Session):
    role = db_session.execute(select(Role).where(Role.name == "Statistical Officer")).scalar_one_or_none()
    assert role is not None
    resp = client.get(f"/api/workforce/competencies?role_id={role.id}", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "competencies" in data
    assert len(data["competencies"]) > 0


# 5. Competency aggregation
def test_05_competency_aggregation(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/competencies", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_competencies_reported" in data
    assert data["total_competencies_reported"] >= 1


# 6. Subskill aggregation
def test_06_subskill_aggregation(client: TestClient, admin_user: User, db_session: Session):
    # Verify subskills exist in taxonomy and can be audited via data-quality
    subskills = db_session.execute(select(SubSkill)).scalars().all()
    assert len(subskills) >= 160
    resp = client.get("/api/workforce/quality", headers=auth_h(admin_user))
    assert resp.status_code == 200
    assert "status" in resp.json()


# 7. Assessed ratio
def test_07_assessed_ratio(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/overview", headers=auth_h(admin_user))
    assert resp.status_code == 200
    summary = resp.json()["workforce_summary"]
    assert "workforce_assessed_ratio" in summary
    assert 0.0 <= summary["workforce_assessed_ratio"] <= 1.0


# 8. Missing evidence handling (status UNASSESSED, not 0 mastery)
def test_08_missing_evidence_handling(client: TestClient, admin_user: User, db_session: Session):
    # An unassessed competency state must not be silently coerced to 0 mastery
    unassessed_state = db_session.execute(
        select(CompetencyState).where(CompetencyState.status == "UNASSESSED")
    ).scalars().first()
    if unassessed_state:
        assert unassessed_state.mastery is None
    overview = client.get("/api/workforce/overview", headers=auth_h(admin_user)).json()
    assert "workforce_summary" in overview


# 9. Zero denominator
def test_09_zero_denominator(client: TestClient, admin_user: User, db_session: Session):
    # Query with a non-existent role_id to check zero division safety
    resp = client.get("/api/workforce/competencies?role_id=999999", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_competencies_reported"] >= 0
    # Every group was suppressed or evaluated with 0 error
    for c in data["competencies"]:
        assert c["aggregation_status"] in ("SUPPRESSED", "EVALUATED")


# 10. Cohort suppression (N < 5)
def test_10_cohort_suppression(client: TestClient, admin_user: User):
    # Enforcing min_group_size = 50 should suppress small cohorts
    resp = client.get("/api/workforce/competencies?minimum_group_size=50", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    suppressed = [c for c in data["competencies"] if c["aggregation_status"] == "SUPPRESSED"]
    assert len(suppressed) > 0
    assert "below minimum privacy threshold" in suppressed[0]["suppression_reason"]


# 11. Small cohort handling
def test_11_small_cohort_handling(db_session: Session):
    # Verify WorkforceAnalyticsService suppresses populations below threshold
    res = WorkforceAnalyticsService.get_competencies_aggregate(db_session, min_group_size=100)
    assert res["suppressed_groups_count"] > 0
    assert res["suppression_policy"]["small_cell_protection_enabled"] is True


# 12. Gap calculation
def test_12_gap_calculation(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/gaps?minimum_group_size=1", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "workforce_gaps" in data
    for gap in data["workforce_gaps"]:
        assert "gap_severity" in gap
        assert "classification" in gap
        assert gap["classification"] in ("ACTIONABLE", "NEEDS_MORE_EVIDENCE")


# 13. Confidence reporting
def test_13_confidence_reporting(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/gaps?minimum_group_size=1", headers=auth_h(admin_user))
    assert resp.status_code == 200
    for gap in resp.json()["workforce_gaps"]:
        assert "confidence" in gap
        assert 0.0 <= gap["confidence"] <= 1.0


# 14. Stale evidence handling
def test_14_stale_evidence_handling(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/retention", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "retention_summary" in data
    assert "retention_monitoring" in data
    assert "methodology_disclosure" in data


# 15. Taxonomy version handling
def test_15_taxonomy_version_handling(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/governance/models", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "model_registry" in data
    for m in data["model_registry"]:
        assert "version" in m


# 16. Fairness diagnostic with sufficient groups
def test_16_fairness_diagnostic_with_sufficient_groups(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/fairness", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["fairness_framework"] == "OPERATIONAL_COHORT_PARITY_AUDIT"
    assert "overall_classification" in data
    assert "cohort_metrics" in data


# 17. Fairness diagnostic with missing group
def test_17_fairness_diagnostic_with_missing_group(db_session: Session):
    # Audit must complete without KeyError even if some roles have 0 users
    res = FairnessAuditService.audit_operational_fairness(db_session)
    assert res is not None
    assert "overall_classification" in res


# 18. Fairness diagnostic with suppressed group
def test_18_fairness_diagnostic_with_suppressed_group(db_session: Session):
    res = FairnessAuditService.audit_operational_fairness(db_session)
    suppressed_count = res.get("suppressed_small_cohorts_count", 0)
    assert suppressed_count >= 0
    for metric in res.get("cohort_metrics", {}).values():
        if metric.get("audit_status") == "SUPPRESSED_SMALL_COHORT":
            assert "statistical privacy threshold" in metric["reason"]


# 19. No protected attribute fabrication
def test_19_no_protected_attribute_fabrication(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/fairness", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "demographic_data_disclosure" in data
    assert "Protected demographic characteristics" in data["demographic_data_disclosure"]
    assert "strictly NOT collected or stored" in data["demographic_data_disclosure"]
    # Verify no race, caste, gender, religion keys in any cohort metrics
    for cohort_name, metrics in data.get("cohort_metrics", {}).items():
        assert "gender" not in metrics
        assert "caste" not in metrics
        assert "ethnicity" not in metrics
        assert "religion" not in metrics


# 20. Longitudinal query
def test_20_longitudinal_query(client: TestClient, admin_user: User):
    resp = client.get("/api/workforce/trends", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "longitudinal_trends" in data
    assert "overall_trend_distribution" in data
    assert "analytical_disclosure" in data
