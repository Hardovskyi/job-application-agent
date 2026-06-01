"""Reviewer / Guardrail agent: the system's safety + quality gate.

It judges whether a draft is honest (grounded in the resume) and well-written.
Its verdict drives the conditional edge that either accepts the draft or loops
back to the tailoring agent with feedback.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas import ReviewResult
from app.state import AgentState

SYSTEM = (
    "You are a strict integrity reviewer. Compare the draft application materials "
    "against the candidate's ACTUAL resume.\n"
    "- List in `exaggerations` every claim NOT supported by the resume "
    "(invented skills, inflated metrics, fake roles, tools never mentioned).\n"
    "- List purely stylistic/quality nits in `issues` (these alone must NOT fail "
    "the draft).\n"
    "- Set `authenticity_score` = how grounded-in-the-resume the draft is (0-100).\n"
    "Decision rule for `passed`: set passed=TRUE if and only if there are ZERO "
    "exaggerations AND authenticity_score >= 85. Otherwise passed=FALSE. "
    "Minor wording preferences must never block a pass. Provide concise, "
    "actionable feedback the writer can use to fix any flagged exaggerations."
)


def reviewer_agent(state: AgentState) -> dict:
    draft = state["draft"]
    content = (
        f"CANDIDATE RESUME\n{state['resume_text']}\n\n"
        f"DRAFT BULLETS\n{draft.tailored_bullets}\n\n"
        f"DRAFT COVER LETTER\n{draft.cover_letter}\n\n"
        f"DRAFT RECRUITER MESSAGE\n{draft.recruiter_message}"
    )
    llm = get_llm().with_structured_output(ReviewResult)
    review: ReviewResult = llm.invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=content)]
    )
    verdict = "PASS" if review.passed else "REVISE"
    return {
        "review": review,
        "trace": [
            f"[reviewer] {verdict} (authenticity={review.authenticity_score}, "
            f"{len(review.exaggerations)} exaggeration(s))"
        ],
    }
