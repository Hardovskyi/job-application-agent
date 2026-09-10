"""CI-friendly unit tests — no LLM API keys required."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.graph import (
    AUTHENTICITY_THRESHOLD,
    _is_acceptable,
    _prepare_input,
    _route_after_review,
    build_graph,
)
from app.schemas import ReviewResult


class TestPrepareInput:
    def test_strips_and_accepts(self):
        assert _prepare_input("  hello  ", "Resume") == "hello"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _prepare_input("   ", "Resume")

    def test_truncates_long_input(self):
        text = "x" * 20_000
        out = _prepare_input(text, "Job posting")
        assert out.endswith("...[truncated]")
        assert len(out) < 20_000


class TestReviewRouting:
    def _state(self, review: ReviewResult, revision_count: int = 0, max_revisions: int = 2):
        return {
            "review": review,
            "revision_count": revision_count,
            "max_revisions": max_revisions,
        }

    def test_passed_goes_to_finalize(self):
        review = ReviewResult(
            passed=True,
            authenticity_score=90,
            exaggerations=[],
            issues=[],
            feedback="ok",
        )
        assert _route_after_review(self._state(review)) == "finalize"

    def test_high_authenticity_no_exaggerations_accepted(self):
        review = ReviewResult(
            passed=False,
            authenticity_score=AUTHENTICITY_THRESHOLD,
            exaggerations=[],
            issues=["tone"],
            feedback="minor",
        )
        assert _is_acceptable(review) is True
        assert _route_after_review(self._state(review)) == "finalize"

    def test_fail_with_retries_revises(self):
        review = ReviewResult(
            passed=False,
            authenticity_score=40,
            exaggerations=["invented internship"],
            issues=[],
            feedback="remove claim",
        )
        assert _route_after_review(self._state(review, revision_count=0)) == "revise"

    def test_fail_out_of_retries_escalates(self):
        review = ReviewResult(
            passed=False,
            authenticity_score=40,
            exaggerations=["invented internship"],
            issues=[],
            feedback="remove claim",
        )
        assert (
            _route_after_review(self._state(review, revision_count=2, max_revisions=2))
            == "escalate"
        )


class TestGraphCompile:
    def test_compiles_without_checkpointer(self):
        graph = build_graph(persistent=False)
        assert graph is not None


class TestAPI:
    def test_health(self):
        from app.api import app

        client = TestClient(app)
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_create_rejects_empty_body(self):
        from app.api import app

        client = TestClient(app)
        res = client.post(
            "/v1/applications",
            json={"resume_text": "", "job_text": "Engineer"},
        )
        assert res.status_code == 422
