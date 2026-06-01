"""Shared graph state passed between agents.

LangGraph threads this TypedDict through every node. Each agent reads the
fields it needs and writes back its structured result, which is how the
specialized agents "hand off" work to each other.
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from app.schemas import (
    ApplicationDraft,
    MatchResult,
    ParsedJob,
    ReviewResult,
    SkillGapResult,
)


def append(left: list, right: list) -> list:
    """Reducer that accumulates the trace log across nodes."""
    return (left or []) + (right or [])


class AgentState(TypedDict, total=False):
    # Inputs
    resume_text: str
    job_text: str

    # Agent outputs (filled in as the graph runs)
    parsed_job: ParsedJob
    company_research: str
    match: MatchResult
    skill_gaps: SkillGapResult
    draft: ApplicationDraft
    review: ReviewResult

    # Self-correction loop control
    revision_count: int
    max_revisions: int
    needs_human_review: bool

    # Observability: a human-readable trace of which agent did what
    trace: Annotated[list[str], append]
