"""Pydantic schemas for structured agent outputs.

Every agent that produces structured data returns one of these models via
LangChain's `.with_structured_output(...)`. This guarantees valid, typed JSON
between agents instead of free-text parsing — a core requirement of reliable
agent systems.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedJob(BaseModel):
    """Structured representation of a job posting."""

    title: str = Field(description="Job title")
    company: str = Field(description="Hiring company name, or 'Unknown'")
    seniority: str = Field(
        description="Seniority level, e.g. Intern/Junior/Mid/Senior/Lead"
    )
    min_years_experience: int = Field(
        default=0, description="Minimum years of experience required (0 if unspecified)"
    )
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(
        default_factory=list, description="Named tools/technologies/frameworks"
    )
    responsibilities: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    """How well the resume matches the parsed job."""

    match_score: int = Field(ge=0, le=100, description="Overall fit score 0-100")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    rationale: str = Field(description="Brief explanation of the score")


class SkillGapResult(BaseModel):
    """Prioritized gaps and what to learn."""

    critical_gaps: list[str] = Field(
        default_factory=list, description="Must-have skills the candidate lacks"
    )
    nice_to_have_gaps: list[str] = Field(default_factory=list)
    learning_suggestions: list[str] = Field(
        default_factory=list,
        description="Concrete, actionable suggestions to close the gaps",
    )


class ApplicationDraft(BaseModel):
    """The candidate-facing deliverables."""

    tailored_bullets: list[str] = Field(
        default_factory=list,
        description="Rewritten resume bullets aligned to the job. Must be grounded "
        "in the candidate's actual resume — no invented experience.",
    )
    cover_letter: str = Field(description="Short, tailored cover letter")
    recruiter_message: str = Field(
        description="Brief LinkedIn/email message to a recruiter"
    )


class ReviewResult(BaseModel):
    """Guardrail agent's verdict on a draft."""

    passed: bool = Field(description="True if the draft is honest and high quality")
    authenticity_score: int = Field(
        ge=0, le=100, description="How grounded-in-the-resume the draft is (0-100)"
    )
    exaggerations: list[str] = Field(
        default_factory=list,
        description="Specific claims that exaggerate or invent experience",
    )
    issues: list[str] = Field(
        default_factory=list, description="Other quality/tone problems"
    )
    feedback: str = Field(
        description="Actionable feedback the tailoring agent can use to revise"
    )
