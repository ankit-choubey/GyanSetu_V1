from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.competency import Role
from app.models.user import User
from app.services.data_quality_service import DataQualityService
from app.utils.security import create_access_token


@pytest.fixture
def db_session():
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db_session: Session):
    admin_role = db_session.execute(
        select(Role).where(Role.name.in_(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "admin_t71b@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t71b@mospi.gov.in",
            full_name="Admin T71b",
            role_id=admin_role.id if admin_role else 2,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def learner_user(db_session: Session):
    role = db_session.execute(
        select(Role).where(Role.name.not_in(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "learner_t71b@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_t71b@mospi.gov.in",
            full_name="Learner T71b",
            role_id=role.id if role else 1,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


def auth_h(user: User) -> dict[str, str]:
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_session: Session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# 1. Full Data Quality Scan
def test_01_full_data_quality_audit(db_session: Session):
    res = DataQualityService.audit_data_quality(db_session)
    assert "overall_data_health_score" in res
    assert "status" in res
    assert "issues" in res
    assert res["status"] in {"HEALTHY", "ATTENTION_REQUIRED", "DEGRADED"}
    assert isinstance(res["issues"], list)


# 2. Taxonomy Integrity Audit
def test_02_taxonomy_integrity(db_session: Session):
    issues = DataQualityService.audit_taxonomy_integrity(db_session)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["category"] == "taxonomy"
        assert issue["severity"] in {"ERROR", "WARNING", "INFO"}
        assert "description" in issue


# 3. Evidence Integrity Audit
def test_03_evidence_integrity(db_session: Session):
    issues = DataQualityService.audit_evidence_integrity(db_session)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["category"] == "evidence"
        assert "remediation" in issue


# 4. Assessment Integrity Audit
def test_04_assessment_integrity(db_session: Session):
    issues = DataQualityService.audit_assessment_integrity(db_session)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["category"] == "assessment"


# 5. Intervention Integrity Audit
def test_05_intervention_integrity(db_session: Session):
    issues = DataQualityService.audit_intervention_integrity(db_session)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["category"] == "intervention"


# 6. Competency State Integrity Audit
def test_06_competency_state_integrity(db_session: Session):
    issues = DataQualityService.audit_competency_state_integrity(db_session)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["category"] == "competency_state"


# 7. Summary Scorecard
def test_07_summary_scorecard(db_session: Session):
    summary = DataQualityService.get_summary(db_session)
    assert "overall_data_health_score" in summary
    assert "category_breakdown" in summary
    assert "status" in summary


# 8. Category Diagnostic
def test_08_category_diagnostic(db_session: Session):
    res = DataQualityService.audit_category(db_session, category="taxonomy")
    assert res["category"] == "taxonomy"
    assert "issues_count" in res

    bad_res = DataQualityService.audit_category(db_session, category="non_existent")
    assert "error" in bad_res


# 9. Admin REST API Full Scan
def test_09_admin_api_data_quality(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/data-quality", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_data_health_score" in data
    assert "issues" in data


# 10. Admin REST API Summary
def test_10_admin_api_data_quality_summary(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/data-quality/summary", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "category_breakdown" in data


# 11. Admin REST API Category
def test_11_admin_api_data_quality_category(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/data-quality/evidence", headers=auth_h(admin_user))
    assert resp.status_code == 200
    assert resp.json()["category"] == "evidence"

    bad_resp = client.get("/api/admin/data-quality/invalid_cat", headers=auth_h(admin_user))
    assert bad_resp.status_code == 400


# 12. Learner Access Denied (403)
def test_12_learner_access_denied(client: TestClient, learner_user: User):
    resp = client.get("/api/admin/data-quality", headers=auth_h(learner_user))
    assert resp.status_code == 403
