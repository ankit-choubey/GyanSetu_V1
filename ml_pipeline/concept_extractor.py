import json
import os
from openai import OpenAI

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_PRIMARY


PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "concept_prompt.txt"
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
    """Load the concept extraction prompt template."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def _validate_concept_shape(concept):
    """Validate the structure of one extracted concept."""
    if not isinstance(concept, dict):
        return False

    required_fields = {"concept", "description", "subskills"}

    if not required_fields.issubset(concept.keys()):
        return False

    if not isinstance(concept["concept"], str):
        return False

    if not isinstance(concept["description"], str):
        return False

    if not isinstance(concept["subskills"], list):
        return False

    if not all(isinstance(skill, str) for skill in concept["subskills"]):
        return False

    return True


def parse_concept_response(response_text):
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

    concepts = json.loads(response_text)

    if not isinstance(concepts, list):
        raise ValueError("Concept response must be a JSON array.")

    for concept in concepts:
        if not _validate_concept_shape(concept):
            raise ValueError(
                "Invalid concept structure returned by the model."
            )

    return concepts


def extract_concepts(content):
    """
    Extract concepts and subskills from learning content.

    Args:
        content (str): Learning material text.

    Returns:
        list: Validated concepts.
    """
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Content must be a non-empty string.")

    prompt_template = _load_prompt()
    prompt = prompt_template.replace("{content}", content)

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

    return parse_concept_response(response_text)