from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.scenario import (
    Scenario,
    ScenarioAttempt,
    ScenarioAttemptStatus,
    ScenarioEvaluation,
    ScenarioResponse,
    ScenarioStatus,
)
from app.services.orchestrator import recalculate_competency_state
from app.services.scenarios.scenario_interfaces import (
    CandidateValidationError,
    DeterministicScenarioEvaluator,
    DeterministicScenarioGenerator,
    EvaluationValidationError,
    ScenarioCandidate,
    ScenarioEvaluationResult,
    ScenarioEvaluator,
    ScenarioGenerationContext,
    ScenarioGenerator,
    validate_evaluation_result,
    validate_scenario_candidate,
)


class ScenarioService:
    """Service orchestrating realistic application scenarios, attempts, evaluations, and evidence emission."""

    @staticmethod
    def list_scenarios(
        db: Session,
        competency_id: int | None = None,
        subskill_id: int | None = None,
        role_id: int | None = None,
        difficulty: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Scenario]:
        stmt = select(Scenario).where(Scenario.status == ScenarioStatus.ACTIVE.value)
        if competency_id is not None:
            stmt = stmt.where(Scenario.competency_id == competency_id)
        if subskill_id is not None:
            stmt = stmt.where(Scenario.subskill_id == subskill_id)
        if role_id is not None:
            stmt = stmt.where(Scenario.role_id == role_id)
        if difficulty is not None:
            stmt = stmt.where(Scenario.difficulty == difficulty.lower())
        stmt = stmt.offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_scenario(db: Session, scenario_id_or_int: str | int) -> Scenario | None:
        if isinstance(scenario_id_or_int, int) or (isinstance(scenario_id_or_int, str) and scenario_id_or_int.isdigit()):
            return db.get(Scenario, int(scenario_id_or_int))
        return db.execute(
            select(Scenario).where(Scenario.scenario_id == str(scenario_id_or_int))
        ).scalar_one_or_none()

    @staticmethod
    def create_scenario(db: Session, candidate: ScenarioCandidate) -> Scenario:
        """Validate candidate scenario against taxonomy and persist."""
        validate_scenario_candidate(db, candidate)

        scenario = Scenario(
            scenario_id=candidate.scenario_id,
            title=candidate.title,
            description=candidate.description,
            scenario_type=candidate.scenario_type,
            role_id=candidate.role_id,
            competency_id=candidate.competency_id,
            subskill_id=candidate.subskill_id,
            difficulty=candidate.difficulty.lower(),
            source=candidate.source,
            provenance=candidate.provenance,
            version=candidate.version,
            status=candidate.status,
            expected_outcomes_json=json.dumps(candidate.expected_outcomes),
            evaluation_rubric_json=json.dumps(candidate.evaluation_rubric),
            metadata_json=json.dumps(candidate.metadata),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def generate_and_persist_scenario(
        db: Session,
        context: ScenarioGenerationContext,
        generator: ScenarioGenerator | None = None,
    ) -> Scenario:
        """Generate a candidate via replaceable generator, validate, and persist."""
        if generator is None:
            generator = DeterministicScenarioGenerator()

        candidate = generator.generate(context)
        return ScenarioService.create_scenario(db, candidate)

    @staticmethod
    def start_attempt(db: Session, user_id: int, scenario_id_or_int: str | int) -> ScenarioAttempt:
        scenario = ScenarioService.get_scenario(db, scenario_id_or_int)
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id_or_int}' not found.")

        attempt_id = f"scen_att_{uuid.uuid4().hex[:12]}"
        attempt = ScenarioAttempt(
            attempt_id=attempt_id,
            scenario_id=scenario.id,
            user_id=user_id,
            status=ScenarioAttemptStatus.STARTED.value,
            scenario_version=scenario.version,
            started_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_attempt(db: Session, user_id: int, attempt_id: str) -> ScenarioAttempt | None:
        attempt = db.execute(
            select(ScenarioAttempt).where(ScenarioAttempt.attempt_id == attempt_id)
        ).scalar_one_or_none()
        if not attempt:
            return None
        if attempt.user_id != user_id:
            raise PermissionError("Learner isolation violation: attempt belongs to another user.")
        return attempt

    @staticmethod
    def submit_attempt(
        db: Session,
        user_id: int,
        attempt_id: str,
        response_payload: dict[str, Any],
        idempotency_key: str | None = None,
        evaluator: ScenarioEvaluator | None = None,
    ) -> tuple[ScenarioAttempt, ScenarioEvaluation | None, dict[str, Any] | None]:
        """Submit scenario attempt, evaluate through evaluator boundary, emit evidence, and recalculate competency."""
        # 1. Idempotency Check
        if idempotency_key:
            existing_by_key = db.execute(
                select(ScenarioAttempt).where(ScenarioAttempt.idempotency_key == idempotency_key)
            ).scalar_one_or_none()
            if existing_by_key:
                if existing_by_key.user_id != user_id:
                    raise PermissionError("Idempotency key belongs to another user.")
                existing_eval = None
                if existing_by_key.evaluation_id:
                    existing_eval = db.get(ScenarioEvaluation, existing_by_key.evaluation_id)
                return existing_by_key, existing_eval, None

        # 2. Learner Isolation & Attempt Retrieval
        attempt = ScenarioService.get_attempt(db, user_id, attempt_id)
        if not attempt:
            raise ValueError(f"Scenario attempt '{attempt_id}' not found.")

        # Check if already completed
        if attempt.status in (ScenarioAttemptStatus.EVALUATED.value, ScenarioAttemptStatus.REVIEW_REQUIRED.value):
            existing_eval = db.get(ScenarioEvaluation, attempt.evaluation_id) if attempt.evaluation_id else None
            return attempt, existing_eval, None

        scenario = db.get(Scenario, attempt.scenario_id)
        if not scenario:
            raise ValueError(f"Scenario with id {attempt.scenario_id} not found.")

        # 3. Store Learner Response
        response_rec = ScenarioResponse(
            attempt_id=attempt.id,
            response_payload_json=json.dumps(response_payload),
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(response_rec)
        db.flush()

        # Update attempt submission state
        attempt.status = ScenarioAttemptStatus.SUBMITTED.value
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.idempotency_key = idempotency_key

        # 4. Resolve Evaluator & Run Evaluation
        if evaluator is None:
            evaluator = DeterministicScenarioEvaluator()

        eval_result: ScenarioEvaluationResult = evaluator.evaluate(scenario, response_payload)
        validate_evaluation_result(eval_result)

        # 5. Persist Evaluation Record
        evaluation = ScenarioEvaluation(
            attempt_id=attempt.id,
            score=eval_result.score,
            max_score=eval_result.max_score,
            normalized_score=eval_result.normalized_score,
            passed=eval_result.passed,
            competency_evidence_json=json.dumps(eval_result.competency_evidence),
            subskill_evidence_json=json.dumps(eval_result.subskill_evidence),
            rubric_results_json=json.dumps(eval_result.rubric_results),
            evaluator_type=eval_result.evaluator_type,
            evaluator_version=eval_result.evaluator_version,
            confidence=eval_result.confidence,
            review_required=eval_result.review_required,
            provenance=eval_result.provenance,
            feedback=eval_result.feedback,
            created_at=datetime.now(timezone.utc),
        )
        db.add(evaluation)
        db.flush()

        attempt.evaluation_id = evaluation.id
        attempt.score = eval_result.normalized_score
        attempt.status = (
            ScenarioAttemptStatus.REVIEW_REQUIRED.value
            if eval_result.review_required
            else ScenarioAttemptStatus.EVALUATED.value
        )
        attempt.updated_at = datetime.now(timezone.utc)

        # 6. Structured Evidence Creation (EvidenceType.APPLICATION_SCENARIO)
        competency_update_summary: dict[str, Any] | None = None

        evidence = Evidence(
            user_id=user_id,
            competency_id=scenario.competency_id,
            subskill_id=scenario.subskill_id,
            evidence_type=EvidenceType.APPLICATION_SCENARIO,
            title=f"Scenario: {scenario.title}",
            description=f"Operational application scenario evaluation score {eval_result.normalized_score:.2%} on {scenario.scenario_id}",
            score=eval_result.normalized_score,
            source=f"SCENARIO:{scenario.scenario_id}",
            provenance=eval_result.provenance,
            reliability_status="VERIFIED" if eval_result.confidence >= 0.80 else "PROVISIONAL",
            evidence_metadata=json.dumps({
                "scenario_id": scenario.scenario_id,
                "scenario_version": scenario.version,
                "evaluator_type": eval_result.evaluator_type,
                "evaluator_version": eval_result.evaluator_version,
                "attempt_id": attempt.attempt_id,
                "passed": eval_result.passed,
                "confidence": eval_result.confidence,
                "review_required": eval_result.review_required,
                "rubric_results": eval_result.rubric_results,
            }),
            observed_at=datetime.now(timezone.utc),
        )
        db.add(evidence)
        db.flush()

        # 7. Route through Competency State Engine
        orch_result = recalculate_competency_state(
            db,
            user_id=user_id,
            competency_id=scenario.competency_id,
            triggering_evidence_id=evidence.id,
        )
        competency_update_summary = {
            "competency_id": scenario.competency_id,
            "mastery": orch_result.state.mastery,
            "confidence": orch_result.state.confidence,
            "status": orch_result.state.status,
            "evidence_id": evidence.id,
            "score": eval_result.normalized_score,
            "passed": eval_result.passed,
        }

        db.commit()
        db.refresh(attempt)
        db.refresh(evaluation)
        return attempt, evaluation, competency_update_summary
