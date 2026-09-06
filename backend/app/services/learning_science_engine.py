from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LearningDeficit(str, Enum):
    RECALL_FAILURE = "Recall failure"
    FORGETTING = "Forgetting"
    CONFUSION_MISCONCEPTION = "Confusion/Misconception"
    APPLICATION_GAP = "Application gap"
    KNOWLEDGE_GAP = "Knowledge gap"


class PedagogicalStrategy(str, Enum):
    RETRIEVAL_PRACTICE = "Retrieval practice"
    SPACED_REPETITION = "Spaced repetition"
    CONTRASTIVE_EXPLANATION = "Contrastive explanation"
    SCENARIO_VIRTUAL_LAB = "Scenario/Virtual Lab"
    DIRECT_INSTRUCTION = "Direct instruction"


@dataclass(frozen=True)
class LearningScienceInput:
    deficit: str | LearningDeficit
    competency_id: int | None = None
    subskill_id: int | None = None


@dataclass(frozen=True)
class LearningScienceRecommendation:
    deficit: str
    strategy: str | None
    known: bool
    competency_id: int | None = None
    subskill_id: int | None = None


_STRATEGY_BY_DEFICIT: dict[str, PedagogicalStrategy] = {
    LearningDeficit.RECALL_FAILURE.value.casefold(): PedagogicalStrategy.RETRIEVAL_PRACTICE,
    LearningDeficit.FORGETTING.value.casefold(): PedagogicalStrategy.SPACED_REPETITION,
    LearningDeficit.CONFUSION_MISCONCEPTION.value.casefold(): PedagogicalStrategy.CONTRASTIVE_EXPLANATION,
    LearningDeficit.APPLICATION_GAP.value.casefold(): PedagogicalStrategy.SCENARIO_VIRTUAL_LAB,
    LearningDeficit.KNOWLEDGE_GAP.value.casefold(): PedagogicalStrategy.DIRECT_INSTRUCTION,
}


def select_pedagogical_strategy(
    request: LearningScienceInput,
) -> LearningScienceRecommendation:
    """Map an explicit deficit to a strategy without classifying or inferring it."""
    deficit = request.deficit.value if isinstance(request.deficit, LearningDeficit) else str(request.deficit).strip()
    strategy = _STRATEGY_BY_DEFICIT.get(deficit.casefold())
    return LearningScienceRecommendation(
        deficit=deficit,
        strategy=strategy.value if strategy else None,
        known=strategy is not None,
        competency_id=request.competency_id,
        subskill_id=request.subskill_id,
    )