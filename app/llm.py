"""Return a LangChain chat model for the configured provider."""
from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import settings


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install langchain-ollama and run `ollama serve` for LLM_PROVIDER=ollama."
            ) from exc
        return ChatOllama(model=settings.ollama_model, temperature=temperature)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Expected openai, anthropic, or ollama."
    )
