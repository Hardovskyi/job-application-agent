"""Shared LangGraph state for the agent pipeline."""
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
    return (left or []) + (right or [])


class AgentState(TypedDict, total=False):
    resume_text: str
    job_text: str

    parsed_job: ParsedJob
    company_research: str
    match: MatchResult
    skill_gaps: SkillGapResult
    draft: ApplicationDraft
    review: ReviewResult

    revision_count: int
    max_revisions: int
    needs_human_review: bool

    thread_id: str
    trace: Annotated[list[str], append]
