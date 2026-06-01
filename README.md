# AI Job Application Agent

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-7e3ff2)
![Pydantic](https://img.shields.io/badge/Pydantic-structured%20outputs-e92063)
![LangSmith](https://img.shields.io/badge/LangSmith-tracing-1c3c3c)
![License](https://img.shields.io/badge/license-MIT-green)

A **multi-agent system** (not a single chatbot) that turns a job posting + your
résumé into tailored, *honest* application materials — with a self-correcting
guardrail loop that refuses to invent experience.

Built with **LangGraph**, **Pydantic** structured outputs, **real tool calling**
(web search), **LangSmith** tracing, an **evaluation harness**, and a
**Streamlit** dashboard.

## Demo

> Add your own screenshots/GIF to `docs/` and they'll render here.

| Dashboard | LangSmith trace |
|---|---|
| ![App dashboard](docs/dashboard.png) | ![Agent trace](docs/langsmith-trace.png) |

The trace screenshot is the money shot — it shows every agent, the `web_search`
tool call nested in the research agent, and each iteration of the review loop.

---

## Why this is an *agentic* system

It isn't one LLM call dressed up as an "agent." It's a `StateGraph` of
specialized agents that hand structured work off to one another, one of which
is a tool-using ReAct sub-agent, with a **conditional self-correction loop**:

```
START
  │
  ▼
[Job Parser]            structured extraction → ParsedJob (Pydantic)
  │
  ▼
[Company Research]      ReAct agent that CHOOSES to call the web_search tool
  │
  ▼
[Resume Match]          honest 0–100 fit score + matched/missing skills
  │
  ▼
[Skill Gap]             critical vs. nice-to-have gaps + learning plan
  │
  ▼
[Tailor]  ◄─────────────────────────┐   bullets + cover letter + recruiter msg
  │                                  │
  ▼                                  │ conditional edge (retry budget)
[Reviewer / Guardrail]               │
  │  pass ─────────► [Finalize] ──► END
  │  fail & retries left ───────────┘  (loops back with feedback)
  │  fail & out of retries ─► [Escalate → human review] ─► END
```

The **review → revise → tailor loop** (with a max-revision budget and a
human-in-the-loop escape hatch) is the core of the design: the system
*evaluates its own output and self-corrects* until it passes integrity checks.

### Concepts demonstrated
- Multi-agent orchestration & handoffs (LangGraph `StateGraph`)
- Real tool calling (web search; the LLM decides when to use it)
- Structured outputs everywhere (Pydantic → valid typed JSON between agents)
- Stateful, conditional routing + retry loops
- Guardrails (anti-exaggeration integrity reviewer)
- Human-in-the-loop escalation
- Provider-agnostic LLM layer (OpenAI / Anthropic / Ollama)
- Evaluation harness measuring reliability, not vibes
- Persistence + dashboard (SQLite + Streamlit)

---

## Quickstart

```bash
cd job-application-agent
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # (cp on macOS/Linux) then fill in a key
```

Set **one** provider in `.env` (e.g. `OPENAI_API_KEY`). `TAVILY_API_KEY` is
optional — without it, web search falls back to DuckDuckGo (no key needed).

### Observability (LangSmith tracing)
Set `LANGSMITH_API_KEY` in `.env` (get one at
[smith.langchain.com](https://smith.langchain.com) → Settings → API Keys) and
tracing turns on automatically — every agent step, tool call, and the
review-loop iterations become a visual trace at smith.langchain.com. Leave the
key empty to run without tracing. The CLI/UI print the current tracing status
on each run.

### Run the CLI
```bash
python -m app.cli --resume data/sample_resume.md --job data/sample_job.txt
```

### Run the dashboard
```bash
streamlit run app/ui.py
```

### Run the evaluation suite
```bash
python -m evals.run_eval
```

---

## Project layout

```
job-application-agent/
├── app/
│   ├── config.py          # env-driven settings
│   ├── llm.py             # provider-agnostic LLM factory
│   ├── schemas.py         # Pydantic structured outputs
│   ├── state.py           # LangGraph shared state
│   ├── graph.py           # the orchestrator (StateGraph + review loop)
│   ├── db.py              # SQLite persistence
│   ├── resume.py          # txt/md/pdf loader
│   ├── cli.py             # command-line runner
│   ├── ui.py              # Streamlit dashboard
│   ├── tools/
│   │   └── web_search.py  # Tavily → DuckDuckGo fallback tool
│   └── agents/
│       ├── job_parser.py
│       ├── company_research.py   # tool-using ReAct sub-agent
│       ├── resume_match.py
│       ├── skill_gap.py
│       ├── tailor.py
│       └── reviewer.py           # guardrail / integrity gate
├── data/                  # sample resume + job posting
├── evals/                 # labeled JDs + metrics harness
├── requirements.txt
└── .env.example
```

---

## Résumé line you can use after building this

> Designed a multi-agent job-application assistant in Python/LangGraph with a
> self-correcting review loop (conditional routing + retry budget +
> human-in-the-loop), real tool-calling for company research, Pydantic
> structured outputs, a provider-agnostic LLM layer, and an evaluation harness
> measuring extraction accuracy and guardrail catch-rate.

## Deploy a live demo (free)

The Streamlit app deploys to **Streamlit Community Cloud** in a few clicks, and
its sidebar accepts a *bring-your-own* OpenAI key — so a public demo runs on the
visitor's key, not yours (no surprise bills).

1. Push this folder to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Point it at your repo, main file `app/ui.py`.
4. (Optional) In **Advanced settings → Secrets**, add `OPENAI_API_KEY` and
   `LANGSMITH_API_KEY` if you want a fully-loaded owner demo; otherwise leave
   blank and let visitors paste their own key in the sidebar.
5. Deploy, then link the URL from your portfolio site.

> Tip: for a portfolio, a short screen-recording + the LangSmith trace
> screenshot often demos better (and costs nothing) than a always-on live app.

## Roadmap (next phases)
- [x] LangSmith tracing for full run observability
- [ ] RAG: retrieve strong bullet/STAR patterns from a knowledge base to ground tailoring
- [ ] Expand eval set to 20–50 labeled job descriptions
- [ ] Dockerfile + deploy (Render / Railway) and link from portfolio site
