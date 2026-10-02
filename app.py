"""ResearchMind - Streamlit front end for the multi-agent research pipeline.

Backend is untouched: this file only calls build_search_agent(),
build_reader_agent(), writer_chain and critic_chain from agents.py,
using the same inputs as pipeline.py.
"""

import html
import re
import time
from urllib.parse import urlparse

import streamlit as st

try:  # API keys stay in .env; nothing is ever rendered in the UI
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

IMPORT_ERROR = None
try:
    from agents import (
        build_search_agent,
        build_reader_agent,
        writer_chain,
        critic_chain,
    )
except Exception as exc:  # shown gracefully below
    IMPORT_ERROR = exc

st.set_page_config(
    page_title="ResearchMind",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
  --bg: #0a0a0a;
  --surface: #121212;
  --surface-2: #181818;
  --border: #262626;
  --border-hover: #3a3a3a;
  --text: #ececec;
  --muted: #8b8b8b;
  --accent: #ff6a1a;
  --accent-soft: rgba(255, 106, 26, 0.12);
  --ok: #3ecf8e;
  --err: #ff5d5d;
  --display: 'Bricolage Grotesque', 'Segoe UI', sans-serif;
  --body: 'IBM Plex Sans', 'Segoe UI', sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, Consolas, monospace;
}

/* ---- Chrome removal ---- */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* ---- Base ---- */
.stApp {
  background:
    radial-gradient(900px 380px at 50% -80px, rgba(255,106,26,0.10), transparent 70%),
    var(--bg);
  color: var(--text);
  font-family: var(--body);
}
.block-container { max-width: 1180px; padding: 3.5rem 1.5rem 2rem; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em { color: var(--text); font-family: var(--body); }
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 { color: var(--text); font-family: var(--display); letter-spacing: -0.01em; }
[data-testid="stMarkdownContainer"] a { color: var(--accent); }
[data-testid="stMarkdownContainer"] code { background: var(--surface-2); color: #ffb48a; border-radius: 6px; }
[data-testid="stMarkdownContainer"] hr { border-color: var(--border); }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { line-height: 1.7; }

/* ---- Hero ---- */
.rm-hero { text-align: center; margin: 0 auto 2.6rem; max-width: 720px; }
.rm-eyebrow {
  display: inline-flex; align-items: center; gap: .55rem;
  font-family: var(--mono); font-size: .72rem; font-weight: 600;
  letter-spacing: .18em; color: var(--accent);
  border: 1px solid rgba(255,106,26,.35); background: var(--accent-soft);
  padding: .4rem .85rem; border-radius: 999px; margin-bottom: 1.4rem;
}
.rm-eyebrow i { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); display: inline-block; }
.rm-title {
  font-family: var(--display); font-weight: 800; color: #fff;
  font-size: clamp(2.8rem, 8vw, 5.2rem); line-height: 1; letter-spacing: -0.04em;
  margin-bottom: 1.1rem;
}
.rm-sub { color: var(--muted); font-size: 1.08rem; line-height: 1.6; max-width: 560px; margin: 0 auto; }

/* ---- Input ---- */
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
div[data-testid="stTextInput"] input {
  background: var(--surface) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: 14px !important;
  height: 3.6rem; padding: 0 1.2rem !important; font-size: 1.08rem !important;
  font-family: var(--body) !important; transition: border-color .2s, box-shadow .2s;
}
div[data-testid="stTextInput"] input::placeholder { color: #5f5f5f !important; }
div[data-testid="stTextInput"] input:hover { border-color: var(--border-hover) !important; }
div[data-testid="stTextInput"] input:focus {
  border-color: var(--accent) !important; box-shadow: 0 0 0 4px var(--accent-soft) !important;
}
div[data-testid="stTextInput"] > div, div[data-baseweb="input"], div[data-baseweb="base-input"] {
  background: transparent !important; border: none !important;
}
[data-testid="InputInstructions"] { display: none !important; }

/* ---- Buttons ---- */
[data-testid^="stBaseButton-primary"] {
  background: var(--accent) !important; color: #140700 !important; border: none !important;
  border-radius: 14px !important; height: 3.4rem; font-weight: 600 !important;
  font-family: var(--body) !important; font-size: 1.02rem !important;
  transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
}
[data-testid^="stBaseButton-primary"]:hover {
  transform: translateY(-1px); filter: brightness(1.08);
  box-shadow: 0 10px 30px -8px rgba(255,106,26,.55);
}
[data-testid^="stBaseButton-primary"]:active { transform: translateY(0); }
[data-testid^="stBaseButton-primary"] p { color: #140700 !important; }
[data-testid^="stBaseButton-secondary"] {
  background: transparent !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: 12px !important;
  transition: border-color .2s, background .2s;
}
[data-testid^="stBaseButton-secondary"]:hover { border-color: var(--accent) !important; background: var(--accent-soft) !important; }
[data-testid^="stBaseButton-secondary"] p { color: var(--text) !important; }

/* ---- Tags ---- */
.rm-tags { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.1rem; }
.rm-tag {
  font-size: .8rem; color: var(--muted); border: 1px solid var(--border);
  background: var(--surface); padding: .35rem .8rem; border-radius: 999px;
  transition: color .2s, border-color .2s, transform .2s;
}
.rm-tag:hover { color: var(--text); border-color: var(--accent); transform: translateY(-1px); }

/* ---- Output note card ---- */
.rm-note { margin-top: 1.6rem; border: 1px solid var(--border); background: var(--surface); border-radius: 16px; padding: 1.2rem 1.3rem; }
.rm-note-title { font-family: var(--display); font-weight: 700; margin-bottom: .6rem; }
.rm-note-row { display: flex; gap: .7rem; padding: .35rem 0; color: var(--muted); font-size: .92rem; }
.rm-note-row b { color: var(--text); font-weight: 600; min-width: 7.2rem; }

/* ---- Pipeline panel ---- */
.rm-panel { border: 1px solid var(--border); background: var(--surface); border-radius: 20px; padding: 1.3rem; }
.rm-panel-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: .9rem; }
.rm-panel-title { font-family: var(--display); font-weight: 700; font-size: 1.15rem; }
.rm-panel-meta { font-family: var(--mono); font-size: .75rem; color: var(--muted); }
.rm-bar { height: 4px; background: var(--border); border-radius: 4px; overflow: hidden; margin-bottom: 1rem; }
.rm-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width .5s ease; }
.rm-bar-fill.rm-bar-err { background: var(--err); }

.rm-stage {
  display: flex; align-items: center; gap: 1rem; padding: .95rem 1rem; margin-bottom: .6rem;
  border: 1px solid var(--border); background: var(--surface-2); border-radius: 14px;
  transition: border-color .2s, transform .2s, background .2s;
}
.rm-stage:last-child { margin-bottom: 0; }
.rm-stage:hover { border-color: var(--border-hover); transform: translateX(2px); }
.rm-num {
  font-family: var(--mono); font-weight: 600; font-size: .85rem; color: var(--muted);
  width: 2.4rem; height: 2.4rem; display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border); border-radius: 10px; flex-shrink: 0;
}
.rm-info { flex: 1; min-width: 0; }
.rm-name { font-weight: 600; color: var(--text); }
.rm-desc { color: var(--muted); font-size: .82rem; margin-top: .1rem; }
.rm-right { text-align: right; flex-shrink: 0; }
.rm-badge { font-family: var(--mono); font-size: .68rem; font-weight: 600; letter-spacing: .1em; color: var(--muted); }
.rm-time { font-family: var(--mono); font-size: .7rem; color: var(--muted); margin-top: .2rem; }

.rm-running { border-color: rgba(255,106,26,.55); background: linear-gradient(90deg, var(--accent-soft), var(--surface-2)); }
.rm-running .rm-num { color: var(--accent); border-color: var(--accent); animation: rm-pulse 1.4s ease-in-out infinite; }
.rm-running .rm-badge { color: var(--accent); }
.rm-complete .rm-num { color: var(--ok); border-color: rgba(62,207,142,.4); }
.rm-complete .rm-badge { color: var(--ok); }
.rm-error { border-color: rgba(255,93,93,.5); }
.rm-error .rm-num { color: var(--err); border-color: var(--err); }
.rm-error .rm-badge { color: var(--err); }
@keyframes rm-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,106,26,.45); } 50% { box-shadow: 0 0 0 8px rgba(255,106,26,0); } }

/* ---- Results ---- */
.rm-results-title { font-family: var(--display); font-weight: 800; font-size: 1.8rem; letter-spacing: -0.02em; color: #fff; }
.rm-results-topic { color: var(--muted); margin-top: .2rem; }
.rm-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: 1.2rem 0 1.4rem; }
.rm-stat { border: 1px solid var(--border); background: var(--surface); border-radius: 14px; padding: 1rem 1.2rem; transition: border-color .2s; }
.rm-stat:hover { border-color: var(--border-hover); }
.rm-stat-v { font-family: var(--display); font-weight: 700; font-size: 1.6rem; color: #fff; }
.rm-stat-l { color: var(--muted); font-size: .82rem; }

button[data-baseweb="tab"] { color: var(--muted) !important; font-family: var(--body); }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--text) !important; }
div[data-baseweb="tab-highlight"] { background: var(--accent) !important; }
div[data-baseweb="tab-border"] { background: var(--border) !important; }

div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] .stMarkdown),
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border) !important; border-radius: 16px !important; }
[data-testid="stExpander"] details { border: 1px solid var(--border) !important; border-radius: 12px !important; background: var(--surface) !important; }
[data-testid="stExpander"] summary p { color: var(--text) !important; }
[data-testid="stAlert"] { border-radius: 12px; }

.rm-source {
  display: flex; align-items: center; gap: .8rem; padding: .75rem 1rem; margin-bottom: .5rem;
  border: 1px solid var(--border); background: var(--surface); border-radius: 12px;
  text-decoration: none !important; transition: border-color .2s, transform .2s;
}
.rm-source:hover { border-color: var(--accent); transform: translateX(2px); }
.rm-source-host { color: var(--text); font-weight: 500; }
.rm-source-url { color: var(--muted); font-size: .8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ---- Footer ---- */
.rm-footer {
  margin-top: 4rem; padding-top: 1.4rem; border-top: 1px solid var(--border);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: .6rem;
  color: var(--muted); font-size: .82rem;
}
.rm-footer b { color: var(--text); font-family: var(--display); }

@media (max-width: 760px) {
  .block-container { padding: 2rem 1rem 1.5rem; }
  .rm-stats { grid-template-columns: 1fr; }
  .rm-footer { flex-direction: column; }
}
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
STAGES = [
    ("01", "Search Agent", "Finds recent, reliable sources"),
    ("02", "Reader Agent", "Scrapes the most relevant page"),
    ("03", "Writer Chain", "Drafts the research report"),
    ("04", "Critic Chain", "Reviews the finished report"),
]
BADGES = {"waiting": "WAITING", "running": "RUNNING", "complete": "COMPLETE", "error": "FAILED"}


def as_text(value) -> str:
    """Normalise agent/chain output (str, message object, or content blocks) to text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    content = getattr(value, "content", None)
    if content is not None:
        return as_text(content)
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(as_text(item))
        return "".join(parts)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("content") or value)
    return str(value)


def extract_urls(text: str) -> list:
    found = re.findall(r"https?://[^\s\)\]>\"'<,]+", text)
    seen, urls = set(), []
    for u in found:
        u = u.rstrip(".;:")
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def init_state():
    ss = st.session_state
    ss.setdefault("statuses", ["waiting"] * 4)
    ss.setdefault("times", [None] * 4)
    ss.setdefault("result", None)
    ss.setdefault("error", None)
    ss.setdefault("topic", "")
    ss.setdefault("total_time", None)


def clear_all():
    ss = st.session_state
    ss.statuses = ["waiting"] * 4
    ss.times = [None] * 4
    ss.result = None
    ss.error = None
    ss.topic = ""
    ss.total_time = None
    ss.topic_input = ""


def render_pipeline(placeholder):
    ss = st.session_state
    done = sum(1 for s in ss.statuses if s == "complete")
    failed = "error" in ss.statuses
    pct = int(done / len(STAGES) * 100)
    cards = []
    for i, (num, name, desc) in enumerate(STAGES):
        status = ss.statuses[i]
        t = ss.times[i]
        time_html = f'<div class="rm-time">{t:.1f}s</div>' if t is not None else ""
        cards.append(
            f'<div class="rm-stage rm-{status}">'
            f'<div class="rm-num">{num}</div>'
            f'<div class="rm-info"><div class="rm-name">{name}</div><div class="rm-desc">{desc}</div></div>'
            f'<div class="rm-right"><div class="rm-badge">{BADGES[status]}</div>{time_html}</div>'
            f"</div>"
        )
    bar_cls = "rm-bar-fill rm-bar-err" if failed else "rm-bar-fill"
    placeholder.markdown(
        '<div class="rm-panel">'
        '<div class="rm-panel-head"><span class="rm-panel-title">Pipeline</span>'
        f'<span class="rm-panel-meta">{done}/4 complete</span></div>'
        f'<div class="rm-bar"><div class="{bar_cls}" style="width:{pct}%"></div></div>'
        + "".join(cards)
        + "</div>",
        unsafe_allow_html=True,
    )


# ---- The four steps: same calls and inputs as pipeline.py ----
def step_search(topic, state):
    search_agent = build_search_agent()
    search_result = search_agent.invoke(
        {"messages": [("user", f"Find recent, reliable  and detailed information about:{topic}")]}
    )
    state["search_results"] = search_result["messages"][-1].content


def step_reader(topic, state):
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke(
        {
            "messages": [
                (
                    "user",
                    f"Based on the following search results about '{topic}',"
                    f"Pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{as_text(state['search_results'])[:800]}",
                )
            ]
        }
    )
    state["scraped_content"] = reader_result["messages"][-1].content


def step_writer(topic, state):
    research_combined = (
        f"SEARCH RESULTS : \n {as_text(state['search_results'])} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {as_text(state['scraped_content'])}"
    )
    state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})


def step_critic(topic, state):
    state["feedback"] = critic_chain.invoke({"report": state["report"]})


STEPS = [step_search, step_reader, step_writer, step_critic]


def execute(topic, placeholder):
    ss = st.session_state
    ss.statuses = ["waiting"] * 4
    ss.times = [None] * 4
    ss.result = None
    ss.error = None
    ss.topic = topic
    render_pipeline(placeholder)

    state = {}
    started = time.perf_counter()
    for i, step in enumerate(STEPS):
        ss.statuses[i] = "running"
        render_pipeline(placeholder)
        t0 = time.perf_counter()
        try:
            step(topic, state)
        except Exception as exc:
            ss.statuses[i] = "error"
            ss.times[i] = time.perf_counter() - t0
            msg = f"{type(exc).__name__}: {str(exc)[:400]}"
            ss.error = f"{STAGES[i][1]} failed. {msg}"
            render_pipeline(placeholder)
            return
        ss.times[i] = time.perf_counter() - t0
        ss.statuses[i] = "complete"
        render_pipeline(placeholder)

    ss.total_time = time.perf_counter() - started
    ss.result = state


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
init_state()

st.markdown(
    '<div class="rm-hero">'
    '<div class="rm-eyebrow"><i></i>MULTI-AGENT AI SYSTEM</div>'
    '<div class="rm-title">ResearchMind</div>'
    '<div class="rm-sub">Four specialised agents search the web, read the best source, '
    "write a structured report and critique it. Enter a topic to begin.</div>"
    "</div>",
    unsafe_allow_html=True,
)

if IMPORT_ERROR is not None:
    st.error(
        "Could not load your agents. Check that agents.py is in the same folder as app.py "
        f"and that your dependencies are installed.\n\n{type(IMPORT_ERROR).__name__}: {IMPORT_ERROR}"
    )
    st.stop()

left, right = st.columns([1.55, 1], gap="large")

with left:
    with st.form("research_form", border=False):
        topic_in = st.text_input(
            "Research topic",
            key="topic_input",
            placeholder="What do you want to research?",
            label_visibility="collapsed",
        )
        run_clicked = st.form_submit_button(
            "Run Research Pipeline", type="primary", use_container_width=True
        )
    st.markdown(
        '<div class="rm-tags">'
        '<span class="rm-tag">Live web search</span>'
        '<span class="rm-tag">Page scraping</span>'
        '<span class="rm-tag">Report writing</span>'
        '<span class="rm-tag">Critic review</span>'
        '<span class="rm-tag">Source list</span>'
        "</div>"
        '<div class="rm-note">'
        '<div class="rm-note-title">What you get</div>'
        '<div class="rm-note-row"><b>Report</b><span>A written research report you can download</span></div>'
        '<div class="rm-note-row"><b>Critic feedback</b><span>An independent review of that report</span></div>'
        '<div class="rm-note-row"><b>Sources</b><span>The search results and scraped content behind it</span></div>'
        "</div>",
        unsafe_allow_html=True,
    )

with right:
    pipeline_slot = st.empty()
    render_pipeline(pipeline_slot)

if run_clicked:
    if not (topic_in or "").strip():
        st.warning("Enter a research topic to start the pipeline.")
    else:
        with st.spinner(""):
            execute(topic_in.strip(), pipeline_slot)

# ---- Errors ----
if st.session_state.error:
    st.error(
        st.session_state.error
        + "\n\nCheck your .env keys and your connection, then run the pipeline again. "
        "Stages that finished before the failure are marked complete."
    )

# ---- Results ----
result = st.session_state.result
if result:
    report_text = as_text(result.get("report"))
    feedback_text = as_text(result.get("feedback"))
    search_text = as_text(result.get("search_results"))
    scraped_text = as_text(result.get("scraped_content"))
    urls = extract_urls(search_text + "\n" + scraped_text)

    st.markdown("<div style='height:2.4rem'></div>", unsafe_allow_html=True)
    head_l, head_r = st.columns([4, 1], vertical_alignment="center")
    with head_l:
        st.markdown(
            '<div class="rm-results-title">Research results</div>'
            f'<div class="rm-results-topic">{html.escape(st.session_state.topic)}</div>',
            unsafe_allow_html=True,
        )
    with head_r:
        st.button("Clear Research", on_click=clear_all, use_container_width=True)

    total = st.session_state.total_time or 0
    st.markdown(
        '<div class="rm-stats">'
        f'<div class="rm-stat"><div class="rm-stat-v">{total:.0f}s</div><div class="rm-stat-l">Total pipeline time</div></div>'
        f'<div class="rm-stat"><div class="rm-stat-v">{len(report_text.split()):,}</div><div class="rm-stat-l">Words in report</div></div>'
        f'<div class="rm-stat"><div class="rm-stat-v">{len(urls)}</div><div class="rm-stat-l">Source links found</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    tab_report, tab_feedback, tab_sources = st.tabs(["Report", "Critic feedback", "Sources"])

    with tab_report:
        with st.container(border=True):
            st.markdown(report_text)
        slug = re.sub(r"[^a-z0-9]+", "-", st.session_state.topic.lower()).strip("-")[:50] or "report"
        st.download_button(
            "Download Report",
            data=report_text,
            file_name=f"researchmind-{slug}.md",
            mime="text/markdown",
        )

    with tab_feedback:
        with st.container(border=True):
            st.markdown(feedback_text)

    with tab_sources:
        if urls:
            links = []
            for u in urls:
                host = urlparse(u).netloc.replace("www.", "") or u
                links.append(
                    f'<a class="rm-source" href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">'
                    f'<div style="min-width:0"><div class="rm-source-host">{html.escape(host)}</div>'
                    f'<div class="rm-source-url">{html.escape(u)}</div></div></a>'
                )
            st.markdown("".join(links), unsafe_allow_html=True)
        with st.expander("Search results", expanded=not urls):
            st.markdown(search_text)
        with st.expander("Scraped content"):
            st.markdown(scraped_text)

# ---- Footer ----
st.markdown(
    '<div class="rm-footer">'
    "<span><b>ResearchMind</b> &nbsp;Multi-agent research pipeline</span>"
    "<span>API keys are read from your local .env and never shown in this interface.</span>"
    "</div>",
    unsafe_allow_html=True,
)