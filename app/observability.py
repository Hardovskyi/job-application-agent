"""LangSmith tracing setup.

LangChain/LangGraph auto-instrument every LLM and graph call when the right
environment variables are present. We enable tracing automatically *only* when
a LANGSMITH_API_KEY is set, so the project runs cleanly with or without it.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

# Load .env into the process environment so LangChain (which reads os.environ
# directly) can see LANGSMITH_* and provider keys.
load_dotenv()

DEFAULT_PROJECT = "job-application-agent"


def configure_tracing() -> bool:
    """Turn LangSmith tracing on iff an API key is available.

    Returns True if tracing is active, False otherwise.
    """
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ.setdefault(
            "LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT)
        )
        return True

    # No key: make sure tracing is off to avoid upload warnings.
    os.environ["LANGSMITH_TRACING"] = "false"
    return False


def tracing_status() -> str:
    if configure_tracing():
        project = os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT)
        return f"LangSmith tracing: ON (project='{project}')"
    return "LangSmith tracing: OFF (set LANGSMITH_API_KEY in .env to enable)"
