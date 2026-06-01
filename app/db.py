"""Lightweight SQLite persistence for application runs.

Stores each completed run so the Streamlit dashboard can track applications
over time. JSON columns keep it schema-simple for a portfolio project.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.state import AgentState

DB_PATH = Path(__file__).resolve().parent.parent / "applications.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                company TEXT,
                title TEXT,
                match_score INTEGER,
                needs_human_review INTEGER,
                draft_json TEXT,
                full_state_json TEXT
            )
            """
        )


def _model_dump(obj):
    return obj.model_dump() if hasattr(obj, "model_dump") else obj


def save_application(state: AgentState) -> int:
    init_db()
    parsed = state.get("parsed_job")
    match = state.get("match")
    draft = state.get("draft")

    serializable = {
        k: _model_dump(v)
        for k, v in state.items()
    }

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO applications
                (created_at, company, title, match_score, needs_human_review,
                 draft_json, full_state_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                getattr(parsed, "company", None),
                getattr(parsed, "title", None),
                getattr(match, "match_score", None),
                1 if state.get("needs_human_review") else 0,
                json.dumps(_model_dump(draft)) if draft else None,
                json.dumps(serializable, default=str),
            ),
        )
        return cur.lastrowid


def list_applications() -> list[sqlite3.Row]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, company, title, match_score, needs_human_review "
            "FROM applications ORDER BY id DESC"
        ).fetchall()
    return rows
