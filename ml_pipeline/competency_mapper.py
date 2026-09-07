import json
import os
from openai import OpenAI

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_PRIMARY


PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "competency_prompt.txt"
)


_client = None


def _get_client():
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment or ml_pipeline/.env")
        _client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    return _client


def _load_prompt():
    """Load the competency mapping prompt template."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def _validate_mapping_shape(mapping):
    """Validate the structure of one competency mapping."""
    if not isinstance(mapping, dict):
        return False

    required_fields = {
        "concept",
        "competency",
        "subskills",
        "confidence",
        "rationale"
    }

    if not required_fields.issubset(mapping.keys()):
        return False

    if not isinstance(mapping["concept"], str):
        return False

    if not isinstance(mapping["competency"], str):
        return False

    if not isinstance(mapping["subskills"], list):
        return False

    if not all(isinstance(skill, str) for skill in mapping["subskills"]):
        return False

    if not isinstance(mapping["confidence"], (int, float)):
        return False

    if not 0 <= mapping["confidence"] <= 1:
        return False

    if not isinstance(mapping["rationale"], str):
        return False

    return True


def parse_competency_response(response_text):
    """Parse and validate the JSON response from the LLM."""
    response_text = response_text.strip()

    # Remove accidental markdown code fences.
    if response_text.startswith("```"):
        lines = response_text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response_text = "\n".join(lines).strip()

    mappings = json.loads(response_text)

    if not isinstance(mappings, list):
        raise ValueError("Competency response must be a JSON array.")

    for mapping in mappings:
        if not _validate_mapping_shape(mapping):
            raise ValueError(
                "Invalid competency mapping structure returned by the model."
            )

    return mappings


def validate_canonical_mapping(mapping: dict) -> dict:
    """
    Validates mapping against canonical 40 competencies and 160 subskills.
    Marks status as 'VERIFIED' or 'REVIEW_REQUIRED'.
    """
    from ml_pipeline.canonical_taxonomy import (
        CANONICAL_COMPETENCIES,
        CANONICAL_SUBSKILLS,
        is_canonical_competency,
        is_canonical_subskill,
    )

    enriched = dict(mapping)
    comp = enriched.get("competency", "").strip()
    subskills = enriched.get("subskills", [])

    if is_canonical_competency(comp):
        enriched["canonical_verified"] = True
        enriched["domain"] = CANONICAL_COMPETENCIES[comp]
        # Validate subskills
        valid_sub = [s for s in subskills if is_canonical_subskill(comp, s)]
        enriched["canonical_subskills"] = valid_sub
        enriched["status"] = "VERIFIED"
    else:
        enriched["canonical_verified"] = False
        enriched["domain"] = None
        enriched["canonical_subskills"] = []
        enriched["status"] = "REVIEW_REQUIRED"
        enriched["review_reason"] = f"Competency '{comp}' is not one of the 40 canonical competencies."

    return enriched



def map_competencies(concepts):
    """
    Map extracted concepts and subskills to competencies.

    Args:
        concepts (list): Extracted concepts from concept_extractor.py.

    Returns:
        list: Validated competency mappings.
    """
    if not isinstance(concepts, list) or not concepts:
        raise ValueError("Concepts must be a non-empty list.")

    prompt_template = _load_prompt()

    concepts_json = json.dumps(
        concepts,
        ensure_ascii=False,
        indent=2
    )

    prompt = prompt_template.replace(
        "{concepts}",
        concepts_json
    )

    response = _get_client().chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    response_text = response.choices[0].message.content

    return parse_competency_response(response_text)