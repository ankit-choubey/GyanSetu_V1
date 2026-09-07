from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ScenarioBankRecord:
    competency_name: str
    subskill_name: str
    scenario_output: Mapping[str, Any]
    source_reference: str


SCENARIO_BANK: tuple[ScenarioBankRecord, ...] = (
    ScenarioBankRecord(
        competency_name="Sampling Design",
        subskill_name="Stratified sampling",
        source_reference=(
            "gyansetu-scenario:sandbox-sampling:"
            "Sampling-Design:Stratified-sampling:v1"
        ),
        scenario_output={
            "scenario": {
                "title": "Stratified Sampling Planning Scenario",
                "context": (
                    "A survey team is planning a sample. The population "
                    "can be divided into homogeneous subgroups before "
                    "sampling."
                ),
                "context_data": {
                    "planning_stage": "before sampling",
                    "population_structure": "homogeneous subgroups",
                },
                "task": {
                    "question": (
                        "Which sampling approach should the team apply, "
                        "and how should it use the subgroups? Explain "
                        "your reasoning."
                    ),
                    "response_type": "structured_text",
                    "instructions": (
                        "Identify the approach and justify how the "
                        "subgroups are used."
                    ),
                },
            },
            "expected_reasoning": {
                "key_points": [
                    "Identify stratified sampling.",
                    "Recognize that the population is divided into "
                    "homogeneous subgroups before sampling.",
                    "Explain the choice using the stated population "
                    "structure.",
                ],
                "reference_answer": (
                    "Stratified sampling is appropriate because the "
                    "population can be divided into homogeneous "
                    "subgroups before sampling."
                ),
            },
            "rubric": {
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "description": "Identifies stratified sampling.",
                        "max_score": 4,
                    },
                    {
                        "criterion_id": "C2",
                        "description": (
                            "Explains division into homogeneous subgroups."
                        ),
                        "max_score": 3,
                    },
                    {
                        "criterion_id": "C3",
                        "description": "Justifies the application to the scenario.",
                        "max_score": 3,
                    },
                ],
                "max_score": 10,
            },
            "difficulty": "medium",
            "cognitive_level": "application",
            "source": {
                "content_reference": "sandbox-sampling-methodology-v1",
            },
        },
    ),
)