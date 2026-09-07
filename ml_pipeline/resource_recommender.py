from __future__ import annotations

from typing import Any


def rank_resources(
    resources: list[dict[str, Any]],
    competency_id: int | None = None,
    subskill_id: int | None = None,
    gap_reason: str | None = None,
) -> list[dict[str, Any]]:
    """
    Rank normalized learning resources against a learner's competency gap.

    ML owns relevance scoring only.
    Backend owns canonical IDs, authorization, persistence, and provider data.
    """

    ranked: list[dict[str, Any]] = []

    for resource in resources:
        resource_id = resource.get("resource_id")

        if resource_id is None:
            continue

        resource_competency = resource.get("competency_id")
        resource_subskill = resource.get("subskill_id")

        if (
            subskill_id is not None
            and resource_subskill == subskill_id
        ):
            score = 1.0
            reason = "Directly matches the identified subskill gap."

        elif (
            competency_id is not None
            and resource_competency == competency_id
        ):
            score = 0.8
            reason = "Matches the identified competency."

        elif (
            resource_competency is None
            and resource_subskill is None
        ):
            score = 0.4
            reason = "Provides general learning support."

        else:
            continue

        if resource.get("availability") not in (None, "AVAILABLE"):
            continue

        ranked.append(
            {
                "resource_id": resource_id,
                "relevance_score": score,
                "reason": reason,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["relevance_score"],
            item["resource_id"],
        )
    )

    return ranked