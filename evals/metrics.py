"""Eval scoring + token/cost tracking for the job-application agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.graph import _is_acceptable

# Approximate list prices for gpt-4o-mini (USD / 1M tokens). Override via env if needed.
DEFAULT_INPUT_USD_PER_1M = 0.15
DEFAULT_OUTPUT_USD_PER_1M = 0.60


@dataclass
class UsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimated_cost_usd(
        self,
        input_per_1m: float = DEFAULT_INPUT_USD_PER_1M,
        output_per_1m: float = DEFAULT_OUTPUT_USD_PER_1M,
    ) -> float:
        return (
            self.input_tokens * input_per_1m / 1_000_000
            + self.output_tokens * output_per_1m / 1_000_000
        )


class UsageTracker(BaseCallbackHandler):
    """Collects token usage from LangChain LLM ends (OpenAI usage_metadata)."""

    def __init__(self) -> None:
        super().__init__()
        self.totals = UsageTotals()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:  # noqa: ARG002
        self.totals.llm_calls += 1
        added = False
        for gens in response.generations or []:
            for gen in gens:
                msg = getattr(gen, "message", None)
                meta = getattr(msg, "usage_metadata", None) if msg is not None else None
                if isinstance(meta, dict) and (
                    meta.get("input_tokens") is not None or meta.get("output_tokens") is not None
                ):
                    self.totals.input_tokens += int(meta.get("input_tokens") or 0)
                    self.totals.output_tokens += int(meta.get("output_tokens") or 0)
                    added = True
        if added:
            return
        llm_output = response.llm_output or {}
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        if usage:
            self.totals.input_tokens += int(
                usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            )
            self.totals.output_tokens += int(
                usage.get("completion_tokens") or usage.get("output_tokens") or 0
            )


@dataclass
class CaseMetrics:
    case_id: str
    structured_ok: bool
    title_ok: bool
    skill_recall: float
    score_in_range: bool
    first_pass_success: bool
    final_success: bool
    research_ok: bool | None  # None = skipped (unknown company)
    authenticity: int | None
    revision_count: int
    needs_human_review: bool
    latency_s: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    error: str | None = None


def skill_recall(found: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0
    found_lc = " ".join(found).lower()
    hits = sum(1 for e in expected if e.lower() in found_lc)
    return hits / len(expected)


def title_matches(parsed_title: str | None, expected_contains: str) -> bool:
    if not parsed_title or not expected_contains:
        return False
    return all(word in parsed_title.lower() for word in expected_contains.lower().split())


def research_succeeded(state: dict[str, Any]) -> bool | None:
    """True if research ran usefully; False if failed; None if skipped."""
    research = (state.get("company_research") or "").strip()
    trace = " ".join(state.get("trace") or [])
    if "skipped (unknown company)" in trace or research.startswith("No identifiable company"):
        return None
    if not research:
        return False
    failure_markers = (
        "web search unavailable",
        "no results found",
        "proceed without external research",
    )
    low = research.lower()
    if any(m in low for m in failure_markers) and len(research) < 120:
        return False
    return len(research) >= 40


def score_case(case_id: str, state: dict[str, Any], spec: dict[str, Any], *, latency_s: float, usage: UsageTotals) -> CaseMetrics:
    parsed = state.get("parsed_job")
    match = state.get("match")
    gaps = state.get("skill_gaps")
    draft = state.get("draft")
    review = state.get("review")
    revision_count = int(state.get("revision_count") or 0)
    needs_human = bool(state.get("needs_human_review"))

    all_skills: list[str] = []
    if parsed is not None:
        all_skills = list(parsed.required_skills) + list(parsed.preferred_skills) + list(parsed.tools)

    structured_ok = all(x is not None for x in (parsed, match, gaps, draft, review))
    title_ok = title_matches(
        getattr(parsed, "title", None),
        spec.get("expected_title_contains", ""),
    )
    recall = skill_recall(all_skills, spec.get("expected_required_skills", []))
    score_ok = (
        match is not None
        and spec.get("min_match_score", 0) <= match.match_score <= spec.get("max_match_score", 100)
    )

    acceptable = review is not None and _is_acceptable(review)
    first_pass = revision_count == 0 and acceptable and not needs_human
    final_ok = acceptable and not needs_human

    return CaseMetrics(
        case_id=case_id,
        structured_ok=structured_ok,
        title_ok=title_ok,
        skill_recall=round(recall, 3),
        score_in_range=score_ok,
        first_pass_success=first_pass,
        final_success=final_ok,
        research_ok=research_succeeded(state),
        authenticity=getattr(review, "authenticity_score", None) if review else None,
        revision_count=revision_count,
        needs_human_review=needs_human,
        latency_s=round(latency_s, 2),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        estimated_cost_usd=round(usage.estimated_cost_usd(), 5),
    )


@dataclass
class SuiteSummary:
    n_cases: int
    first_pass_success_rate: float
    final_success_rate: float
    structured_output_success_rate: float
    research_success_rate: float | None
    avg_skill_recall: float
    title_ok_rate: float
    score_in_range_rate: float
    avg_latency_s: float
    p95_latency_s: float
    avg_cost_usd: float
    total_cost_usd: float
    total_tokens: int
    errors: int
    case_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_cases": self.n_cases,
            "first_pass_success_rate": self.first_pass_success_rate,
            "final_success_rate": self.final_success_rate,
            "structured_output_success_rate": self.structured_output_success_rate,
            "research_success_rate": self.research_success_rate,
            "avg_skill_recall": self.avg_skill_recall,
            "title_ok_rate": self.title_ok_rate,
            "score_in_range_rate": self.score_in_range_rate,
            "avg_latency_s": self.avg_latency_s,
            "p95_latency_s": self.p95_latency_s,
            "avg_cost_usd": self.avg_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "errors": self.errors,
            "case_ids": self.case_ids,
        }


def _pct(ok: int, n: int) -> float:
    return round((ok / n) * 100.0, 1) if n else 0.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return round(ordered[idx], 2)


def summarize(rows: list[CaseMetrics]) -> SuiteSummary:
    n = len(rows)
    research_rows = [r for r in rows if r.research_ok is not None]
    research_ok = sum(1 for r in research_rows if r.research_ok)
    latencies = [r.latency_s for r in rows]
    costs = [r.estimated_cost_usd for r in rows]
    return SuiteSummary(
        n_cases=n,
        first_pass_success_rate=_pct(sum(1 for r in rows if r.first_pass_success), n),
        final_success_rate=_pct(sum(1 for r in rows if r.final_success), n),
        structured_output_success_rate=_pct(sum(1 for r in rows if r.structured_ok), n),
        research_success_rate=_pct(research_ok, len(research_rows)) if research_rows else None,
        avg_skill_recall=round(sum(r.skill_recall for r in rows) / n, 3) if n else 0.0,
        title_ok_rate=_pct(sum(1 for r in rows if r.title_ok), n),
        score_in_range_rate=_pct(sum(1 for r in rows if r.score_in_range), n),
        avg_latency_s=round(sum(latencies) / n, 2) if n else 0.0,
        p95_latency_s=_p95(latencies),
        avg_cost_usd=round(sum(costs) / n, 5) if n else 0.0,
        total_cost_usd=round(sum(costs), 5),
        total_tokens=sum(r.input_tokens + r.output_tokens for r in rows),
        errors=sum(1 for r in rows if r.error),
        case_ids=[r.case_id for r in rows],
    )
