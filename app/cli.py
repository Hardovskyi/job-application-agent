"""Command-line runner.

Example:
    python -m app.cli --resume data/sample_resume.md --job data/sample_job.txt
"""
from __future__ import annotations

import argparse

from app.db import save_application
from app.graph import run_application
from app.observability import tracing_status
from app.resume import load_text


def _print_section(title: str, body: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    print(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Job Application Agent")
    parser.add_argument("--resume", required=True, help="Path to resume (.txt/.md/.pdf)")
    parser.add_argument("--job", required=True, help="Path to job posting (.txt/.md)")
    parser.add_argument("--no-save", action="store_true", help="Skip saving to the DB")
    args = parser.parse_args()

    resume_text = load_text(args.resume)
    job_text = load_text(args.job)

    print(tracing_status())
    print("Running multi-agent pipeline...\n")
    state = run_application(resume_text, job_text)

    _print_section("AGENT TRACE", "\n".join(state.get("trace", [])))

    match = state.get("match")
    if match:
        _print_section(
            "MATCH",
            f"Score: {match.match_score}/100\n"
            f"Matched: {', '.join(match.matched_skills)}\n"
            f"Missing: {', '.join(match.missing_skills)}\n"
            f"Rationale: {match.rationale}",
        )

    gaps = state.get("skill_gaps")
    if gaps:
        _print_section(
            "SKILL GAPS",
            f"Critical: {', '.join(gaps.critical_gaps)}\n"
            f"Nice-to-have: {', '.join(gaps.nice_to_have_gaps)}\n"
            f"Learn: {'; '.join(gaps.learning_suggestions)}",
        )

    draft = state.get("draft")
    if draft:
        _print_section("TAILORED BULLETS", "\n".join(f"- {b}" for b in draft.tailored_bullets))
        _print_section("COVER LETTER", draft.cover_letter)
        _print_section("RECRUITER MESSAGE", draft.recruiter_message)

    review = state.get("review")
    if review:
        outcome = (
            "FLAGGED FOR HUMAN REVIEW"
            if state.get("needs_human_review")
            else "ACCEPTED"
        )
        _print_section(
            "REVIEW (GUARDRAIL)",
            f"Outcome: {outcome}\n"
            f"Authenticity: {review.authenticity_score}/100\n"
            f"Exaggerations: {review.exaggerations}\n"
            f"Feedback: {review.feedback}",
        )

    if state.get("needs_human_review"):
        print("\n[!] Draft did not fully pass guardrails — flagged for human review.")

    if not args.no_save:
        app_id = save_application(state)
        print(f"\nSaved application #{app_id} to the database.")


if __name__ == "__main__":
    main()
