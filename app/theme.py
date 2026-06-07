"""Shared UI theming for the Streamlit app.

Injects a branded dark theme (matching the portfolio site: blue accent, DM Sans /
JetBrains Mono) plus helpers for a hero header and an agent-pipeline strip.
"""
from __future__ import annotations

import streamlit as st

ACCENT = "#3b9eff"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea {
  font-family: 'DM Sans', system-ui, sans-serif;
}
.stApp {
  background:
    radial-gradient(1100px 520px at 18% -8%, rgba(59,158,255,0.12), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(155,123,255,0.08), transparent 55%),
    #0a0a0f;
}
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] {
  background: #0c0c13;
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* Hero */
.hero-wrap {
  padding: 6px 0 20px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  margin-bottom: 22px;
}
.hero-title {
  font-size: 2.3rem; font-weight: 700; letter-spacing: -0.025em; margin: 0; line-height: 1.1;
}
.hero-title .grad {
  background: linear-gradient(90deg, #3b9eff, #9b7bff);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: #9898a8; font-size: 1rem; margin-top: 8px; }

/* Pipeline strip */
.pipe { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 16px; }
.pipe .step {
  font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; padding: 6px 13px;
  border: 1px solid rgba(255,255,255,0.1); border-radius: 100px; color: #c7c7d2;
  background: rgba(255,255,255,0.03);
}
.pipe .step.loop { border-color: rgba(59,158,255,0.4); color: #8fc2ff; background: rgba(59,158,255,0.08); }
.pipe .arrow { color: #3b9eff; font-size: 0.85rem; font-weight: 600; }

/* Buttons */
div.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #3b9eff, #5b7bff); border: none;
  border-radius: 10px; font-weight: 600; padding: 0.55rem 1.3rem;
}
div.stButton > button[kind="primary"]:hover { filter: brightness(1.08); }

/* Metric + containers */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 14px 18px;
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title_html: str, subtitle: str, steps: list[str], loop_from: int | None = None) -> None:
    """Render a hero header with a pipeline strip.

    `loop_from` highlights steps at/after that index to hint a feedback loop.
    """
    parts: list[str] = []
    for i, s in enumerate(steps):
        if i:
            parts.append('<span class="arrow">&#8594;</span>')
        cls = "step loop" if (loop_from is not None and i >= loop_from) else "step"
        parts.append(f'<span class="{cls}">{s}</span>')
    chips = "".join(parts)
    st.markdown(
        f"""
        <div class="hero-wrap">
          <div class="hero-title">{title_html}</div>
          <div class="hero-sub">{subtitle}</div>
          <div class="pipe">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
