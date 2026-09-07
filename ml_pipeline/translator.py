"""
ml_pipeline/translator.py — Multilingual Translation Pipeline for Official Statistics.
GyanSetu - Phase 6.3

Provides domain-accurate translation between English and Indian regional languages
(Hindi, Tamil, Telugu, Bengali, Marathi, etc.) with technical terminology preservation.
Supports translation of plain text, MCQ items, and practical scenarios.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_FAST

_GLOSSARY_PATH = os.path.join(
    os.path.dirname(__file__),
    "terminology_glossary.json",
)

_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "translation_prompt.txt",
)

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "en": "English",
}

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured; translation unavailable.")
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )
    return _client


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class StatisticalTranslator:
    """
    Bilingual translation engine with domain terminology preservation.
    """

    def __init__(self, glossary_path: Optional[str] = None):
        self.glossary_path = glossary_path or _GLOSSARY_PATH
        self.glossary: Dict[str, Any] = {}
        self._load_glossary()

    def _load_glossary(self) -> None:
        if os.path.exists(self.glossary_path):
            try:
                with open(self.glossary_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.glossary = data.get("terms", {})
            except Exception:
                self.glossary = {}

    def get_glossary_guidance(self, target_lang: str) -> str:
        """Extracts bullet points of technical terms for the prompt."""
        lines = []
        lang_key = target_lang.lower()
        for term, trans_dict in self.glossary.items():
            if lang_key in trans_dict:
                equiv = trans_dict[lang_key]
                lines.append(f"- {term}: {equiv}")
        return "\n".join(lines) if lines else "Preserve official statistical terms in English where appropriate."

    def translate_text(
        self,
        text: str,
        target_language: str = "hi",
        source_language: str = "en",
    ) -> str:
        """
        Translates plain text into the target language.
        """
        if not text or not text.strip():
            return text

        target_code = target_language.lower()
        if target_code not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported target language '{target_language}'. "
                f"Supported: {sorted(SUPPORTED_LANGUAGES.keys())}"
            )

        if target_code == source_language.lower():
            return text

        if not GROQ_API_KEY:
            # Fallback when offline
            return text

        target_name = SUPPORTED_LANGUAGES[target_code]
        source_name = SUPPORTED_LANGUAGES.get(source_language.lower(), "English")
        glossary_guidance = self.get_glossary_guidance(target_code)

        with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        prompt = template.format(
            source_language=source_name,
            target_language=target_name,
            glossary_guidance=glossary_guidance,
            content=text,
        )

        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = response.choices[0].message.content or ""
        return _strip_code_fences(raw)

    def translate_mcq(self, mcq: Dict[str, Any], target_language: str = "hi") -> Dict[str, Any]:
        """
        Translates all text elements of an MCQ while strictly preserving its structure,
        option keys, and answer integrity.
        """
        result = dict(mcq)
        q_key = "question_text" if "question_text" in mcq else "question"
        if q_key in mcq:
            result[q_key] = self.translate_text(mcq[q_key], target_language=target_language)

        if "explanation" in mcq and mcq["explanation"]:
            result["explanation"] = self.translate_text(mcq["explanation"], target_language=target_language)

        options = mcq.get("options")
        if isinstance(options, list):
            translated_options = [
                self.translate_text(opt, target_language=target_language) if isinstance(opt, str) else opt
                for opt in options
            ]
            result["options"] = translated_options
        elif isinstance(options, dict):
            translated_options = {
                k: self.translate_text(v, target_language=target_language) if isinstance(v, str) else v
                for k, v in options.items()
            }
            result["options"] = translated_options

        result["target_language"] = target_language
        return result

    def translate_scenario(self, scenario: Dict[str, Any], target_language: str = "hi") -> Dict[str, Any]:
        """
        Translates scenario text fields (title, context, question, instructions)
        while preserving rubric, numbers, and evaluation criteria.
        """
        result = dict(scenario)

        text_fields = ["title", "context", "scenario_text", "question", "task_question", "instructions"]
        for field in text_fields:
            if field in scenario and scenario[field]:
                result[field] = self.translate_text(str(scenario[field]), target_language=target_language)

        result["target_language"] = target_language
        return result


_default_translator: Optional[StatisticalTranslator] = None


def get_translator() -> StatisticalTranslator:
    global _default_translator
    if _default_translator is None:
        _default_translator = StatisticalTranslator()
    return _default_translator


def translate(text: str, target_language: str = "hi") -> str:
    """Convenience translation function."""
    return get_translator().translate_text(text, target_language=target_language)


def translate_mcq(mcq: Dict[str, Any], target_language: str = "hi") -> Dict[str, Any]:
    """Convenience MCQ translation function."""
    return get_translator().translate_mcq(mcq, target_language=target_language)


def translate_scenario(scenario: Dict[str, Any], target_language: str = "hi") -> Dict[str, Any]:
    """Convenience scenario translation function."""
    return get_translator().translate_scenario(scenario, target_language=target_language)
