"""The orchestrator: a LangGraph StateGraph wiring the specialized agents.

Pipeline:
    parse -> research(company, tool-using) -> match -> skill_gap -> tailor
          -> review --(pass)--> finalize
                      --(fail, retries left)--> revise -> tailor   (loop)
                      --(fail, out of retries)--> escalate -> finalize (human-in-loop)

The review->revise->tailor loop with a retry budget is what makes this an
agentic system rather than a one-shot pipeline.

Compiled graphs use a SQLite checkpointer so every run is durable and
inspectable by thread_id (survives process restarts).
"""
from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents import (
    company_research_agent,
    job_parser_agent,
    resume_match_agent,
    reviewer_agent,
    skill_gap_agent,
    tailor_agent,
)
from app.checkpointing import get_checkpointer
from app.config import settings
from app.state import AgentState


def _revise(state: AgentState) -> dict:
    """Bump the revision counter before looping back to the tailor."""
    count = state.get("revision_count", 0) + 1
    return {"revision_count": count, "trace": [f"[loop] revision {count} requested"]}


def _escalate(state: AgentState) -> dict:
    """Out of retries: flag for human review and stop looping."""
    return {
        "needs_human_review": True,
        "trace": ["[loop] max revisions reached -> human review"],
    }


def _finalize(state: AgentState) -> dict:
    """Terminal node; ensure the human-review flag is always present."""
    return {"needs_human_review": state.get("needs_human_review", False)}


AUTHENTICITY_THRESHOLD = 85


def _is_acceptable(review) -> bool:
    """Accept a draft only when it invents nothing and is well-grounded.

    Enforced here (not just trusted from the model's `passed` flag) so the
    accept/loop decision is deterministic and testable.
    """
    return (
        review.passed
        or (not review.exaggerations and review.authenticity_score >= AUTHENTICITY_THRESHOLD)
    )


def _route_after_review(state: AgentState) -> str:
    review = state["review"]
    if _is_acceptable(review):
        return "finalize"
    max_revisions = state.get("max_revisions", settings.max_revisions)
    if state.get("revision_count", 0) < max_revisions:
        return "revise"
    return "escalate"


def build_graph(*, persistent: bool = True):
    g = StateGraph(AgentState)

    g.add_node("job_parser", job_parser_agent)
    g.add_node("company_research", company_research_agent)
    g.add_node("resume_match", resume_match_agent)
    g.add_node("skill_gap", skill_gap_agent)
    g.add_node("tailor", tailor_agent)
    g.add_node("reviewer", reviewer_agent)
    g.add_node("revise", _revise)
    g.add_node("escalate", _escalate)
    g.add_node("finalize", _finalize)

    g.add_edge(START, "job_parser")
    g.add_edge("job_parser", "company_research")
    g.add_edge("company_research", "resume_match")
    g.add_edge("resume_match", "skill_gap")
    g.add_edge("skill_gap", "tailor")
    g.add_edge("tailor", "reviewer")

    g.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {"finalize": "finalize", "revise": "revise", "escalate": "escalate"},
    )
    g.add_edge("revise", "tailor")  # the self-correction loop
    g.add_edge("escalate", "finalize")
    g.add_edge("finalize", END)

    if persistent:
        return g.compile(checkpointer=get_checkpointer())
    return g.compile()


# Guardrail on input size: keeps context windows and cost bounded for very
# long resumes/postings while staying generous enough for real documents.
MAX_INPUT_CHARS = 16_000


def _prepare_input(text: str, label: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError(f"{label} is empty. Provide some {label.lower()} text.")
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS] + "\n...[truncated]"
    return text


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def run_application(
    resume_text: str,
    job_text: str,
    *,
    thread_id: str | None = None,
    persistent: bool = True,
    callbacks: list[Any] | None = None,
) -> AgentState:
    """Run the full graph and return final state (checkpointed when persistent)."""
    resume_text = _prepare_input(resume_text, "Resume")
    job_text = _prepare_input(job_text, "Job posting")
    thread_id = thread_id or str(uuid.uuid4())

    graph = build_graph(persistent=persistent)
    initial: AgentState = {
        "resume_text": resume_text,
        "job_text": job_text,
        "revision_count": 0,
        "max_revisions": settings.max_revisions,
        "needs_human_review": False,
        "thread_id": thread_id,
        "trace": [],
    }

    config: dict[str, Any] = {}
    if persistent:
        config.update(_thread_config(thread_id))
    if callbacks:
        config["callbacks"] = callbacks

    result = graph.invoke(initial, config=config or None)

    # Ensure callers always see the thread key even if a node overwrote state.
    if isinstance(result, dict):
        result["thread_id"] = thread_id
    return result


def get_application_state(thread_id: str) -> AgentState | None:
    """Load the latest checkpointed state for a thread (None if unknown)."""
    graph = build_graph(persistent=True)
    snapshot = graph.get_state(_thread_config(thread_id))
    if not snapshot or not snapshot.values:
        return None
    values = dict(snapshot.values)
    values["thread_id"] = thread_id
    return values  # type: ignore[return-value]
