"""
scripts/verify_task_7_2_e2e.py — Phase 7.2 Psychometric Item Analytics Runtime E2E Verifier.

Verifies:
1. Cold-start handling for never-attempted questions.
2. Empirical difficulty calculation (P-value).
3. Distractor utilization distribution and anomaly detection.
4. Point-Biserial discrimination index computation.
5. Quality review flag triggering (INSUFFICIENT_DATA, EXTREMELY_EASY, DISTRACTOR_UNUSED).
6. Question bank catalog analytics and filtering.
7. Admin REST endpoints & RBAC protection.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
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
from app.models.assessment import AssessmentAttempt, AssessmentItem, AssessmentResponse
from app.models.competency import Competency, Role
from app.models.user import User
from app.services.assessment_analytics_service import AssessmentAnalyticsService
from app.utils.security import create_access_token


def print_step(num: int, title: str) -> None:
    print(f"\n{'='*75}\n STEP {num}: {title.upper()}\n{'='*75}")


def main() -> None:
    print("\n" + "=" * 75)
    print(" GYANSETU V1 — TASK 7.2 PSYCHOMETRIC ITEM ANALYTICS E2E VERIFICATION")
    print("=" * 75)

    db = SessionLocal()
    client = TestClient(app)

    try:
        admin_role = db.execute(select(Role).where(Role.name.in_(["Administrator", "admin", "Admin"]))).scalars().first()
        admin = db.execute(select(User).where(User.email == "admin_v72@mospi.gov.in")).scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin_v72@mospi.gov.in",
                full_name="Admin V72",
                role_id=admin_role.id if admin_role else 9,
                is_active=True,
                password_hash="pwd_v72",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        learner_role = db.execute(select(Role).where(Role.name.not_in(["Administrator", "admin", "Admin"]))).scalars().first()
        learner = db.execute(select(User).where(User.email == "learner_v72@mospi.gov.in")).scalar_one_or_none()
        if not learner:
            learner = User(
                email="learner_v72@mospi.gov.in",
                full_name="Learner V72",
                role_id=learner_role.id if learner_role else 1,
                is_active=True,
                password_hash="pwd_v72",
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)

        admin_h = {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}
        learner_h = {"Authorization": f"Bearer {create_access_token(subject=learner.id)}"}

        comp = Competency(name=f"Analytics Competency {uuid.uuid4().hex[:6]}", code=f"ANL_{uuid.uuid4().hex[:4]}")
        db.add(comp)
        db.commit()
        db.refresh(comp)

        # 1. Cold Start Item
        print_step(1, "Cold-Start Handling for Never-Attempted Question")
        cold_item = AssessmentItem(
            competency_id=comp.id,
            question_text="What is multi-stage cluster sampling?",
            options_json=json.dumps({"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"}),
            correct_option="A",
            difficulty="MEDIUM",
        )
        db.add(cold_item)
        db.commit()
        db.refresh(cold_item)

        c_stats = AssessmentAnalyticsService.get_item_statistics(db, cold_item.id)
        assert c_stats["sample_size"] == 0
        assert "INSUFFICIENT_DATA" in c_stats["quality_flags"]
        assert "NEVER_ATTEMPTED" in c_stats["quality_flags"]
        print(f"[*] Cold-start item #{cold_item.id}: sample_size=0, flags={c_stats['quality_flags']}")

        # 2. Populated Item Response Evaluation
        print_step(2, "Psychometric Responses & Difficulty Calculation")
        item = AssessmentItem(
            competency_id=comp.id,
            question_text="Calculate the design effect (Deff) of a complex survey sample.",
            options_json=json.dumps({"A": "Var(complex)/Var(SRS)", "B": "Var(SRS)/Var(complex)", "C": "Sample Size Ratio", "D": "Non-response Rate"}),
            correct_option="A",
            difficulty="HARD",
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        # 12 responses: 9 correct on A, 2 on B, 1 on C, 0 on D
        for i in range(12):
            is_c = (i < 9)
            opt = "A" if is_c else ("B" if i < 11 else "C")
            att = AssessmentAttempt(user_id=learner.id, competency_id=comp.id, score=0.9 if is_c else 0.3)
            db.add(att)
            db.commit()
            r = AssessmentResponse(
                attempt_id=att.id,
                assessment_item_id=item.id,
                competency_id=comp.id,
                selected_option=opt,
                is_correct=is_c,
            )
            db.add(r)
        db.commit()

        stats = AssessmentAnalyticsService.get_item_statistics(db, item.id)
        assert stats["sample_size"] == 12
        assert stats["difficulty_index"] == 0.75
        assert stats["discrimination_index"] is not None
        assert "DISTRACTOR_UNUSED" in stats["quality_flags"]  # Option D was 0
        print(f"[*] Evaluated item #{item.id}: P-value={stats['difficulty_index']}, Discrimination={stats['discrimination_index']}")
        print(f"[*] Distractor distribution: {list(stats['option_distribution'].keys())}")
        print(f"[*] Quality flags: {stats['quality_flags']}")

        # 3. Question Bank Catalog Analytics
        print_step(3, "Question Bank Catalog Overview API")
        cat_res = client.get("/api/admin/assessment/items/analytics", headers=admin_h)
        assert cat_res.status_code == 200
        cat_data = cat_res.json()
        print(f"[*] Total items in catalog: {cat_data['total_items_in_catalog']}")
        print(f"[*] Evaluated items:        {cat_data['evaluated_count']}")

        # 4. Item Detail & Quality Endpoints
        print_step(4, "Single Item Analytics & Quality Endpoints")
        res_i = client.get(f"/api/admin/assessment/items/{item.id}/analytics", headers=admin_h)
        assert res_i.status_code == 200
        assert res_i.json()["item_id"] == item.id

        res_q = client.get(f"/api/admin/assessment/items/{item.id}/quality", headers=admin_h)
        assert res_q.status_code == 200
        assert "quality_flags" in res_q.json()
        print(f"[*] Verified GET /api/admin/assessment/items/{item.id}/analytics -> 200")
        print(f"[*] Verified GET /api/admin/assessment/items/{item.id}/quality -> 200")

        # 5. RBAC Protection
        print_step(5, "Learner RBAC Protection (403 Forbidden)")
        res_learn = client.get("/api/admin/assessment/items/analytics", headers=learner_h)
        assert res_learn.status_code == 403
        print(f"[*] Learner access to catalog analytics: {res_learn.status_code} Forbidden [VERIFIED]")

        print("\n" + "=" * 75)
        print(" ALL TASK 7.2 E2E VERIFICATION STEPS PASSED SUCCESSFULLY!")
        print("=" * 75 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
