from __future__ import annotations

import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.audit import AuditEvent
from app.models.competency import Role
from app.models.user import User
from app.services.policy_service import PolicyService
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
    user = db_session.execute(select(User).where(User.email == "admin_t75@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t75@mospi.gov.in",
            full_name="Admin T75",
            role_id=admin_role.id if admin_role else 2,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def learner_a(db_session: Session):
    role = db_session.execute(
        select(Role).where(Role.name.not_in(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "learner_a_t75@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_a_t75@mospi.gov.in",
            full_name="Learner A T75",
            role_id=role.id if role else 1,
            is_active=True,
            password_hash="test_pwd_hash",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def learner_b(db_session: Session):
    role = db_session.execute(
        select(Role).where(Role.name.not_in(["Administrator", "admin"]))
    ).scalars().first()
    user = db_session.execute(select(User).where(User.email == "learner_b_t75@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_b_t75@mospi.gov.in",
            full_name="Learner B T75",
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


# 1. Learner isolation: Learner A only sees Learner A's timeline
def test_01_learner_timeline_isolation(client: TestClient, learner_a: User, learner_b: User):
    resp_a = client.get("/api/competency/timeline", headers=auth_h(learner_a))
    assert resp_a.status_code == 200
    assert resp_a.json()["user_id"] == learner_a.id
    assert resp_a.json()["user_id"] != learner_b.id

    resp_b = client.get("/api/competency/timeline", headers=auth_h(learner_b))
    assert resp_b.status_code == 200
    assert resp_b.json()["user_id"] == learner_b.id
    assert resp_b.json()["user_id"] != learner_a.id


# 2. Unauthenticated calls return 401/403
def test_02_rbac_unauthenticated_forbidden(client: TestClient):
    assert client.get("/api/admin/audit/events").status_code in [401, 403]
    assert client.get("/api/admin/policies").status_code in [401, 403]
    assert client.get("/api/competency/timeline").status_code in [401, 403]


# 3. Learner cannot access audit events (403)
def test_03_rbac_learner_cannot_access_audit_logs(client: TestClient, learner_a: User):
    resp = client.get("/api/admin/audit/events", headers=auth_h(learner_a))
    assert resp.status_code == 403


# 4. Learner cannot access data quality diagnostics (403)
def test_04_rbac_learner_cannot_access_data_quality(client: TestClient, learner_a: User):
    resp = client.get("/api/admin/data-quality/diagnostics", headers=auth_h(learner_a))
    assert resp.status_code == 403


# 5. Learner cannot access admin health subsystems (403)
def test_05_rbac_learner_cannot_access_subsystems_health(client: TestClient, learner_a: User):
    resp = client.get("/api/admin/health/subsystems", headers=auth_h(learner_a))
    assert resp.status_code == 403


# 6. Learner cannot read or update operational policies (403)
def test_06_rbac_learner_cannot_read_or_update_policies(client: TestClient, learner_a: User):
    resp_get = client.get("/api/admin/policies", headers=auth_h(learner_a))
    assert resp_get.status_code == 403

    resp_post = client.post(
        "/api/admin/policies/MIN_ITEM_RESPONSES_FOR_ANALYSIS",
        json={"value": 10, "reason": "Unauthorized update attempt"},
        headers=auth_h(learner_a),
    )
    assert resp_post.status_code == 403


# 7. Privacy: N < 5 suppression policy configuration verified
def test_07_privacy_n_less_than_5_suppression():
    policies = PolicyService.get_all_policies()
    assert "PRIVACY_SUPPRESSION_THRESHOLD" in policies
    assert policies["PRIVACY_SUPPRESSION_THRESHOLD"]["value"] == 5


# 8. Zero demographic fabrication: verify no demographic columns in User model schema
def test_08_zero_demographic_fabrication():
    # Verify User model attributes contains NO demographic fields (religion, caste, ethnicity, socio-economic)
    user_attrs = set(User.model_fields.keys() if hasattr(User, "model_fields") else User.__table__.columns.keys())
    forbidden_terms = {"religion", "caste", "ethnicity", "tribe", "income", "gender_guess", "synthetic_demographic"}
    for term in forbidden_terms:
        assert term not in user_attrs, f"Forbidden demographic field '{term}' found in User schema!"



# 9. Admin policy read
def test_09_policy_read_and_version_registry(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/policies", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "policies" in data
    assert float(data["policies"]["MIN_ITEM_RESPONSES_FOR_ANALYSIS"]["version"]) >= 1.0


# 10. Admin policy update and audit provenance
def test_10_policy_update_and_audit_provenance(client: TestClient, admin_user: User, db_session: Session):
    key = "RETENTION_WINDOW_DAYS"
    current_val = PolicyService.get_policy(key)["value"]
    new_val = 90 if current_val != 90 else 120

    resp = client.post(
        f"/api/admin/policies/{key}",
        json={"value": new_val, "reason": "Operational calibration for Q4 governance audit"},
        headers=auth_h(admin_user),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "UPDATED"
    assert resp.json()["updated_policy"]["value"] == new_val

    # Check AuditEvent recorded
    event = db_session.execute(
        select(AuditEvent)
        .where(AuditEvent.action == "POLICY_UPDATED", AuditEvent.entity_id == key)
        .order_by(AuditEvent.timestamp.desc())
    ).scalars().first()
    assert event is not None
    assert event.actor_id == admin_user.id
    assert event.get_after_state()["value"] == new_val


# 11. Policy update validation (invalid key / invalid value)
def test_11_policy_update_validation(client: TestClient, admin_user: User):
    resp_404 = client.post(
        "/api/admin/policies/NON_EXISTENT_POLICY_KEY",
        json={"value": 100, "reason": "Testing 404"},
        headers=auth_h(admin_user),
    )
    assert resp_404.status_code == 404

    resp_400 = client.post(
        "/api/admin/policies/RETENTION_WINDOW_DAYS",
        json={"value": -50, "reason": "Negative retention days should fail"},
        headers=auth_h(admin_user),
    )
    assert resp_400.status_code == 400


# 12. Public and Admin Operational Health Probes
def test_12_operational_health_probes(client: TestClient, admin_user: User):
    # Public health
    resp_public = client.get("/api/health")
    assert resp_public.status_code == 200
    assert resp_public.json()["status"] in ["HEALTHY", "DEGRADED"]

    # Admin health
    resp_admin = client.get("/api/admin/health/subsystems", headers=auth_h(admin_user))
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert "subsystems" in data
    assert "table_record_counts" in data
    assert "database" in data["subsystems"]
    assert "providers" in data["subsystems"]
