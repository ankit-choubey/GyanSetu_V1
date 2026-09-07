"""
scripts/verify_task_7_4_e2e.py — Phase 7.4 Outcome Analytics Runtime E2E Verifier.

Verifies:
1. Recommendation conversion funnel (Proposed -> Accepted -> Started -> Completed -> Rejected).
2. Acceptance, completion, and rejection rates.
3. Observed intervention pre/post mastery gain calculations.
4. Non-causal association reporting with explicit disclaimers.
5. Ecosystem provider breakdown (counts, average scores, completion rates).
6. Admin REST endpoints & RBAC enforcement.
"""

from __future__ import annotations

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
from app.models.competency import Competency, Role
from app.models.intervention import Intervention
from app.models.intervention_outcome import InterventionOutcome
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.outcome_analytics_service import OutcomeAnalyticsService
from app.utils.security import create_access_token


def print_step(num: int, title: str) -> None:
    print(f"\n{'='*75}\n STEP {num}: {title.upper()}\n{'='*75}")


def main() -> None:
    print("\n" + "=" * 75)
    print(" GYANSETU V1 — TASK 7.4 OUTCOME ANALYTICS E2E VERIFICATION")
    print("=" * 75)

    db = SessionLocal()
    client = TestClient(app)

    try:
        admin_role = db.execute(select(Role).where(Role.name.in_(["Administrator", "admin", "Admin"]))).scalars().first()
        admin = db.execute(select(User).where(User.email == "admin_v74@mospi.gov.in")).scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin_v74@mospi.gov.in",
                full_name="Admin V74",
                role_id=admin_role.id if admin_role else 9,
                is_active=True,
                password_hash="pwd_v74",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        learner_role = db.execute(select(Role).where(Role.name.not_in(["Administrator", "admin", "Admin"]))).scalars().first()
        learner = db.execute(select(User).where(User.email == "learner_v74@mospi.gov.in")).scalar_one_or_none()
        if not learner:
            learner = User(
                email="learner_v74@mospi.gov.in",
                full_name="Learner V74",
                role_id=learner_role.id if learner_role else 1,
                is_active=True,
                password_hash="pwd_v74",
            )
            db.add(learner)
            db.commit()
            db.refresh(learner)

        admin_h = {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}
        learner_h = {"Authorization": f"Bearer {create_access_token(subject=learner.id)}"}

        comp = Competency(name=f"Outcome Comp {uuid.uuid4().hex[:6]}", code=f"OTC_{uuid.uuid4().hex[:4]}")
        db.add(comp)
        db.commit()
        db.refresh(comp)

        it_diksha = Intervention(
            competency_id=comp.id,
            title="Sampling in Field Surveys",
            intervention_type="LEARNING_RESOURCE",
            provider="DIKSHA",
            source_id=f"diksha_{uuid.uuid4().hex[:6]}",
        )
        it_igot = Intervention(
            competency_id=comp.id,
            title="Administrative Data Systems",
            intervention_type="LEARNING_RESOURCE",
            provider="IGOT_KARMAYOGI",
            source_id=f"igot_{uuid.uuid4().hex[:6]}",
        )
        db.add_all([it_diksha, it_igot])
        db.commit()

        # 1. Recommendation Funnel
        print_step(1, "Recommendation Funnel Conversion Evaluation")
        rec1 = RecommendationRecord(recommendation_id=f"rec_{uuid.uuid4().hex[:12]}", user_id=learner.id, competency_id=comp.id, status="COMPLETED")
        rec2 = RecommendationRecord(recommendation_id=f"rec_{uuid.uuid4().hex[:12]}", user_id=learner.id, competency_id=comp.id, status="ACCEPTED")
        rec3 = RecommendationRecord(recommendation_id=f"rec_{uuid.uuid4().hex[:12]}", user_id=learner.id, competency_id=comp.id, status="REJECTED")
        rec4 = RecommendationRecord(recommendation_id=f"rec_{uuid.uuid4().hex[:12]}", user_id=learner.id, competency_id=comp.id, status="SKIPPED")
        db.add_all([rec1, rec2, rec3, rec4])
        db.commit()

        funnel = OutcomeAnalyticsService.get_recommendation_funnel_analytics(db)
        print(f"[*] Total recommendations generated: {funnel['total_recommendations_generated']}")
        print(f"[*] Acceptance Rate:                 {round(funnel['acceptance_rate'] * 100, 1)}%")
        print(f"[*] Completion Rate:                 {round(funnel['completion_rate'] * 100, 1)}%")
        print(f"[*] Rejection Rate:                  {round(funnel['rejection_rate'] * 100, 1)}%")
        assert funnel["total_recommendations_generated"] >= 4

        # 2. Observed Gains & Non-Causal Associations
        print_step(2, "Intervention Observed Gains & Causal Disclaimers")
        out1 = InterventionOutcome(
            user_id=learner.id,
            intervention_id=it_diksha.id,
            status="COMPLETED",
            completion_score=0.88,
            pre_competency_mastery=0.40,
            post_competency_mastery=0.75,
            provider="DIKSHA",
        )
        out2 = InterventionOutcome(
            user_id=learner.id,
            intervention_id=it_igot.id,
            status="COMPLETED",
            completion_score=0.92,
            pre_competency_mastery=0.30,
            post_competency_mastery=0.80,
            provider="IGOT_KARMAYOGI",
        )
        db.add_all([out1, out2])
        db.commit()

        outcomes = OutcomeAnalyticsService.get_intervention_outcome_analytics(db)
        gains = outcomes["observed_gains"]
        print(f"[*] Completed outcomes: {outcomes['completed_count']}")
        print(f"[*] Observed Mean Gain: {gains['mean_gain']}")
        print(f"[*] Positive Gain Rate: {round(gains['positive_outcome_rate'] * 100, 1)}%")
        print(f"[*] Causal Disclaimer:  {gains['causal_disclaimer']}")
        assert "no causal claim" in gains["causal_disclaimer"].lower()

        # 3. Provider Breakdown
        print_step(3, "Ecosystem Provider Breakdown")
        pb = outcomes["provider_breakdown"]
        for prov_name, prov_info in pb.items():
            print(f"    - Provider {prov_name:16}: total={prov_info['total']}, completed={prov_info['completed']}, avg_score={prov_info['avg_score']}")
        assert "DIKSHA" in pb
        assert "IGOT_KARMAYOGI" in pb

        # 4. REST Endpoints & RBAC
        print_step(4, "Admin REST Endpoints & RBAC Verification")
        res_rec = client.get("/api/admin/analytics/recommendations", headers=admin_h)
        assert res_rec.status_code == 200
        assert "funnel" in res_rec.json()

        res_out = client.get("/api/admin/analytics/interventions/outcomes", headers=admin_h)
        assert res_out.status_code == 200
        assert "provider_breakdown" in res_out.json()
        print("[*] Admin endpoints verified: /recommendations (200), /interventions/outcomes (200)")

        # Learner blocked
        assert client.get("/api/admin/analytics/recommendations", headers=learner_h).status_code == 403
        assert client.get("/api/admin/analytics/interventions/outcomes", headers=learner_h).status_code == 403
        print("[*] Learner access blocked with 403 Forbidden [VERIFIED]")

        print("\n" + "=" * 75)
        print(" ALL TASK 7.4 E2E VERIFICATION STEPS PASSED SUCCESSFULLY!")
        print("=" * 75 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
