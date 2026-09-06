"""
Central config for the ML/AI pipeline.
Loads from ml_pipeline/.env — never commit that file (see GIT_WORKFLOW.md §3, §7).
"""
import os
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL_PRIMARY = os.environ.get("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile")
GROQ_MODEL_FAST = os.environ.get("GROQ_MODEL_FAST", "llama-3.1-8b-instant")

CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./ml_pipeline/vector_store/chroma_db")

if not GROQ_API_KEY:
    # Don't raise at import time — lets teammates import this module for
    # non-Groq work (e.g. document_processor.py) without a key set yet.
    # Anything that actually calls Groq should check this explicitly.
    pass
