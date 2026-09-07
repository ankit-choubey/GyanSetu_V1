"""
Deterministic grounding checks for generated scenario assessments.

The validator does not use an LLM. It performs conservative checks to
catch obvious unsupported content before a scenario is accepted.

Contract:
    validate_scenario_grounding(scenario, source_content) -> list[str]

An empty list means no obvious grounding violations were detected.
"""

from __future__ import annotations

import re
from typing import Any


# Patterns that commonly introduce unsupported factual claims.
# These checks are deliberately conservative. They are intended to
# flag suspicious content for review, not to prove semantic grounding.
_SUSPICIOUS_PATTERNS = (
    r"\b\d+(?:\.\d+)?\s*%",
    r"\b\d+(?:\.\d+)?\s*(?:million|billion|thousand|crore|lakh)\b",
    r"\b(?:three|four|five|six|seven|eight|nine|ten)\s+states?\b",
    r"\burban\b",
    r"\brural\b",
)


def _collect_text(value: Any) -> str:
    """Recursively collect textual values from a scenario object."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return " ".join(
            _collect_text(item)
            for item in value.values()
        )

    if isinstance(value, list):
        return " ".join(
            _collect_text(item)
            for item in value
        )

    return ""


def _normalise(text: str) -> str:
    """Normalise text for simple comparison."""
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def validate_scenario_grounding(
    scenario: dict,
    source_content: str,
) -> list[str]:
    """
    Perform conservative grounding checks.

    Args:
        scenario:
            Generated scenario dictionary.

        source_content:
            Original training material supplied to the generator.

    Returns:
        A list of human-readable grounding issues.

    Notes:
        This is NOT a semantic proof that every statement is grounded.
        It is a first safety layer intended to catch obvious unsupported
        facts, values, and contextual claims.
    """
    issues: list[str] = []

    if not isinstance(scenario, dict):
        return ["scenario must be a dictionary"]

    if not isinstance(source_content, str) or not source_content.strip():
        return ["source_content must not be empty"]

    scenario_text = _collect_text(scenario)
    source_text = _normalise(source_content)

    if not scenario_text.strip():
        issues.append("scenario contains no textual content")
        return issues

    # Check suspicious factual/contextual claims.
    for pattern in _SUSPICIOUS_PATTERNS:
        matches = re.findall(
            pattern,
            scenario_text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            normalised_match = _normalise(match)

            if normalised_match not in source_text:
                issues.append(
                    "possible unsupported factual claim: "
                    f"'{match}'"
                )

    # Check scenario context specifically.
    context = scenario.get("scenario", {}).get("context")

    if isinstance(context, str):
        context_normalised = _normalise(context)

        if context_normalised and context_normalised not in source_text:
            # Generated scenarios are expected to rephrase source material,
            # so this is only a review warning and not a hard rejection.
            issues.append(
                "scenario context contains generated wording that "
                "is not directly present in the source material; "
                "semantic grounding review is recommended"
            )

    return issues