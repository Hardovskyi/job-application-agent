# AI Job Application Agent

A multi-agent system that takes a job posting and a résumé and produces tailored application materials — bullets, a cover letter, and a short recruiter message — without inventing experience.

Built with **LangGraph**, **Pydantic**, tool calling for company research, **LangSmith** tracing, and a **Streamlit** UI.

**[Live demo](https://job-application-agent-c9m5l6nm6sp6t3gkfptfla.streamlit.app/)** — paste your own OpenAI key in the sidebar.

## How it works

Six agents run in sequence inside a LangGraph `StateGraph`:

1. **Job Parser** — extracts role, skills, and requirements  
2. **Company Research** — ReAct agent that can call web search  
3. **Resume Match** — fit score and matched / missing skills  
4. **Skill Gap** — critical vs nice-to-have gaps  
5. **Tailor** — writes bullets, cover letter, recruiter note  
6. **Reviewer** — integrity check; if it fails, the tailor revises (up to 2 retries) or escalates for human review  

Structured outputs between agents use Pydantic. Runs can be saved to SQLite and viewed in the Streamlit dashboard.

## Setup

```bash
cd job-application-agent
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt
copy .env.example .env               # then set OPENAI_API_KEY
```

Optional: `TAVILY_API_KEY` for search (otherwise DuckDuckGo), `LANGSMITH_API_KEY` for tracing.

## Run

```bash
# CLI
python -m app.cli --resume data/sample_resume.md --job data/sample_job.txt

# UI
streamlit run app/ui.py

# Eval harness
python -m evals.run_eval
```

## Layout

```
app/
  graph.py           # orchestrator + review loop
  agents/            # six specialized agents
  tools/web_search.py
  schemas.py         # Pydantic models
  ui.py              # Streamlit
  cli.py
data/                # sample résumé + job
evals/               # labeled JDs + metrics
```

## Stack

Python · LangGraph · LangChain · Pydantic · Streamlit · SQLite · LangSmith
