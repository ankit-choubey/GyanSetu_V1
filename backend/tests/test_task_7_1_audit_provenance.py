from __future__ import annotations

import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.main import app
from app.models.audit import AuditEvent
from app.models.competency import Role
from app.models.user import User
from app.services.audit_service import AuditService
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
    user = db_session.execute(select(User).where(User.email == "admin_t71@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="admin_t71@mospi.gov.in",
            full_name="Admin T71",
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
    user = db_session.execute(select(User).where(User.email == "learner_t71@mospi.gov.in")).scalar_one_or_none()
    if not user:
        user = User(
            email="learner_t71@mospi.gov.in",
            full_name="Learner T71",
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


# 1. Event Logging & Retrieval
def test_01_log_and_retrieve_event(db_session: Session):
    evt = AuditService.log_event(
        db=db_session,
        action="TEST_ACTION",
        entity_type="TEST_ENTITY",
        actor_id=999,
        actor_role="ADMINISTRATOR",
        entity_id="ENT-001",
        result="SUCCESS",
        metadata={"detail": "unit_test_log"},
    )
    assert evt.id is not None
    assert evt.event_id.startswith("evt_")
    assert evt.action == "TEST_ACTION"

    retrieved = AuditService.get_event_by_id(db_session, evt.event_id)
    assert retrieved is not None
    assert retrieved.id == evt.id
    assert retrieved.get_metadata().get("detail") == "unit_test_log"


# 2. Filter by Action
def test_02_filter_by_action(db_session: Session):
    act = f"ACTION_{uuid.uuid4().hex[:6]}"
    AuditService.log_event(db=db_session, action=act, entity_type="ENTITY_A", result="SUCCESS")
    AuditService.log_event(db=db_session, action=act, entity_type="ENTITY_B", result="SUCCESS")

    events, total = AuditService.get_audit_events(db=db_session, action=act)
    assert total >= 2
    for e in events:
        assert e.action == act


# 3. Filter by Entity Type
def test_03_filter_by_entity_type(db_session: Session):
    etype = f"ETYPE_{uuid.uuid4().hex[:6]}"
    AuditService.log_event(db=db_session, action="CREATE", entity_type=etype, result="SUCCESS")

    events, total = AuditService.get_audit_events(db=db_session, entity_type=etype)
    assert total >= 1
    assert all(e.entity_type == etype for e in events)


# 4. Correlation ID Tracking
def test_04_correlation_id_tracking(db_session: Session):
    corr_id = f"corr_{uuid.uuid4().hex[:8]}"
    AuditService.log_event(db=db_session, action="STEP_1", entity_type="PROCESS", correlation_id=corr_id)
    AuditService.log_event(db=db_session, action="STEP_2", entity_type="PROCESS", correlation_id=corr_id)

    events, total = AuditService.get_audit_events(db=db_session, correlation_id=corr_id)
    assert total == 2
    actions = {e.action for e in events}
    assert actions == {"STEP_1", "STEP_2"}


# 5. Before & After State Capture
def test_05_before_after_state(db_session: Session):
    before = {"mastery": 0.45, "confidence": 0.60}
    after = {"mastery": 0.65, "confidence": 0.80}
    evt = AuditService.log_event(
        db=db_session,
        action="COMPETENCY_UPDATE",
        entity_type="COMPETENCY_STATE",
        before_state=before,
        after_state=after,
    )
    d = evt.to_dict()
    assert d["before_state"] == before
    assert d["after_state"] == after


# 6. Audit Summary Statistics
def test_06_audit_summary(db_session: Session):
    summary = AuditService.get_audit_summary(db_session)
    assert "total_events" in summary
    assert "success_rate" in summary
    assert summary["total_events"] > 0


# 7. Admin API Get Audit Logs (Authorized 200)
def test_07_admin_get_audit_logs(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/audit-logs", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "total_matches" in data


# 8. Learner Access to Audit Logs (Forbidden 403)
def test_08_learner_forbidden_audit_logs(client: TestClient, learner_user: User):
    resp = client.get("/api/admin/audit-logs", headers=auth_h(learner_user))
    assert resp.status_code == 403


# 9. Unauthenticated Access (Unauthorized 401)
def test_09_unauthenticated_forbidden_audit_logs(client: TestClient):
    resp = client.get("/api/admin/audit-logs")
    assert resp.status_code == 401


# 10. Admin API Audit Summary
def test_10_admin_get_audit_summary(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/audit-logs/summary", headers=auth_h(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "success_count" in data


# 11. Admin API Single Event by ID
def test_11_admin_get_single_event(client: TestClient, admin_user: User, db_session: Session):
    evt = AuditService.log_event(db=db_session, action="FETCH_TEST", entity_type="TEST")
    resp = client.get(f"/api/admin/audit-logs/{evt.event_id}", headers=auth_h(admin_user))
    assert resp.status_code == 200
    assert resp.json()["event_id"] == evt.event_id


# 12. Single Event 404
def test_12_single_event_not_found(client: TestClient, admin_user: User):
    resp = client.get("/api/admin/audit-logs/evt_nonexistent_99999", headers=auth_h(admin_user))
    assert resp.status_code == 404
