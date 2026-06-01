"""Job Parser agent: turns a raw posting into structured data."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas import ParsedJob
from app.state import AgentState

SYSTEM = (
    "You are a precise job-posting analyst. Extract structured information from "
    "the posting. Only include skills/tools explicitly mentioned or strongly "
    "implied. If the company is not named, use 'Unknown'."
)


def job_parser_agent(state: AgentState) -> dict:
    llm = get_llm().with_structured_output(ParsedJob)
    parsed: ParsedJob = llm.invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Job posting:\n\n{state['job_text']}"),
        ]
    )
    return {
        "parsed_job": parsed,
        "trace": [f"[job_parser] parsed '{parsed.title}' @ {parsed.company}"],
    }
