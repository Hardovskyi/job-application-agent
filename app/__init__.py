"""AI Job Application Agent — a multi-agent LangGraph system."""

__version__ = "0.1.0"

# Load .env and configure LangSmith tracing as early as possible, before any
# LangChain/LangGraph objects are created.
from app.observability import configure_tracing  # noqa: E402

configure_tracing()
