"""Web search tool for the company-research agent.

This is a *real* tool the LLM can choose to call: it decides what to search
for and when. Uses Tavily when a key is available (built for agents), and
falls back to DuckDuckGo so the project runs with zero API keys.
"""
from __future__ import annotations

from langchain_core.tools import tool

from app.config import settings


def _tavily_search(query: str, max_results: int) -> str:
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    resp = client.search(query=query, max_results=max_results)
    results = resp.get("results", [])
    if not results:
        return "No results found."
    return "\n\n".join(
        f"- {r.get('title', 'Untitled')}\n  {r.get('content', '').strip()}\n  ({r.get('url', '')})"
        for r in results
    )


def _duckduckgo_search(query: str, max_results: int) -> str:
    try:
        from ddgs import DDGS
    except ImportError:  # older package name
        from duckduckgo_search import DDGS  # type: ignore

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    return "\n\n".join(
        f"- {r.get('title', 'Untitled')}\n  {r.get('body', '').strip()}\n  ({r.get('href', '')})"
        for r in results
    )


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date information about a company, role, or topic.

    Use this to learn what a company does, its tech stack, recent news, culture,
    or values — anything useful for tailoring a job application.
    """
    try:
        if settings.tavily_api_key:
            return _tavily_search(query, max_results)
        return _duckduckgo_search(query, max_results)
    except Exception as exc:  # tool failures should not crash the graph
        return f"Web search unavailable ({type(exc).__name__}: {exc}). Proceed without external research."
