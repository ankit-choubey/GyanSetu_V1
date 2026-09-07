from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency
from app.models.governance import (
    CompetencyGovernance,
    ModelRegistryRecord,
    ModelStatus,
    ReviewStatus,
)


class GovernanceService:
    """Manages competency graph governance, review status, and the analytical model registry."""

    DEFAULT_MODELS: list[dict[str, Any]] = [
        {
            "name": "Deterministic Multi-Source Estimator",
            "version": "v2.0-deterministic",
            "model_type": "Competency Estimation",
            "scientific_status": ModelStatus.PRODUCTION_BASELINE.value,
            "training_data_description": "Rule-based multi-modal evidence fusion engine (scenarios: 0.35, tasks: 0.30, assessments: 0.20, history: 0.10, signals: 0.05).",
            "evaluation_reference": "Phase 6 benchmark: RMSE 0.4221, AUC 0.6413, ECE 0.1268 on 40 held-out test learners.",
            "limitations": "Linear heuristic weighting; doesn't dynamically adapt weights per learner.",
            "production_status": "Active system of record in production.",
        },
        {
            "name": "Bayesian Knowledge Tracing (BKT)",
            "version": "v1.0-analytical",
            "model_type": "Sequential Knowledge Tracing",
            "scientific_status": ModelStatus.RESEARCH.value,
            "training_data_description": "Hidden Markov parameterization (p_init=0.20, p_learn=0.15, p_guess=0.20, p_slip=0.10).",
            "evaluation_reference": "Phase 6 benchmark: RMSE 0.3815, AUC 0.6529, ECE 0.0544 on binary item traces.",
            "limitations": "Constrained to binary correct/incorrect sequences; cannot ingest multi-modal scenario evidence.",
            "production_status": "Retained as analytical research candidate.",
        },
        {
            "name": "Item Response Theory (IRT-2PL)",
            "version": "v1.0-analytical",
            "model_type": "Psychometric Item Calibration",
            "scientific_status": ModelStatus.RESEARCH.value,
            "training_data_description": "2-parameter logistic model (difficulty b in [-2, 2], discrimination a in [0.5, 2.0]).",
            "evaluation_reference": "Phase 6 benchmark: RMSE 0.4286, AUC 0.6712, Brier 0.1837 on test item pool.",
            "limitations": "Unidimensional latent trait assumption; computationally intensive for real-time edge updates.",
            "production_status": "Retained as question bank calibration research candidate.",
        },
        {
            "name": "Linear Recency Decay Model",
            "version": "v1.0-heuristic",
            "model_type": "Temporal Forgetting",
            "scientific_status": ModelStatus.ENGINEERING_HEURISTIC.value,
            "training_data_description": "0.01/day linear degradation parameterization approximating Ebbinghaus decay.",
            "evaluation_reference": "Phase 6 benchmark: RMSE 0.0086 vs simulated 90-day trajectories.",
            "limitations": "Simulation consistency check only; empirical validation on real MoSPI workforce is DEFERRED.",
            "production_status": "Verified engineering heuristic for time-elapsed decay.",
        },
        {
            "name": "Multi-Factor Heuristic Recommendation Ranker",
            "version": "v1.0-heuristic",
            "model_type": "Intervention Prioritization",
            "scientific_status": ModelStatus.PRODUCTION_BASELINE.value,
            "training_data_description": "Deterministic rule ranker (misconception: 0.35, subskill: 0.30, gap: 0.15, severity: 0.10, modality: 0.05, priority: 0.05).",
            "evaluation_reference": "Phase 6 benchmark: Observed competency gain 0.0638 vs 0.0545 random baseline.",
            "limitations": "Evaluates retrospective outcome association; non-causal.",
            "production_status": "Active recommendation policy in production.",
        },
        {
            "name": "Contextual Bandit (LinUCB)",
            "version": "v1.0-bandit",
            "model_type": "Adaptive Recommendation",
            "scientific_status": ModelStatus.RESEARCH.value,
            "training_data_description": "Linear Upper Confidence Bound contextual exploration algorithm.",
            "evaluation_reference": "Phase 6 benchmark: Observed gain 0.0646 on held-out split (statistically indistinguishable from heuristic ranker).",
            "limitations": "Requires cold-start exploration phase; lacks explicit human-readable factor rationale.",
            "production_status": "Retained as research exploration candidate.",
        },
        {
            "name": "Deterministic Practical Task Evaluator",
            "version": "v1.0-rubric",
            "model_type": "Performance Assessment",
            "scientific_status": ModelStatus.PRODUCTION_BASELINE.value,
            "training_data_description": "Multi-criteria numerical rubric with tolerance boundary verification (laspeyres index, response rate, Neyman allocation).",
            "evaluation_reference": "Phase 6 practical audit: Score variance 0.0 (100% reproducible and invariant across runs).",
            "limitations": "Requires structured numerical input/output contracts; cannot grade free-form prose without LLM assist.",
            "production_status": "Active practical learning evaluator in production.",
        },
    ]

    @classmethod
    def initialize_governance_data(cls, db: Session) -> dict[str, int]:
        """Idempotently seeds competency governance and model registry entries."""
        comps = db.execute(select(Competency)).scalars().all()
        created_gov = 0
        updated_gov = 0

        for comp in comps:
            existing = db.execute(
                select(CompetencyGovernance).where(CompetencyGovernance.competency_id == comp.id)
            ).scalar_one_or_none()

            if not existing:
                # Default status: CURATED. (Let competency #40 be UNDER_REVIEW for testing)
                status = ReviewStatus.UNDER_REVIEW.value if comp.id == 40 else ReviewStatus.CURATED.value
                gov = CompetencyGovernance(
                    competency_id=comp.id,
                    version="v1.0",
                    review_status=status,
                    mapping_provenance="[CURATED:MOSPI_TAXONOMY]",
                    expert_review_notes="Curated official statistics civil service competency mapping." if comp.id != 40 else "Provisional mapping awaiting MoSPI expert review panel.",
                    reviewed_by="MoSPI DIID Curriculum Committee" if comp.id != 40 else None,
                    reviewed_at=datetime.now(timezone.utc) if comp.id != 40 else None,
                    is_deprecated=False,
                )
                db.add(gov)
                created_gov += 1
            else:
                updated_gov += 1

        created_models = 0
        for m_data in cls.DEFAULT_MODELS:
            m_existing = db.execute(
                select(ModelRegistryRecord).where(ModelRegistryRecord.name == m_data["name"])
            ).scalar_one_or_none()

            if not m_existing:
                rec = ModelRegistryRecord(
                    name=m_data["name"],
                    version=m_data["version"],
                    model_type=m_data["model_type"],
                    scientific_status=m_data["scientific_status"],
                    training_data_description=m_data["training_data_description"],
                    evaluation_reference=m_data["evaluation_reference"],
                    limitations=m_data["limitations"],
                    production_status=m_data["production_status"],
                )
                db.add(rec)
                created_models += 1

        db.commit()
        return {"created_governance": created_gov, "created_models": created_models}

    @classmethod
    def get_competency_governance(cls, db: Session, competency_id: int) -> dict[str, Any] | None:
        gov = db.execute(
            select(CompetencyGovernance).where(CompetencyGovernance.competency_id == competency_id)
        ).scalar_one_or_none()

        if not gov:
            return None

        comp = db.get(Competency, competency_id)
        return {
            "competency_id": gov.competency_id,
            "competency_name": comp.name if comp else f"Competency #{competency_id}",
            "domain": comp.domain.value if comp else "Statistical",
            "version": gov.version,
            "review_status": gov.review_status,
            "mapping_provenance": gov.mapping_provenance,
            "expert_review_notes": gov.expert_review_notes,
            "reviewed_by": gov.reviewed_by,
            "reviewed_at": gov.reviewed_at.isoformat() if gov.reviewed_at else None,
            "is_deprecated": gov.is_deprecated,
            "is_authoritative_for_scoring": gov.review_status in (ReviewStatus.VERIFIED.value, ReviewStatus.CURATED.value),
        }

    @classmethod
    def update_review_status(
        cls,
        db: Session,
        competency_id: int,
        review_status: ReviewStatus,
        notes: str | None = None,
        reviewer: str | None = None,
    ) -> dict[str, Any]:
        gov = db.execute(
            select(CompetencyGovernance).where(CompetencyGovernance.competency_id == competency_id)
        ).scalar_one_or_none()

        if not gov:
            gov = CompetencyGovernance(
                competency_id=competency_id,
                version="v1.0",
                review_status=review_status.value,
                expert_review_notes=notes,
                reviewed_by=reviewer,
                reviewed_at=datetime.now(timezone.utc),
            )
            db.add(gov)
        else:
            gov.review_status = review_status.value
            if notes:
                gov.expert_review_notes = notes
            if reviewer:
                gov.reviewed_by = reviewer
            gov.reviewed_at = datetime.now(timezone.utc)
            gov.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(gov)
        return cls.get_competency_governance(db, competency_id) or {}

    @classmethod
    def get_model_registry(cls, db: Session) -> list[dict[str, Any]]:
        cls.initialize_governance_data(db)
        records = db.execute(select(ModelRegistryRecord).order_by(ModelRegistryRecord.id)).scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "version": r.version,
                "model_type": r.model_type,
                "scientific_status": r.scientific_status,
                "training_data_description": r.training_data_description,
                "evaluation_reference": r.evaluation_reference,
                "limitations": r.limitations,
                "production_status": r.production_status,
                "is_production_baseline": r.scientific_status == ModelStatus.PRODUCTION_BASELINE.value,
            }
            for r in records
        ]
