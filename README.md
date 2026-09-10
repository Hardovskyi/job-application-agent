# AI Job Application Agent

A multi-agent system that takes a job posting and a résumé and produces tailored application materials - bullets, a cover letter, and a short recruiter message - without inventing experience.

Built with **LangGraph** (SQLite checkpoints), **Pydantic**, tool calling, **LangSmith** tracing, a **FastAPI** API, and a **Streamlit** UI.

**[Live demo (Streamlit)](https://job-application-agent-c9m5l6nm6sp6t3gkfptfla.streamlit.app/)** — paste your own OpenAI key in the sidebar.

> Streamlit = interactive UI. FastAPI = programmatic API (`/docs`). They complement each other; Postgres would replace SQLite storage, not Streamlit.

## How it works

Six agents run in sequence inside a LangGraph `StateGraph`:

1. **Job Parser** - extracts role, skills, and requirements  
2. **Company Research** - ReAct agent that can call web search  
3. **Resume Match** - fit score and matched / missing skills  
4. **Skill Gap** - critical vs nice-to-have gaps  
5. **Tailor** - writes bullets, cover letter, recruiter note  
6. **Reviewer** - integrity check; if it fails, the tailor revises (up to 2 retries) or escalates for human review  

Structured outputs between agents use Pydantic. Every run is checkpointed to SQLite by `thread_id` so state survives restarts and can be reloaded via the API. Completed runs are also stored in an applications history DB for the Streamlit dashboard.

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

# Streamlit UI
streamlit run app/ui.py

# FastAPI (docs at http://localhost:8000/docs)
uvicorn app.api:app --reload --port 8000

# Unit tests + coverage (no API key required)
python -m pytest tests/ -q --cov=app --cov-report=term-missing

# Eval harness (needs OPENAI_API_KEY)
python -m evals.run_eval --suite gold                 # 3 labeled cases (CI)
python -m evals.run_eval --suite full --limit 60      # measurement suite
```

### API examples

```bash
# Run the pipeline
curl -X POST http://localhost:8000/v1/applications \
  -H "Content-Type: application/json" \
  -d "{\"resume_text\": \"...\", \"job_text\": \"...\"}"

# Reload checkpointed state by thread_id
curl http://localhost:8000/v1/threads/<thread_id>

# List saved application history
curl http://localhost:8000/v1/applications
```

## Deploy FastAPI (Docker → Render / Railway)

The Streamlit demo stays on Streamlit Cloud. Use Docker for the **API** so recruiters can open `/docs`.

```bash
docker build -t job-application-agent-api .
docker run --rm -p 8000:8000 --env-file .env job-application-agent-api
# open http://localhost:8000/docs and http://localhost:8000/health
```

**Render:** New → Blueprint (uses `render.yaml`) or Web Service with Dockerfile. Set `OPENAI_API_KEY` in the dashboard. Root directory = this folder if the repo is a monorepo.

**Railway:** New → Deploy from GitHub → set Dockerfile path / root to this folder (`railway.toml`). Set `OPENAI_API_KEY`. Health check: `/health`.

## Evaluation metrics

`python -m evals.run_eval` writes `evals/results/latest.json` with:

| Metric | Meaning |
|--------|---------|
| `first_pass_success_rate` | Accepted with **0** reviewer revisions |
| `final_success_rate` | Accepted after the bounded reviewer loop |
| `structured_output_success_rate` | All agent Pydantic outputs present |
| `research_success_rate` | Company-research path produced a usable briefing |
| `avg_latency_s` / `p95_latency_s` | End-to-end wall time |
| `avg_cost_usd` | Estimated OpenAI cost (gpt-4o-mini list prices) |

Use **measured** numbers from that JSON on your résumé — never invent rates. Full suite is ~63 cases (`--suite full`); CI runs `--suite gold` only to control spend.

## CI/CD

GitHub Actions runs unit tests + coverage on every push/PR. If `OPENAI_API_KEY` is set as a repo secret, pushes to `main` also run the gold eval suite and upload the summary artifact.

## Layout

```
app/                 # agents, FastAPI, Streamlit, checkpoints
tests/               # CI unit tests (no LLM required)
evals/               # case bank + metrics harness + results/
Dockerfile           # API container
render.yaml          # Render Blueprint
railway.toml         # Railway config
.github/workflows/   # CI pipeline
```

## Stack

Python · LangGraph · LangGraph SqliteSaver · LangChain · Pydantic · FastAPI · Streamlit · SQLite · Docker · LangSmith · GitHub Actions
