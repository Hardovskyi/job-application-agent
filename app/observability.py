"""LangSmith tracing helpers."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROJECT = "job-application-agent"


def configure_tracing() -> bool:
    """Enable LangSmith when LANGSMITH_API_KEY (or LANGCHAIN_API_KEY) is set."""
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ.setdefault(
            "LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT)
        )
        return True

    os.environ["LANGSMITH_TRACING"] = "false"
    return False


def tracing_status() -> str:
    if configure_tracing():
        project = os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT)
        return f"LangSmith tracing: ON (project='{project}')"
    return "LangSmith tracing: OFF"
