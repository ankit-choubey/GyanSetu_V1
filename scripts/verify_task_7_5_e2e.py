"""
scripts/verify_task_7_5_e2e.py — Phase 7.5 Security, Privacy, Policies & Health Runtime E2E Verifier.

Verifies:
1. Learner data isolation across personal timeline endpoints.
2. RBAC barriers on all administrative surfaces.
3. Privacy suppression policy configuration (N < 5).
4. Zero demographic fabrication guarantee.
5. Centralized operational policy registry read & versioned updates.
6. Audit event generation on policy modification.
7. Public & Administrative operational health probes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.audit import AuditEvent
from app.models.competency import Role
from app.models.user import User
from app.services.policy_service import PolicyService
from app.utils.security import create_access_token


def print_step(num: int, title: str) -> None:
    print(f"\n{'='*75}\n STEP {num}: {title.upper()}\n{'='*75}")


def main() -> None:
    print("\n" + "=" * 75)
    print(" GYANSETU V1 — TASK 7.5 SECURITY, POLICIES & HEALTH E2E VERIFICATION")
    print("=" * 75)

    db = SessionLocal()
    client = TestClient(app)

    try:
        admin_role = db.execute(select(Role).where(Role.name.in_(["Administrator", "admin", "Admin"]))).scalars().first()
        admin = db.execute(select(User).where(User.email == "admin_v75@mospi.gov.in")).scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin_v75@mospi.gov.in",
                full_name="Admin V75",
                role_id=admin_role.id if admin_role else 9,
                is_active=True,
                password_hash="pwd_v75",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        learner_role = db.execute(select(Role).where(Role.name.not_in(["Administrator", "admin", "Admin"]))).scalars().first()
        learner1 = db.execute(select(User).where(User.email == "learner1_v75@mospi.gov.in")).scalar_one_or_none()
        if not learner1:
            learner1 = User(
                email="learner1_v75@mospi.gov.in",
                full_name="Learner 1 V75",
                role_id=learner_role.id if learner_role else 1,
                is_active=True,
                password_hash="pwd_v75",
            )
            db.add(learner1)
            db.commit()
            db.refresh(learner1)

        learner2 = db.execute(select(User).where(User.email == "learner2_v75@mospi.gov.in")).scalar_one_or_none()
        if not learner2:
            learner2 = User(
                email="learner2_v75@mospi.gov.in",
                full_name="Learner 2 V75",
                role_id=learner_role.id if learner_role else 1,
                is_active=True,
                password_hash="pwd_v75",
            )
            db.add(learner2)
            db.commit()
            db.refresh(learner2)

        admin_h = {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}
        l1_h = {"Authorization": f"Bearer {create_access_token(subject=learner1.id)}"}
        l2_h = {"Authorization": f"Bearer {create_access_token(subject=learner2.id)}"}

        # 1. Learner Isolation
        print_step(1, "Learner Data Isolation Verification")
        r1 = client.get("/api/competency/timeline", headers=l1_h)
        r2 = client.get("/api/competency/timeline", headers=l2_h)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["user_id"] == learner1.id
        assert r2.json()["user_id"] == learner2.id
        assert r1.json()["user_id"] != r2.json()["user_id"]
        print(f"[*] Learner 1 timeline user_id={r1.json()['user_id']} | Learner 2 timeline user_id={r2.json()['user_id']}")
        print("[*] Strict tenant/user data isolation verified.")

        # 2. Zero Demographic Fabrication
        print_step(2, "Zero Demographic Fabrication Audit")
        user_cols = set(User.model_fields.keys() if hasattr(User, "model_fields") else User.__table__.columns.keys())
        forbidden = {"caste", "religion", "ethnicity", "gender_assumption", "income", "socioeconomic_tier"}
        for f in forbidden:
            assert f not in user_cols, f"Violation: Forbidden attribute {f} present!"
        print(f"[*] User model attributes inspected: {len(user_cols)} fields found. Zero demographic proxies verified.")

        # 3. Centralized Policy Registry & Modification
        print_step(3, "Centralized Policy Registry & Version Increment")
        p_res = client.get("/api/admin/policies", headers=admin_h)
        assert p_res.status_code == 200
        policies = p_res.json()["policies"]
        print(f"[*] Registered governance policies: {len(policies)}")
        assert "PRIVACY_SUPPRESSION_THRESHOLD" in policies
        assert policies["PRIVACY_SUPPRESSION_THRESHOLD"]["value"] == 5

        # Update policy
        old_v = policies["RETENTION_WINDOW_DAYS"]["version"]
        up_res = client.post(
            "/api/admin/policies/RETENTION_WINDOW_DAYS",
            json={"value": 95, "reason": "Runtime calibration verification test"},
            headers=admin_h,
        )
        assert up_res.status_code == 200
        new_v = up_res.json()["updated_policy"]["version"]
        print(f"[*] Updated RETENTION_WINDOW_DAYS: version {old_v} -> {new_v} | value={up_res.json()['updated_policy']['value']}")
        assert float(new_v) > float(old_v)

        # 4. Audit Event on Policy Modification
        print_step(4, "Policy Modification Audit Event Verification")
        audit_event = db.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "POLICY_UPDATED", AuditEvent.entity_id == "RETENTION_WINDOW_DAYS")
            .order_by(AuditEvent.timestamp.desc())
        ).scalars().first()
        assert audit_event is not None
        assert audit_event.actor_id == admin.id
        print(f"[*] Policy change successfully audited in event {audit_event.event_id} by actor {audit_event.actor_id}")

        # 5. Operational Health Probes
        print_step(5, "Operational Health & Subsystem Probes")
        h_res = client.get("/api/health")
        assert h_res.status_code == 200
        print(f"[*] Public Health Probe: /api/health -> {h_res.json()['status']}")

        s_res = client.get("/api/admin/system-status", headers=admin_h)
        assert s_res.status_code == 200
        counts = s_res.json()["table_record_counts"]
        print(f"[*] Admin System Telemetry: Users={counts['users']}, Competencies={counts['competencies']}, Items={counts['assessment_items']}")

        # 6. Strict RBAC Enforcement
        print_step(6, "Comprehensive RBAC Barrier Verification")
        assert client.get("/api/admin/policies", headers=l1_h).status_code == 403
        assert client.get("/api/admin/system-status", headers=l1_h).status_code == 403
        assert client.get("/api/admin/data-quality", headers=l1_h).status_code == 403
        assert client.get("/api/admin/audit-logs", headers=l1_h).status_code == 403
        print("[*] All 4 administrative endpoints returned 403 Forbidden for learner token [VERIFIED]")

        print("\n" + "=" * 75)
        print(" ALL TASK 7.5 E2E VERIFICATION STEPS PASSED SUCCESSFULLY!")
        print("=" * 75 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
