"""Evaluation harness.

Runs the agent over a labeled set of job descriptions and reports metrics that
matter for an agent system's *reliability*, not just vibe:

  - structured_ok      : every agent returned valid structured output
  - skill_recall       : fraction of expected required-skills the parser found
  - title_ok           : parsed title matches expectation
  - score_in_range     : match score is plausible (not 0 or 100 nonsense)
  - guardrail_ran      : reviewer produced a verdict
  - authenticity       : reviewer's authenticity score (grounding check)

Run with:  python -m evals.run_eval
"""
from __future__ import annotations

import json
from pathlib import Path

from app.graph import run_application
from app.observability import tracing_status
from app.resume import load_text

EVAL_DIR = Path(__file__).resolve().parent
JD_DIR = EVAL_DIR / "job_descriptions"
RESUME = EVAL_DIR.parent / "data" / "sample_resume.md"


def _skill_recall(found: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0
    found_lc = " ".join(found).lower()
    hits = sum(1 for e in expected if e.lower() in found_lc)
    return hits / len(expected)


def main() -> None:
    print(tracing_status())
    expected = json.loads((EVAL_DIR / "expected_outputs.json").read_text("utf-8"))
    resume_text = load_text(RESUME)

    results = []
    for jd_file, spec in expected.items():
        job_text = load_text(JD_DIR / jd_file)
        state = run_application(resume_text, job_text)

        parsed = state.get("parsed_job")
        match = state.get("match")
        review = state.get("review")

        all_skills = []
        if parsed:
            all_skills = parsed.required_skills + parsed.preferred_skills + parsed.tools

        recall = _skill_recall(all_skills, spec.get("expected_required_skills", []))
        # Fair, order-independent title check: every word of the expected title
        # should appear in the parsed title (handles "Junior AI Engineer" etc.).
        expected_title = spec.get("expected_title_contains", "").lower()
        title_ok = parsed is not None and all(
            word in parsed.title.lower() for word in expected_title.split()
        )
        score_ok = (
            match is not None
            and spec.get("min_match_score", 0) <= match.match_score <= spec.get("max_match_score", 100)
        )

        results.append(
            {
                "jd": jd_file,
                "structured_ok": all(x is not None for x in (parsed, match, review)),
                "skill_recall": round(recall, 2),
                "title_ok": title_ok,
                "score_in_range": score_ok,
                "guardrail_ran": review is not None,
                "authenticity": getattr(review, "authenticity_score", None),
                "needs_human_review": state.get("needs_human_review"),
            }
        )

    print(json.dumps(results, indent=2))

    n = len(results)
    if n:
        avg_recall = sum(r["skill_recall"] for r in results) / n
        pct_structured = sum(r["structured_ok"] for r in results) / n * 100
        print(f"\nAvg skill recall: {avg_recall:.2f}")
        print(f"Structured-output success: {pct_structured:.0f}%")


if __name__ == "__main__":
    main()
