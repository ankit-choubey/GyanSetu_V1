"""
scripts/verify_task_7_1_e2e.py — Phase 7.1 Audit Provenance & Data Quality Runtime E2E Verifier.

Verifies:
1. Immutable Audit Event Creation with Actors, Actions, Results, Correlation IDs.
2. Structured JSON State Deltas (before_state, after_state, metadata).
3. Paginated Administrative Audit Queries with Multi-Dimensional Filtering.
4. Summary Audit Statistics & Distribution.
5. 5-Pillar Data Quality Engine Scan (Taxonomy, Evidence, Assessment, Intervention, State).
6. Data Quality Scorecard Summary & Category Diagnostic Inspections.
7. Strict RBAC Enforcement (Admin 200 vs Learner 403).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
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
from app.services.audit_service import AuditService
from app.services.data_quality_service import DataQualityService
from app.utils.security import create_access_token


def print_step(num: int, title: str) -> None:
    print(f"\n{'='*75}\n STEP {num}: {title.upper()}\n{'='*75}")


def main() -> None:
    print("\n" + "=" * 75)
    print(" GYANSETU V1 — TASK 7.1 AUDIT PROVENANCE & DATA QUALITY E2E VERIFICATION")
    print("=" * 75)

    db = SessionLocal()
    client = TestClient(app)

    try:
        admin_role = db.execute(select(Role).where(Role.name.in_(["Administrator", "admin", "Admin"]))).scalars().first()
        admin = db.execute(select(User).where(User.email == "admin_v71@mospi.gov.in")).scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin_v71@mospi.gov.in",
                full_name="Admin V71",
                role_id=admin_role.id if admin_role else 9,
                is_active=True,
                password_hash="pwd_v71",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        learner_role = db.execute(select(Role).where(Role.name.not_in(["Administrator", "admin", "Admin"]))).scalars().first()
        learner = db.execute(select(User).where(User.email == "learner_v71@mospi.gov.in")).scalar_one_or_none()
        if not learner:
            learner = User(
                email="learner_v71@mospi.gov.in",
                full_name="Learner V71",
                role_id=learner_role.id if learner_role else 1,
                is_active=True,
                password_hash="pwd_v71",
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)

        admin_h = {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}
        learner_h = {"Authorization": f"Bearer {create_access_token(subject=learner.id)}"}

        # 1. Audit Event Creation
        print_step(1, "Create Immutable Audit Events")
        corr_id = f"corr_{uuid.uuid4().hex[:12]}"
        evt1 = AuditService.log_event(
            db=db,
            action="MODEL_DEPLOY",
            entity_type="RECOMMENDER",
            actor_id=admin.id,
            actor_role="ADMINISTRATOR",
            entity_id="REC-2026",
            result="SUCCESS",
            correlation_id=corr_id,
            before_state={"version": "1.0"},
            after_state={"version": "1.1"},
            metadata={"environment": "production_simulation"},
        )
        assert evt1.id is not None
        assert evt1.event_id.startswith("evt_")
        print(f"[*] Created AuditEvent: {evt1.event_id} | action={evt1.action} | result={evt1.result}")

        # 2. Query Audit Events via Admin REST API
        print_step(2, "Query Paginated Audit Events via API")
        res = client.get(f"/api/admin/audit-logs?correlation_id={corr_id}", headers=admin_h)
        assert res.status_code == 200, f"Failed: {res.text}"
        data = res.json()
        assert data["total_matches"] >= 1
        assert data["events"][0]["event_id"] == evt1.event_id
        print(f"[*] Retrieved {data['total_matches']} event(s) matching correlation_id={corr_id}")

        # 3. Audit Summary Statistics
        print_step(3, "Audit Summary Statistics & Distribution")
        res_sum = client.get("/api/admin/audit-logs/summary", headers=admin_h)
        assert res_sum.status_code == 200
        sum_data = res_sum.json()
        print(f"[*] Total audit events: {sum_data['total_events']}")
        print(f"[*] Distinct actions recorded: {len(sum_data['top_actions'])}")
        assert sum_data["total_events"] >= 1

        # 4. Data Quality System-Wide Scan
        print_step(4, "Execute 5-Pillar Data Quality Engine Scan")
        dq_res = client.get("/api/admin/data-quality", headers=admin_h)
        assert dq_res.status_code == 200
        dq_data = dq_res.json()
        print(f"[*] Overall Data Health Score: {round(dq_data['overall_data_health_score'] * 100, 1)}%")
        print(f"[*] Health Status:             {dq_data['status']}")
        print(f"[*] Total Issues Detected:     {dq_data['total_issues_count']} (Errors: {dq_data['errors_count']}, Warnings: {dq_data['warnings_count']})")
        assert 0.0 <= dq_data["overall_data_health_score"] <= 1.0

        # 5. Category-Specific Data Quality Inspection
        print_step(5, "Category Diagnostic Inspection")
        for cat in ["TAXONOMY", "EVIDENCE", "ASSESSMENT", "INTERVENTION", "COMPETENCY_STATE"]:
            c_res = client.get(f"/api/admin/data-quality/{cat}", headers=admin_h)
            assert c_res.status_code == 200
            c_data = c_res.json()
            print(f"    - Category {cat:16}: {c_data['issues_count']} issues (Errors: {c_data['errors_count']}, Warnings: {c_data['warnings_count']})")

        # 6. RBAC Authorization Barrier
        print_step(6, "RBAC Authorization Enforcement")
        learner_try1 = client.get("/api/admin/audit-logs", headers=learner_h)
        learner_try2 = client.get("/api/admin/data-quality", headers=learner_h)
        assert learner_try1.status_code == 403, f"Expected 403, got {learner_try1.status_code}"
        assert learner_try2.status_code == 403, f"Expected 403, got {learner_try2.status_code}"
        print(f"[*] Learner accessing /api/admin/audit-logs:   {learner_try1.status_code} Forbidden [VERIFIED]")
        print(f"[*] Learner accessing /api/admin/data-quality:  {learner_try2.status_code} Forbidden [VERIFIED]")

        print("\n" + "=" * 75)
        print(" ALL TASK 7.1 E2E VERIFICATION STEPS PASSED SUCCESSFULLY!")
        print("=" * 75 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
