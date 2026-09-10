"""Labeled eval cases: 3 gold JDs + ~60 synthetic postings (60+ total suite)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

EVAL_DIR = Path(__file__).resolve().parent
JD_DIR = EVAL_DIR / "job_descriptions"


@dataclass(frozen=True)
class EvalCase:
    id: str
    job_text: str
    expected_title_contains: str
    expected_required_skills: list[str]
    min_match_score: int
    max_match_score: int
    suite: Literal["gold", "synthetic"]


def _load_gold() -> list[EvalCase]:
    expected = json.loads((EVAL_DIR / "expected_outputs.json").read_text("utf-8"))
    cases: list[EvalCase] = []
    for jd_file, spec in expected.items():
        path = JD_DIR / jd_file
        cases.append(
            EvalCase(
                id=f"gold:{jd_file}",
                job_text=path.read_text(encoding="utf-8"),
                expected_title_contains=spec["expected_title_contains"],
                expected_required_skills=list(spec["expected_required_skills"]),
                min_match_score=int(spec.get("min_match_score", 0)),
                max_match_score=int(spec.get("max_match_score", 100)),
                suite="gold",
            )
        )
    return cases


# Role templates: (title_fragment, company, required skills, score band, body).
_TEMPLATES: list[dict[str, Any]] = [
    {
        "title": "Junior AI Engineer",
        "skills": ["Python", "agent framework", "REST API", "Pydantic", "Git"],
        "min": 25,
        "max": 95,
        "blurb": "Build LLM agent workflows, REST APIs, and structured outputs.",
    },
    {
        "title": "Computer Vision Engineer",
        "skills": ["Python", "C++", "PyTorch", "computer vision", "quantization", "Linux"],
        "min": 45,
        "max": 100,
        "blurb": "Deploy perception models on edge devices for robotics.",
    },
    {
        "title": "Data Analyst",
        "skills": ["SQL", "Python", "pandas", "visualization"],
        "min": 15,
        "max": 85,
        "blurb": "Build dashboards and turn operational data into decisions.",
    },
    {
        "title": "ML Engineer",
        "skills": ["Python", "PyTorch", "MLOps", "Docker", "CI/CD"],
        "min": 20,
        "max": 90,
        "blurb": "Train, package, and ship ML models with monitoring.",
    },
    {
        "title": "Backend Engineer",
        "skills": ["Python", "FastAPI", "SQL", "Git", "REST API"],
        "min": 20,
        "max": 90,
        "blurb": "Design reliable Python services and APIs.",
    },
    {
        "title": "Embedded Software Engineer",
        "skills": ["C++", "Linux", "embedded", "Python"],
        "min": 30,
        "max": 95,
        "blurb": "Write firmware-adjacent tools and embedded Linux utilities.",
    },
    {
        "title": "Robotics Software Engineer",
        "skills": ["Python", "ROS2", "Linux", "C++"],
        "min": 25,
        "max": 95,
        "blurb": "Integrate sensors and autonomy stacks on ROS2.",
    },
    {
        "title": "Applied Scientist",
        "skills": ["Python", "PyTorch", "computer vision", "experimentation"],
        "min": 25,
        "max": 95,
        "blurb": "Prototype CV models and evaluate them rigorously.",
    },
    {
        "title": "Platform Engineer",
        "skills": ["Python", "Docker", "CI/CD", "Linux", "Git"],
        "min": 15,
        "max": 85,
        "blurb": "Automate developer workflows and deployment pipelines.",
    },
    {
        "title": "Automation Engineer",
        "skills": ["Python", "Git", "APIs", "scripting"],
        "min": 25,
        "max": 95,
        "blurb": "Automate analysis pipelines and reporting workflows.",
    },
]

_COMPANIES = [
    "Acme AI",
    "Nova Robotics",
    "Bright Analytics",
    "EdgeForge",
    "Helix Labs",
    "Orbit Systems",
    "Cedar Health Tech",
    "Northwind Autonomy",
    "Pixel Harbor",
    "Summit Compute",
]


def _render_jd(company: str, title: str, skills: list[str], blurb: str, seniority: str) -> str:
    req = "\n".join(f"- {s}" for s in skills)
    return (
        f"{title} — {company}\n\n"
        f"About {company}:\n"
        f"{company} is hiring for a {seniority.lower()} role. {blurb}\n\n"
        f"Required skills:\n{req}\n\n"
        f"Preferred:\n- Clear communication\n- Ownership mindset\n\n"
        f"Experience: {seniority}.\n"
    )


def _synthetic_cases(target: int = 60) -> list[EvalCase]:
    cases: list[EvalCase] = []
    i = 0
    while len(cases) < target:
        tmpl = _TEMPLATES[i % len(_TEMPLATES)]
        company = _COMPANIES[i % len(_COMPANIES)]
        seniority = ["0-2 years", "1-3 years", "New grads welcome", "Junior-Mid"][i % 4]
        title = tmpl["title"]
        words = title.split()
        expected = " ".join(words[:2]) if len(words) >= 2 else words[0]
        case_id = (
            f"synth:{i:03d}:{title.replace(' ', '_').lower()}"
            f":{company.replace(' ', '_').lower()}"
        )
        cases.append(
            EvalCase(
                id=case_id,
                job_text=_render_jd(company, title, tmpl["skills"], tmpl["blurb"], seniority),
                expected_title_contains=expected,
                expected_required_skills=list(tmpl["skills"][:4]),
                min_match_score=int(tmpl["min"]),
                max_match_score=int(tmpl["max"]),
                suite="synthetic",
            )
        )
        i += 1
    return cases


def load_cases(
    *,
    suite: Literal["gold", "synthetic", "full"] = "full",
    limit: int | None = None,
) -> list[EvalCase]:
    gold = _load_gold()
    synthetic = _synthetic_cases(60)
    if suite == "gold":
        cases = gold
    elif suite == "synthetic":
        cases = synthetic
    else:
        cases = gold + synthetic
    if limit is not None:
        cases = cases[: max(0, limit)]
    return cases


def case_spec(case: EvalCase) -> dict[str, Any]:
    return {
        "expected_title_contains": case.expected_title_contains,
        "expected_required_skills": case.expected_required_skills,
        "min_match_score": case.min_match_score,
        "max_match_score": case.max_match_score,
    }
