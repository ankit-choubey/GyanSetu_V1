"""
ML-001 — Groq API setup verification.

Scope: confirm GROQ_API_KEY loads correctly from .env and a single chat
completion request succeeds. Deliberately does NOT touch MCQ generation,
validation, or any other ML-002+ logic.

Run:
    python ml_pipeline/test_groq_connection.py
"""
import sys

from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL_PRIMARY
from openai import OpenAI


def main() -> int:
    if not GROQ_API_KEY:
        print("FAIL: GROQ_API_KEY is not set.")
        print("Copy ml_pipeline/.env.example to ml_pipeline/.env and fill in your real key.")
        return 1

    client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[{"role": "user", "content": "Reply with exactly one word: hello"}],
        )
    except Exception as e:
        # Deliberately not printing the key or any request headers here.
        print(f"FAIL: request to Groq raised an exception: {e}")
        return 1

    content = response.choices[0].message.content.strip()
    print(f"Model replied: {content!r}")

    if "hello" in content.lower():
        print("PASS: ML-001 connectivity check succeeded.")
        return 0
    else:
        print("PARTIAL: request succeeded but reply didn't contain 'hello' — inspect manually.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
