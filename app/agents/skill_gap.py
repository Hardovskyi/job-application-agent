"""Skill Gap agent: prioritizes missing skills and suggests how to learn them."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas import SkillGapResult
from app.state import AgentState

SYSTEM = (
    "You are a career coach. Given the job's missing skills and the candidate's "
    "resume, separate critical (must-have) gaps from nice-to-have ones, and give "
    "concrete, realistic learning suggestions (resources, mini-projects). Do not "
    "suggest lying or padding the resume."
)


def skill_gap_agent(state: AgentState) -> dict:
    parsed = state["parsed_job"]
    match = state["match"]
    llm = get_llm().with_structured_output(SkillGapResult)
    content = (
        f"Job required skills: {parsed.required_skills}\n"
        f"Job preferred skills: {parsed.preferred_skills}\n"
        f"Identified missing skills: {match.missing_skills}\n\n"
        f"RESUME\n{state['resume_text']}"
    )
    gaps: SkillGapResult = llm.invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=content)]
    )
    return {
        "skill_gaps": gaps,
        "trace": [f"[skill_gap] {len(gaps.critical_gaps)} critical gap(s)"],
    }
