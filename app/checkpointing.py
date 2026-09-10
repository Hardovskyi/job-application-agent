"""LangGraph SQLite checkpointer keyed by thread_id."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

CHECKPOINT_DB = Path(__file__).resolve().parent.parent / "checkpoints.db"

_conn: sqlite3.Connection | None = None
_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    global _conn, _checkpointer
    if _checkpointer is None:
        _conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
        _checkpointer = SqliteSaver(_conn)
        _checkpointer.setup()
    return _checkpointer
