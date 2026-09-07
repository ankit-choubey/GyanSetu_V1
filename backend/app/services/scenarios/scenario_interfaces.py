from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.scenario import Scenario


class CandidateValidationError(ValueError):
    """Raised when a scenario candidate fails backend validation."""
    pass


class EvaluationValidationError(ValueError):
    """Raised when an evaluator output fails backend validation."""
    pass


SUPPORTED_SCENARIO_TYPES = {
    "OPERATIONAL_PROCEDURE",
    "SURVEY_DESIGN",
    "DATA_VALIDATION",
    "INDEX_COMPUTATION",
    "FIELD_DISCREPANCY",
    "DECISION_SUPPORT",
}

SUPPORTED_DIFFICULTIES = {"easy", "medium", "hard"}


@dataclass(frozen=True)
class ScenarioGenerationContext:
    competency_id: int
    role_id: int | None = None
    subskill_id: int | None = None
    difficulty: str = "medium"
    scenario_type: str = "OPERATIONAL_PROCEDURE"
    learning_objective: str = "Verify statistical procedure and operational compliance."
    allowed_source_material: tuple[str, ...] = ("MOSPI_SURVEY_MANUAL", "OFFICIAL_STATISTICS_HANDBOOK")


@dataclass
class ScenarioCandidate:
    title: str
    description: str
    scenario_type: str
    competency_id: int
    subskill_id: int | None = None
    role_id: int | None = None
    difficulty: str = "medium"
    scenario_id: str = field(default_factory=lambda: f"scen_gen_{uuid.uuid4().hex[:8]}")
    version: int = 1
    source: str = "MOSPI_OPERATIONAL"
    provenance: str = "[SANDBOX DATA]"
    status: str = "ACTIVE"
    expected_outcomes: list[str] = field(default_factory=list)
    evaluation_rubric: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ScenarioGenerator(Protocol):
    def generate(self, context: ScenarioGenerationContext) -> ScenarioCandidate:
        """Generate a scenario candidate from structured context."""
        ...


class DeterministicScenarioGenerator:
    """Deterministic, reproducible scenario generator aligned with MoSPI operational procedures."""

    def generate(self, context: ScenarioGenerationContext) -> ScenarioCandidate:
        difficulty = context.difficulty.lower() if context.difficulty else "medium"
        scenario_type = context.scenario_type.upper() if context.scenario_type else "OPERATIONAL_PROCEDURE"

        expected_outcomes = [
            "Identify sampling frame stratification discrepancy accurately.",
            "Formulate appropriate operational correction according to MoSPI standards.",
            "Verify data consistency against secondary survey aggregates.",
        ]
        rubric = {
            "passing_threshold": 0.70,
            "criteria": [
                {"name": "discrepancy_identification", "weight": 0.40, "required_keyword": "stratification"},
                {"name": "corrective_action", "weight": 0.40, "required_keyword": "resample"},
                {"name": "validation_check", "weight": 0.20, "required_keyword": "consistency"},
            ],
            "rubric_version": "v1.0-scenario",
        }

        return ScenarioCandidate(
            scenario_id=f"scen_{uuid.uuid4().hex[:10]}",
            title=f"Field Operation Scenario: Competency #{context.competency_id}",
            description=f"Operational statistical scenario evaluating compliance for competency #{context.competency_id}. Context: {context.learning_objective}",
            scenario_type=scenario_type,
            competency_id=context.competency_id,
            subskill_id=context.subskill_id,
            role_id=context.role_id,
            difficulty=difficulty,
            version=1,
            source="MOSPI_OPERATIONAL",
            provenance="[SANDBOX DATA]",
            status="ACTIVE",
            expected_outcomes=expected_outcomes,
            evaluation_rubric=rubric,
            metadata={
                "generator": "DeterministicScenarioGenerator",
                "generator_version": "1.0",
                "learning_objective": context.learning_objective,
            },
        )


class LLMScenarioGenerator:
    """Replaceable boundary for external/future LLM scenario generation."""

    def __init__(self, available: bool = False):
        self.available = available

    def generate(self, context: ScenarioGenerationContext) -> ScenarioCandidate:
        if not self.available:
            raise RuntimeError("LLMScenarioGenerator service is unavailable.")
        # When implemented by ML/LLM team, structured candidate is returned
        return DeterministicScenarioGenerator().generate(context)


def validate_scenario_candidate(db: Session, candidate: ScenarioCandidate) -> None:
    """Backend validation for candidate scenarios before persistence."""
    if not candidate.title or len(candidate.title.strip()) < 3:
        raise CandidateValidationError("Scenario title must be at least 3 characters.")

    if not candidate.description or len(candidate.description.strip()) < 5:
        raise CandidateValidationError("Scenario description must be at least 5 characters.")

    if candidate.difficulty.lower() not in SUPPORTED_DIFFICULTIES:
        raise CandidateValidationError(f"Invalid difficulty '{candidate.difficulty}'. Supported: {SUPPORTED_DIFFICULTIES}")

    if candidate.scenario_type.upper() not in SUPPORTED_SCENARIO_TYPES:
        raise CandidateValidationError(f"Invalid scenario type '{candidate.scenario_type}'. Supported: {SUPPORTED_SCENARIO_TYPES}")

    # Taxonomy validation
    comp = db.get(Competency, candidate.competency_id)
    if not comp:
        raise CandidateValidationError(f"Referenced competency_id={candidate.competency_id} does not exist.")

    if candidate.subskill_id is not None:
        sub = db.get(SubSkill, candidate.subskill_id)
        if not sub:
            raise CandidateValidationError(f"Referenced subskill_id={candidate.subskill_id} does not exist.")
        if sub.competency_id != candidate.competency_id:
            raise CandidateValidationError(
                f"SubSkill {candidate.subskill_id} belongs to competency {sub.competency_id}, not {candidate.competency_id}."
            )

    if candidate.role_id is not None:
        role = db.get(Role, candidate.role_id)
        if not role:
            raise CandidateValidationError(f"Referenced role_id={candidate.role_id} does not exist.")
        # Verify role-competency relationship if role competencies exist
        rc_exists = db.execute(
            select(RoleCompetency).where(
                RoleCompetency.role_id == candidate.role_id,
                RoleCompetency.competency_id == candidate.competency_id,
            )
        ).first()
        # Note: if there are mapped competencies for this role, verify membership
        total_role_comps = db.execute(
            select(RoleCompetency).where(RoleCompetency.role_id == candidate.role_id)
        ).scalars().all()
        if total_role_comps and not rc_exists:
            raise CandidateValidationError(
                f"Competency {candidate.competency_id} is not mapped to Role {candidate.role_id}."
            )

    # Validate outcomes and rubric
    if not candidate.expected_outcomes or len(candidate.expected_outcomes) == 0:
        raise CandidateValidationError("Scenario must provide at least one expected outcome.")

    if not isinstance(candidate.evaluation_rubric, dict):
        raise CandidateValidationError("Evaluation rubric must be a structured JSON object.")

    if "passing_threshold" not in candidate.evaluation_rubric:
        raise CandidateValidationError("Evaluation rubric must specify passing_threshold.")

    # Duplicate detection against active scenarios with same title and competency
    existing = db.execute(
        select(Scenario).where(
            Scenario.title == candidate.title,
            Scenario.competency_id == candidate.competency_id,
            Scenario.status == "ACTIVE",
        )
    ).first()
    if existing:
        raise CandidateValidationError(f"Duplicate scenario already exists for competency {candidate.competency_id} with title '{candidate.title}'.")


@dataclass
class ScenarioEvaluationResult:
    score: float
    max_score: float
    normalized_score: float
    passed: bool
    competency_evidence: dict[str, Any]
    subskill_evidence: dict[str, Any]
    rubric_results: dict[str, Any]
    evaluator_type: str = "DETERMINISTIC"
    evaluator_version: str = "v1.0"
    confidence: float = 1.0
    review_required: bool = False
    provenance: str = "[SANDBOX DATA]"
    feedback: str = "Evaluation completed."


class ScenarioEvaluator(Protocol):
    def evaluate(self, scenario: Scenario, response: dict[str, Any]) -> ScenarioEvaluationResult:
        """Evaluate learner response against scenario rubric."""
        ...


class DeterministicScenarioEvaluator:
    """Deterministic, reproducible evaluator for operational scenarios."""

    def evaluate(self, scenario: Scenario, response: dict[str, Any]) -> ScenarioEvaluationResult:
        rubric = scenario.get_rubric()
        threshold = rubric.get("passing_threshold", 0.70)
        criteria = rubric.get("criteria", [])

        # Response payload analysis
        answer_text = str(response.get("answer", "")).lower()
        decisions = response.get("decisions", [])
        if isinstance(decisions, list):
            answer_text += " " + " ".join(str(d).lower() for d in decisions)

        total_score = 0.0
        max_score = 1.0
        rubric_results = {}

        if not criteria:
            # Fallback simple scoring
            matched = len(answer_text) > 20
            total_score = 0.85 if matched else 0.40
            rubric_results["default"] = {"score": total_score, "matched": matched}
        else:
            for crit in criteria:
                name = crit.get("name", "criterion")
                weight = crit.get("weight", 1.0 / len(criteria))
                req_keyword = crit.get("required_keyword", "").lower()

                crit_pass = (req_keyword in answer_text) if req_keyword else (len(answer_text) > 10)
                crit_score = weight if crit_pass else 0.0
                total_score += crit_score
                rubric_results[name] = {
                    "weight": weight,
                    "awarded": crit_score,
                    "required_keyword": req_keyword,
                    "matched": crit_pass,
                }

        normalized_score = max(0.0, min(1.0, total_score / max_score))
        passed = normalized_score >= threshold
        review_required = 0.65 <= normalized_score < threshold

        competency_evidence = {
            "competency_id": scenario.competency_id,
            "scenario_id": scenario.scenario_id,
            "normalized_score": round(normalized_score, 4),
            "passed": passed,
        }
        subskill_evidence = {
            "subskill_id": scenario.subskill_id,
            "normalized_score": round(normalized_score, 4),
            "passed": passed,
        } if scenario.subskill_id else {}

        return ScenarioEvaluationResult(
            score=round(total_score, 4),
            max_score=max_score,
            normalized_score=round(normalized_score, 4),
            passed=passed,
            competency_evidence=competency_evidence,
            subskill_evidence=subskill_evidence,
            rubric_results=rubric_results,
            evaluator_type="DETERMINISTIC",
            evaluator_version="v1.0",
            confidence=0.95,
            review_required=review_required,
            provenance="[SANDBOX DATA]",
            feedback=f"Deterministic evaluation completed with score {normalized_score:.2%}.",
        )


def validate_evaluation_result(result: ScenarioEvaluationResult) -> None:
    """Validate evaluator output before allowing evidence emission or state changes."""
    if result.max_score <= 0:
        raise EvaluationValidationError("Evaluator max_score must be strictly positive.")

    if not (0.0 <= result.normalized_score <= 1.0):
        raise EvaluationValidationError(f"Evaluator normalized_score {result.normalized_score} out of bounds [0.0, 1.0].")

    if not (0.0 <= result.score <= result.max_score + 1e-4):
        raise EvaluationValidationError(f"Evaluator raw score {result.score} exceeds max_score {result.max_score}.")

    if not isinstance(result.passed, bool):
        raise EvaluationValidationError("Evaluator passed indicator must be a boolean.")

    if not isinstance(result.rubric_results, dict):
        raise EvaluationValidationError("Evaluator rubric_results must be a dictionary.")

    if not (0.0 <= result.confidence <= 1.0):
        raise EvaluationValidationError(f"Evaluator confidence {result.confidence} out of bounds [0.0, 1.0].")
