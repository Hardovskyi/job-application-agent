"""Company Research agent: a true tool-using (ReAct) sub-agent.

Unlike the other nodes (which make a single structured call), this agent runs
its own reason-act loop: it decides what to search for, calls the web_search
tool, reads results, and may search again before summarizing. This is the
"genuine agency + tool use" piece of the system.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm
from app.state import AgentState
from app.tools import web_search

SYSTEM = (
    "You are a company-research agent helping tailor a job application. "
    "Use the web_search tool to find what the company does, its products, tech "
    "stack, culture, and any recent news. Make at most 2-3 focused searches, "
    "then write a concise 4-6 sentence briefing the application can be tailored "
    "to. If searches return nothing useful, say so briefly and stop."
)


def company_research_agent(state: AgentState) -> dict:
    parsed = state["parsed_job"]
    if not parsed.company or parsed.company.lower() == "unknown":
        return {
            "company_research": "No identifiable company; skipped external research.",
            "trace": ["[company_research] skipped (unknown company)"],
        }

    agent = create_react_agent(get_llm(), tools=[web_search], prompt=SYSTEM)
    query = (
        f"Research the company '{parsed.company}' for a '{parsed.title}' role. "
        "What do they do, what is their tech stack, and what do they value?"
    )
    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    briefing = result["messages"][-1].content
    return {
        "company_research": briefing,
        "trace": [f"[company_research] briefing prepared for {parsed.company}"],
    }
