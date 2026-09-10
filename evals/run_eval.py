"""Evaluation harness with resume-ready reliability metrics.

Measures (over a labeled suite of gold + synthetic job postings):
  - first_pass_success_rate   : accepted with 0 reviewer revisions
  - final_success_rate        : accepted after the bounded reviewer loop
  - structured_output_success : all agent Pydantic outputs present
  - research_success_rate     : company-research tool path produced a briefing
  - title / skill_recall / score_in_range checks
  - avg + p95 latency, estimated API cost/run

Examples:
  python -m evals.run_eval --suite gold
  python -m evals.run_eval --suite full --limit 60
  python -m evals.run_eval --suite full --limit 100 --out evals/results/latest.json
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from app.graph import run_application
from app.observability import tracing_status
from app.resume import load_text
from evals.case_bank import case_spec, load_cases
from evals.metrics import CaseMetrics, UsageTracker, score_case, summarize

EVAL_DIR = Path(__file__).resolve().parent
RESUME = EVAL_DIR.parent / "data" / "sample_resume.md"
RESULTS_DIR = EVAL_DIR / "results"


def _run_one(case, resume_text: str) -> CaseMetrics:
    tracker = UsageTracker()
    t0 = time.perf_counter()
    try:
        state = run_application(
            resume_text,
            case.job_text,
            persistent=False,
            callbacks=[tracker],
        )
        latency = time.perf_counter() - t0
        return score_case(
            case.id,
            state,
            case_spec(case),
            latency_s=latency,
            usage=tracker.totals,
        )
    except Exception as exc:  # noqa: BLE001 — capture per-case failures for the suite
        latency = time.perf_counter() - t0
        return CaseMetrics(
            case_id=case.id,
            structured_ok=False,
            title_ok=False,
            skill_recall=0.0,
            score_in_range=False,
            first_pass_success=False,
            final_success=False,
            research_ok=False,
            authenticity=None,
            revision_count=0,
            needs_human_review=True,
            latency_s=round(latency, 2),
            input_tokens=tracker.totals.input_tokens,
            output_tokens=tracker.totals.output_tokens,
            estimated_cost_usd=round(tracker.totals.estimated_cost_usd(), 5),
            error=f"{type(exc).__name__}: {exc}",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run job-application-agent evaluation suite")
    parser.add_argument(
        "--suite",
        choices=("gold", "synthetic", "full"),
        default="gold",
        help="gold=3 labeled JDs (CI); full=gold+synthetic (~63); synthetic=generated only",
    )
    parser.add_argument("--limit", type=int, default=None, help="Cap number of cases")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON summary+rows (default: evals/results/latest.json)",
    )
    args = parser.parse_args()

    print(tracing_status())
    cases = load_cases(suite=args.suite, limit=args.limit)
    print(f"Running {len(cases)} case(s) from suite={args.suite!r}")
    resume_text = load_text(RESUME)

    rows: list[CaseMetrics] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case.id} ...", flush=True)
        row = _run_one(case, resume_text)
        status = "OK" if row.final_success and not row.error else ("ERR" if row.error else "FAIL")
        print(
            f"    {status} first={row.first_pass_success} final={row.final_success} "
            f"struct={row.structured_ok} lat={row.latency_s}s cost=${row.estimated_cost_usd}",
            flush=True,
        )
        rows.append(row)

    summary = summarize(rows)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": args.suite,
        "summary": summary.as_dict(),
        "cases": [asdict(r) for r in rows],
    }

    out = args.out or (RESULTS_DIR / "latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n=== Suite summary ===")
    print(json.dumps(summary.as_dict(), indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
