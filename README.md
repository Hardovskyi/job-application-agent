# AI Job Application Agent

A multi-agent system that takes a job posting and a résumé and produces tailored application materials — bullets, a cover letter, and a short recruiter message — without inventing experience.

Built with **LangGraph**, **Pydantic** structured outputs, tool-using company research, a bounded reviewer loop, **LangSmith** tracing, a **FastAPI** API, and a **Streamlit** UI. Runs are checkpointed to SQLite by `thread_id` so state survives restarts.

**[Live UI](https://job-application-agent-c9m5l6nm6sp6t3gkfptfla.streamlit.app/)** · **[Live API docs](https://job-application-agent-api.onrender.com/docs)**

## How it works

Six agents run inside a LangGraph `StateGraph`:

1. **Job Parser** — extracts role, skills, and requirements  
2. **Company Research** — ReAct agent with web search  
3. **Resume Match** — fit score and matched / missing skills  
4. **Skill Gap** — critical vs nice-to-have gaps  
5. **Tailor** — writes bullets, cover letter, recruiter note  
6. **Reviewer** — integrity check; on failure, revises (up to 2 retries) or escalates for human review  

## Evaluation

A 60-case suite measures reliability (first-pass vs final pass after the reviewer loop, structured-output success, research success, latency, and estimated cost). On that run:

- First-pass success: **1.7%** → final success after reviewer loop: **70%**
- Structured outputs: **100%** · research success: **100%**
- Avg ~**$0.003**/run · p95 latency ~**30s**

```bash
python -m evals.run_eval --suite gold              # CI smoke set
python -m evals.run_eval --suite full --limit 60   # full measurement
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
cp .env.example .env         # set OPENAI_API_KEY
```

Optional: `TAVILY_API_KEY`, `LANGSMITH_API_KEY`.

## Run

```bash
python -m app.cli --resume data/sample_resume.md --job data/sample_job.txt
streamlit run app/ui.py
uvicorn app.api:app --reload --port 8000
python -m pytest tests/ -q --cov=app
```

API: `POST /v1/applications`, `GET /v1/threads/{thread_id}`, `GET /v1/applications`, `GET /health`.

## Deploy

Streamlit Cloud hosts the UI. The FastAPI service is on Render (`Dockerfile` / `render.yaml` also work for Railway).

```bash
docker build -t job-application-agent-api .
docker run --rm -p 8000:8000 --env-file .env job-application-agent-api
```

## CI

GitHub Actions runs unit tests and coverage on every push/PR. With `OPENAI_API_KEY` as a repo secret, pushes to `main` also run the gold eval suite.

## Layout

```
app/        # agents, FastAPI, Streamlit, checkpoints
evals/      # case bank + metrics harness
tests/      # unit tests
Dockerfile  render.yaml  railway.toml
```

## Stack

Python · LangGraph · SqliteSaver · LangChain · Pydantic · FastAPI · Streamlit · SQLite · Docker · LangSmith · GitHub Actions · Render
