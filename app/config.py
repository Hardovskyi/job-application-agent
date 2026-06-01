"""Centralized, environment-driven configuration.

Keeping settings in one typed object makes the system easy to reconfigure
(swap LLM providers, tune the review loop) without touching agent code.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM provider selection
    llm_provider: str = "openai"  # openai | anthropic | ollama
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    ollama_model: str = "llama3.1"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Tools
    tavily_api_key: str | None = None

    # Agent behavior
    max_revisions: int = 2


settings = Settings()
