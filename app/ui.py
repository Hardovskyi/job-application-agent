"""Streamlit dashboard for the AI Job Application Agent.

Run with:  streamlit run app/ui.py
"""
from __future__ import annotations

import os

import streamlit as st

from app.db import list_applications, save_application
from app.graph import run_application
from app.observability import tracing_status
from app.resume import load_text

st.set_page_config(page_title="AI Job Application Agent", page_icon="🤖", layout="wide")
st.title("🤖 AI Job Application Agent")
st.caption("Multi-agent system: parse → research → match → skill-gap → tailor → review loop")

# Sidebar: optional bring-your-own-key (lets a public demo run on the visitor's
# key instead of the owner's, so deploying is safe and free to host).
with st.sidebar:
    st.subheader("Settings")
    user_key = st.text_input(
        "OpenAI API key (optional)",
        type="password",
        help="Used only for your session. Leave blank to use the server's key.",
    )
    if user_key:
        os.environ["OPENAI_API_KEY"] = user_key
    has_key = bool(user_key or os.getenv("OPENAI_API_KEY"))
    if not has_key:
        st.warning("No OpenAI key configured. Enter one above to run the agents.")
    st.info(tracing_status())

tab_run, tab_history = st.tabs(["New application", "History"])

with tab_run:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your resume")
        resume_file = st.file_uploader("Upload resume (.txt/.md/.pdf)", type=["txt", "md", "pdf"])
        resume_text = st.text_area("...or paste it", height=260, key="resume_text")
    with col2:
        st.subheader("Job posting")
        job_text = st.text_area("Paste the job description", height=320, key="job_text")

    if st.button("Run agents", type="primary"):
        # Resolve resume text from upload or textarea.
        resolved_resume = resume_text
        if resume_file is not None:
            import tempfile
            from pathlib import Path

            suffix = Path(resume_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(resume_file.getbuffer())
                tmp_path = tmp.name
            resolved_resume = load_text(tmp_path)

        if not resolved_resume.strip() or not job_text.strip():
            st.error("Please provide both a resume and a job posting.")
        elif not has_key:
            st.error("Add an OpenAI API key in the sidebar first.")
        else:
            try:
                with st.spinner("Agents working (parse → research → match → tailor → review)..."):
                    state = run_application(resolved_resume, job_text)
                    save_application(state)
            except Exception as exc:  # surface a clean message, not a traceback
                st.error(f"Run failed: {exc}")
                st.stop()

            match = state.get("match")
            if match:
                st.metric("Match score", f"{match.match_score}/100")
                c1, c2 = st.columns(2)
                c1.success("Matched: " + ", ".join(match.matched_skills))
                c2.warning("Missing: " + ", ".join(match.missing_skills))

            if state.get("needs_human_review"):
                st.error("⚠️ Draft did not fully pass guardrails — review before sending.")
            else:
                st.success("✅ Draft passed the integrity reviewer.")

            draft = state.get("draft")
            if draft:
                st.subheader("Tailored resume bullets")
                for b in draft.tailored_bullets:
                    st.markdown(f"- {b}")
                st.subheader("Cover letter")
                st.write(draft.cover_letter)
                st.subheader("Recruiter message")
                st.code(draft.recruiter_message, language="markdown")

            review = state.get("review")
            if review:
                with st.expander("Reviewer (guardrail) details"):
                    st.write(f"**Authenticity:** {review.authenticity_score}/100")
                    if review.exaggerations:
                        st.write("**Exaggerations caught:**", review.exaggerations)
                    st.write("**Feedback:**", review.feedback)

            with st.expander("Agent trace"):
                st.code("\n".join(state.get("trace", [])))

with tab_history:
    st.subheader("Tracked applications")
    rows = list_applications()
    if not rows:
        st.info("No applications yet. Run one in the first tab.")
    else:
        st.dataframe(
            [
                {
                    "ID": r["id"],
                    "Date": r["created_at"],
                    "Company": r["company"],
                    "Title": r["title"],
                    "Match": r["match_score"],
                    "Needs review": bool(r["needs_human_review"]),
                }
                for r in rows
            ],
            use_container_width=True,
        )
