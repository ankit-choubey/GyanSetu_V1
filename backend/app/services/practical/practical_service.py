import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.evidence import Evidence, EvidenceType
from app.models.practical import AttemptStatus, PracticalAttempt, PracticalTask
from app.services.orchestrator import recalculate_competency_state
from app.services.practical.deterministic_evaluator import DeterministicEvaluator
from app.services.practical.evaluator_base import EvaluationResult, PracticalEvaluator
from app.services.practical.llm_evaluator import LLMEvaluator


class PracticalService:
    """Service orchestrating the complete practical task lifecycle, evaluation, and evidence emission."""

    @staticmethod
    def list_tasks(
        db: Session,
        competency_id: int | None = None,
        difficulty: str | None = None,
        scenario_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PracticalTask]:
        stmt = select(PracticalTask).where(PracticalTask.status == "ACTIVE")
        if competency_id is not None:
            stmt = stmt.where(PracticalTask.competency_id == competency_id)
        if difficulty is not None:
            stmt = stmt.where(PracticalTask.difficulty == difficulty.lower())
        if scenario_type is not None:
            stmt = stmt.where(PracticalTask.scenario_type == scenario_type.upper())
        stmt = stmt.offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_task(db: Session, task_id_or_int: str | int) -> PracticalTask | None:
        if isinstance(task_id_or_int, int) or (isinstance(task_id_or_int, str) and task_id_or_int.isdigit()):
            return db.get(PracticalTask, int(task_id_or_int))
        return db.execute(
            select(PracticalTask).where(PracticalTask.task_id == str(task_id_or_int))
        ).scalar_one_or_none()

    @staticmethod
    def start_attempt(db: Session, user_id: int, task_id_or_int: str | int) -> PracticalAttempt:
        task = PracticalService.get_task(db, task_id_or_int)
        if not task:
            raise ValueError(f"Practical task '{task_id_or_int}' not found.")

        attempt_id = f"pr_att_{uuid.uuid4().hex[:12]}"
        attempt = PracticalAttempt(
            attempt_id=attempt_id,
            task_id=task.id,
            user_id=user_id,
            status=AttemptStatus.STARTED.value,
            task_version=task.version,
            rubric_version=task.rubric_version,
            started_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_attempt(db: Session, user_id: int, attempt_id: str) -> PracticalAttempt | None:
        attempt = db.execute(
            select(PracticalAttempt).where(PracticalAttempt.attempt_id == attempt_id)
        ).scalar_one_or_none()
        if not attempt:
            return None
        if attempt.user_id != user_id:
            raise PermissionError("Learner isolation violation: attempt belongs to another user.")
        return attempt

    @staticmethod
    def list_user_attempts(
        db: Session,
        user_id: int,
        task_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PracticalAttempt]:
        stmt = select(PracticalAttempt).where(PracticalAttempt.user_id == user_id)
        if task_id is not None:
            stmt = stmt.where(PracticalAttempt.task_id == task_id)
        stmt = stmt.order_by(PracticalAttempt.created_at.desc()).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def submit_attempt(
        db: Session,
        user_id: int,
        attempt_id: str,
        submission_payload: dict[str, Any],
        idempotency_key: str | None = None,
        evaluator_type: str | None = None,
    ) -> tuple[PracticalAttempt, dict[str, Any] | None]:
        """Submit and evaluate a practical attempt, emitting evidence and updating competency state."""
        # 1. Idempotency Check
        if idempotency_key:
            existing_by_key = db.execute(
                select(PracticalAttempt).where(PracticalAttempt.idempotency_key == idempotency_key)
            ).scalar_one_or_none()
            if existing_by_key:
                if existing_by_key.user_id != user_id:
                    raise PermissionError("Idempotency key belongs to another user.")
                return existing_by_key, None

        # 2. Fetch Attempt & Learner Isolation
        attempt = PracticalService.get_attempt(db, user_id, attempt_id)
        if not attempt:
            raise ValueError(f"Attempt '{attempt_id}' not found.")

        # Check if already completed
        if attempt.status in (AttemptStatus.EVALUATED.value, AttemptStatus.REVIEW_REQUIRED.value):
            return attempt, None

        task = db.get(PracticalTask, attempt.task_id)
        if not task:
            raise ValueError(f"Task with id {attempt.task_id} not found.")

        # 3. Transition to EVALUATING
        attempt.status = AttemptStatus.EVALUATING.value
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.submission_payload_json = json.dumps(submission_payload)
        attempt.idempotency_key = idempotency_key

        # 4. Resolve Evaluator
        evaluator: PracticalEvaluator
        if evaluator_type == "LLM_ASSISTED":
            evaluator = LLMEvaluator()
        else:
            evaluator = DeterministicEvaluator()

        # 5. Execute Evaluation
        eval_result: EvaluationResult = evaluator.evaluate(task, submission_payload)

        attempt.score = eval_result.score
        attempt.status = eval_result.status
        attempt.evaluator_type = eval_result.evaluator_type
        attempt.evaluator_version = eval_result.evaluator_version
        attempt.evaluation_result_json = json.dumps(eval_result.to_dict())
        attempt.updated_at = datetime.now(timezone.utc)

        # 6. Evidence Emission & Competency Recalculation
        competency_update_summary: dict[str, Any] | None = None

        if attempt.status == AttemptStatus.EVALUATED.value:
            # Emit structured practical evidence
            evidence = Evidence(
                user_id=user_id,
                competency_id=task.competency_id,
                subskill_id=task.subskill_id,
                evidence_type=EvidenceType.PRACTICAL_TASK,
                title=f"Practical Task: {task.title}",
                description=f"Automated practical verification score {eval_result.score:.2%} on {task.task_id}",
                score=eval_result.score,
                source=f"PRACTICAL_TASK:{task.task_id}",
                provenance="[SANDBOX DATA]",
                reliability_status="VERIFIED",
                evidence_metadata=json.dumps({
                    "task_id": task.task_id,
                    "task_version": task.version,
                    "rubric_version": task.rubric_version,
                    "evaluator_type": eval_result.evaluator_type,
                    "evaluator_version": eval_result.evaluator_version,
                    "attempt_id": attempt.attempt_id,
                    "dimension_scores": eval_result.dimension_scores,
                }),
                observed_at=datetime.now(timezone.utc),
            )
            db.add(evidence)
            db.flush()

            attempt.evidence_id = evidence.id

            # Trigger transactional competency state recalculation
            orch_result = recalculate_competency_state(
                db,
                user_id=user_id,
                competency_id=task.competency_id,
                triggering_evidence_id=evidence.id,
            )
            competency_update_summary = {
                "competency_id": task.competency_id,
                "mastery": orch_result.state.mastery,
                "confidence": orch_result.state.confidence,
                "status": orch_result.state.status,
                "evidence_id": evidence.id,
            }

        db.commit()
        db.refresh(attempt)
        return attempt, competency_update_summary
