"""Resume Match agent: scores resume vs. parsed job requirements."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas import MatchResult
from app.state import AgentState

SYSTEM = (
    "You are a technical recruiter. Compare the candidate's resume against the "
    "job's required and preferred skills. Be honest and evidence-based: a skill "
    "counts as 'matched' only if the resume actually supports it. Give a 0-100 "
    "fit score with a short rationale."
)


def resume_match_agent(state: AgentState) -> dict:
    parsed = state["parsed_job"]
    llm = get_llm().with_structured_output(MatchResult)
    content = (
        f"JOB\nTitle: {parsed.title}\n"
        f"Required skills: {parsed.required_skills}\n"
        f"Preferred skills: {parsed.preferred_skills}\n"
        f"Tools: {parsed.tools}\n"
        f"Min years: {parsed.min_years_experience}\n\n"
        f"RESUME\n{state['resume_text']}"
    )
    match: MatchResult = llm.invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=content)]
    )
    return {
        "match": match,
        "trace": [f"[resume_match] score={match.match_score}"],
    }
