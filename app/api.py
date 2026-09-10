"""FastAPI deployment for the job-application agent.

Run locally:
    uvicorn app.api:app --reload --port 8000

Endpoints:
    GET  /health
    POST /v1/applications          — run the multi-agent pipeline
    GET  /v1/applications          — list saved application history
    GET  /v1/applications/{id}     — saved history row by DB id
    GET  /v1/threads/{thread_id}   — load LangGraph checkpointed state
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db import get_application, list_applications, save_application
from app.graph import get_application_state, run_application

app = FastAPI(
    title="AI Job Application Agent API",
    description="REST API for the LangGraph multi-agent job-application pipeline.",
    version="1.0.0",
)


class ApplicationRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, description="Plain-text résumé")
    job_text: str = Field(..., min_length=1, description="Job posting text")
    thread_id: str | None = Field(
        default=None,
        description="Optional thread id to continue / overwrite a checkpointed run",
    )
    save: bool = Field(default=True, description="Also persist a history row in SQLite")


def _dump(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def _serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "thread_id": state.get("thread_id"),
        "parsed_job": _dump(state.get("parsed_job")),
        "company_research": state.get("company_research"),
        "match": _dump(state.get("match")),
        "skill_gaps": _dump(state.get("skill_gaps")),
        "draft": _dump(state.get("draft")),
        "review": _dump(state.get("review")),
        "revision_count": state.get("revision_count", 0),
        "needs_human_review": bool(state.get("needs_human_review")),
        "trace": state.get("trace", []),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/applications")
def create_application(body: ApplicationRequest) -> dict[str, Any]:
    try:
        state = run_application(
            body.resume_text,
            body.job_text,
            thread_id=body.thread_id,
            persistent=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface LLM/config errors cleanly
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    application_id = None
    if body.save:
        application_id = save_application(state)

    payload = _serialize_state(state)
    payload["application_id"] = application_id
    return payload


@app.get("/v1/applications")
def list_saved_applications() -> list[dict[str, Any]]:
    rows = list_applications()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "company": row["company"],
            "title": row["title"],
            "match_score": row["match_score"],
            "needs_human_review": bool(row["needs_human_review"]),
        }
        for row in rows
    ]


@app.get("/v1/applications/{application_id}")
def get_saved_application(application_id: int) -> dict[str, Any]:
    row = get_application(application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)


@app.get("/v1/threads/{thread_id}")
def get_thread(thread_id: str) -> dict[str, Any]:
    state = get_application_state(thread_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return _serialize_state(state)
