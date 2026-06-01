"""Provider-agnostic LLM factory.

A single entry point (`get_llm`) returns a LangChain chat model for whichever
provider is configured. This lets every agent stay provider-independent and
makes "I built it to swap between OpenAI, Claude, and a local model" a real
talking point rather than a hardcoded dependency.
"""
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
            raise RuntimeError(
                "LLM_PROVIDER=openai but no OpenAI key found. Set OPENAI_API_KEY "
                "in .env (or enter one in the app sidebar)."
            )
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but no Anthropic key found. Set "
                "ANTHROPIC_API_KEY in .env (or enter one in the app sidebar)."
            )
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
                "LLM_PROVIDER=ollama requires `pip install langchain-ollama` "
                "and a running `ollama serve`."
            ) from exc
        return ChatOllama(model=settings.ollama_model, temperature=temperature)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Use 'openai', 'anthropic', or 'ollama'."
    )
