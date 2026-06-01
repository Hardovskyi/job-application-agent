"""Resume Tailoring agent: produces the candidate-facing deliverables.

On a retry, it receives the reviewer's feedback and must address it — this is
the "act" half of the self-correction loop.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas import ApplicationDraft
from app.state import AgentState

SYSTEM = (
    "You are an expert resume writer. Produce tailored, honest application "
    "materials grounded ONLY in the candidate's actual resume. Rewrite existing "
    "experience to align with the job; never invent roles, skills, metrics, or "
    "achievements. Keep a confident, human, non-AI-sounding tone."
)


def tailor_agent(state: AgentState) -> dict:
    parsed = state["parsed_job"]
    match = state["match"]
    research = state.get("company_research", "")
    prior_review = state.get("review")

    content = (
        f"JOB\nTitle: {parsed.title} @ {parsed.company}\n"
        f"Required: {parsed.required_skills}\nPreferred: {parsed.preferred_skills}\n"
        f"Responsibilities: {parsed.responsibilities}\n\n"
        f"COMPANY BRIEFING\n{research}\n\n"
        f"MATCH\nScore {match.match_score}; matched {match.matched_skills}; "
        f"missing {match.missing_skills}\n\n"
        f"CANDIDATE RESUME\n{state['resume_text']}\n\n"
        "Produce: 3-5 tailored resume bullets, a short cover letter, and a brief "
        "recruiter message."
    )

    # Inject reviewer feedback on revisions.
    if prior_review is not None and not prior_review.passed:
        content += (
            "\n\nREVISION REQUIRED. A reviewer flagged the previous draft.\n"
            f"Exaggerations to remove: {prior_review.exaggerations}\n"
            f"Other issues: {prior_review.issues}\n"
            f"Feedback: {prior_review.feedback}\n"
            "Rewrite to fully address this while staying truthful to the resume."
        )

    # First pass can be a little creative; revisions should converge, so we
    # drop the temperature once the reviewer has given corrective feedback.
    revision = state.get("revision_count", 0)
    temperature = 0.4 if revision == 0 else 0.1
    llm = get_llm(temperature=temperature).with_structured_output(ApplicationDraft)
    draft: ApplicationDraft = llm.invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=content)]
    )
    attempt = revision + 1
    return {
        "draft": draft,
        "trace": [f"[tailor] draft attempt #{attempt}"],
    }
