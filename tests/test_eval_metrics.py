"""Unit tests for eval metrics + case bank (no LLM calls)."""
from __future__ import annotations

from app.schemas import (
    ApplicationDraft,
    MatchResult,
    ParsedJob,
    ReviewResult,
    SkillGapResult,
)
from evals.case_bank import load_cases
from evals.metrics import (
    UsageTotals,
    research_succeeded,
    score_case,
    skill_recall,
    summarize,
    title_matches,
)


def test_case_bank_sizes():
    gold = load_cases(suite="gold")
    assert len(gold) == 3
    full = load_cases(suite="full")
    assert len(full) == 63
    limited = load_cases(suite="full", limit=10)
    assert len(limited) == 10


def test_skill_recall_and_title():
    assert skill_recall(["Python", "FastAPI"], ["Python", "Git"]) == 0.5
    assert title_matches("Junior AI Engineer", "AI Engineer") is True
    assert title_matches("Data Analyst", "Computer Vision") is False


def test_research_skipped_vs_ok():
    assert research_succeeded({"company_research": "No identifiable company; skipped", "trace": ["[company_research] skipped (unknown company)"]}) is None
    assert research_succeeded({"company_research": "Acme builds LLM tools for developers and cares about evals. " * 2, "trace": ["prepared"]}) is True


def test_score_case_first_vs_final():
    parsed = ParsedJob(title="Junior AI Engineer", company="Acme AI", seniority="Junior", required_skills=["Python", "Git"])
    match = MatchResult(match_score=70, matched_skills=["Python"], missing_skills=[], rationale="ok")
    gaps = SkillGapResult()
    draft = ApplicationDraft(tailored_bullets=["Built X"], cover_letter="Hi", recruiter_message="Hello")
    review = ReviewResult(passed=True, authenticity_score=90, exaggerations=[], issues=[], feedback="ok")

    state = {
        "parsed_job": parsed,
        "match": match,
        "skill_gaps": gaps,
        "draft": draft,
        "review": review,
        "revision_count": 0,
        "needs_human_review": False,
        "company_research": "Acme builds developer tools for reliable LLM features and evaluation.",
        "trace": ["[company_research] briefing prepared for Acme AI"],
    }
    spec = {
        "expected_title_contains": "AI Engineer",
        "expected_required_skills": ["Python", "Git"],
        "min_match_score": 25,
        "max_match_score": 90,
    }
    row = score_case("t1", state, spec, latency_s=1.5, usage=UsageTotals(100, 50))
    assert row.first_pass_success is True
    assert row.final_success is True
    assert row.structured_ok is True

    state["revision_count"] = 1
    row2 = score_case("t2", state, spec, latency_s=2.0, usage=UsageTotals())
    assert row2.first_pass_success is False
    assert row2.final_success is True


def test_summarize_rates():
    # Minimal fake rows via score_case path already covered; build two CaseMetrics via summarize inputs
    from evals.metrics import CaseMetrics

    rows = [
        CaseMetrics(
            case_id="a",
            structured_ok=True,
            title_ok=True,
            skill_recall=1.0,
            score_in_range=True,
            first_pass_success=True,
            final_success=True,
            research_ok=True,
            authenticity=90,
            revision_count=0,
            needs_human_review=False,
            latency_s=10.0,
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.01,
        ),
        CaseMetrics(
            case_id="b",
            structured_ok=True,
            title_ok=False,
            skill_recall=0.5,
            score_in_range=True,
            first_pass_success=False,
            final_success=True,
            research_ok=False,
            authenticity=88,
            revision_count=1,
            needs_human_review=False,
            latency_s=20.0,
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.02,
        ),
    ]
    s = summarize(rows)
    assert s.n_cases == 2
    assert s.first_pass_success_rate == 50.0
    assert s.final_success_rate == 100.0
    assert s.p95_latency_s == 20.0
