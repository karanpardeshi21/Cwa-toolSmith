import html
import re
from datetime import datetime
from agent import process_task

import streamlit as st

st.set_page_config(
    page_title="ToolSmith",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Session state
# -----------------------------
DEFAULTS = {
    "page": "Home",
    "saved_tools": [],
    "current_task": "",
    "agent_result": None,
    "search_tools": "",
    "activity": [],
    "runs": 0,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# Styling  (palette: ink / ember / rose / steel)
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --ink: #080b16;
        --surface: #10152a;
        --surface-2: #161c36;
        --line: #232b4a;
        --text: #eceffa;
        --muted: #8f99ba;
        --ember: #ff7a45;
        --rose: #ff3d8b;
        --steel: #6a93ff;
        --ok: #39d98a;
        --bad: #ff5a6a;
        --forge: linear-gradient(100deg, #ff9a4d 0%, #ff4f7b 55%, #c04bff 100%);
    }

    html, body, [class*="css"], .stApp {
        font-family: "Space Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--text);
    }
    #MainMenu, footer { visibility: hidden; }

    /* ---------- canvas ---------- */
    [data-testid="stAppViewContainer"], .stApp {
        background:
            radial-gradient(900px 480px at 92% -8%, rgba(255, 90, 90, .20), transparent 60%),
            radial-gradient(800px 520px at -5% 12%, rgba(106, 147, 255, .16), transparent 60%),
            linear-gradient(rgba(255,255,255,.028) 1px, transparent 1px) 0 0 / 44px 44px,
            linear-gradient(90deg, rgba(255,255,255,.028) 1px, transparent 1px) 0 0 / 44px 44px,
            var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1280px;
        padding: 2.4rem clamp(1rem, 3vw, 2.5rem) 3rem;
    }
    h1, h2, h3, h4, h5, p, label, span, li, div { color: inherit; }
    h2, h3, h4 { font-weight: 600; letter-spacing: -.02em; }
    hr { border-color: var(--line) !important; }

    /* ---------- sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1022 0%, #090c1a 100%);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div { padding-top: 1.3rem; }
    .brand { display: flex; align-items: center; gap: .7rem; padding: .2rem .3rem 1.2rem; }
    .brand-mark {
        width: 38px; height: 38px; border-radius: 11px;
        display: grid; place-items: center;
        background: var(--forge);
        color: #fff; font-size: 1.15rem;
        box-shadow: 0 0 24px rgba(255, 79, 123, .45);
    }
    .brand-name { font-size: 1.35rem; font-weight: 700; letter-spacing: -.04em; color: var(--text); }
    .brand-sub { font-size: .8rem; color: var(--muted); margin-top: -.15rem; }

    [data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: .25rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: .65rem .85rem;
        border-radius: 12px;
        border: 1px solid transparent;
        width: 100%;
        cursor: pointer;
        transition: background .15s, border-color .15s;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child { display: none; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label p { font-weight: 500; color: var(--muted); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.04); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(100deg, rgba(255,122,69,.16), rgba(255,61,139,.12));
        border-color: rgba(255, 106, 106, .38);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { color: var(--text); font-weight: 600; }
    .side-stat {
        margin-top: .4rem; padding: .9rem 1rem;
        border: 1px solid var(--line); border-radius: 14px;
        background: rgba(255,255,255,.025);
    }
    .side-stat b { font-size: 1.6rem; letter-spacing: -.04em; color: var(--text); }
    .side-stat span { display: block; font-size: .82rem; color: var(--muted); }

    /* ---------- type ---------- */
    .hero {
        font-size: clamp(2.4rem, 4.8vw, 4.1rem);
        line-height: 1.02;
        letter-spacing: -.05em;
        font-weight: 700;
        margin: .2rem 0 .9rem;
        background: linear-gradient(180deg, #ffffff 30%, #aab4da 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .hero.small { font-size: clamp(2rem, 3.6vw, 3rem); }
    .subtitle { max-width: 640px; color: var(--muted); font-size: 1.04rem; line-height: 1.6; margin-bottom: 1.6rem; }
    .muted { color: var(--muted); font-size: .88rem; }

    /* ---------- cards ---------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(160deg, rgba(24,30,56,.85), rgba(14,18,36,.85));
        border: 1px solid var(--line) !important;
        border-radius: 20px !important;
        box-shadow: 0 18px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04);
        backdrop-filter: blur(6px);
    }
    .st-key-composer [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-composer {
        border-radius: 22px;
    }
    .st-key-composer > [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid transparent !important;
        background:
            linear-gradient(#10152a, #10152a) padding-box,
            var(--forge) border-box;
        box-shadow: 0 0 60px rgba(255, 79, 123, .13), 0 18px 50px rgba(0,0,0,.4);
    }

    .stat {
        border: 1px solid var(--line); border-radius: 18px;
        background: linear-gradient(160deg, rgba(24,30,56,.85), rgba(14,18,36,.85));
        padding: 1.1rem 1.25rem;
    }
    .stat .n { font-size: 2rem; font-weight: 700; letter-spacing: -.05em; color: var(--text); line-height: 1.1; }
    .stat .l { font-size: .84rem; color: var(--muted); margin-top: .15rem; }

    /* ---------- pipeline ---------- */
    .pipe { display: grid; grid-template-columns: repeat(4, 1fr); gap: .7rem; margin: .4rem 0 1.4rem; }
    .step {
        position: relative;
        border: 1px solid var(--line); border-radius: 16px;
        padding: .85rem .95rem;
        background: rgba(255,255,255,.02);
    }
    .step:not(:last-child)::after {
        content: ""; position: absolute; top: 50%; right: -.7rem;
        width: .7rem; height: 2px; background: var(--line);
    }
    .step .dot {
        width: 24px; height: 24px; border-radius: 50%;
        display: grid; place-items: center;
        font-size: .72rem; font-weight: 700;
        border: 1.5px solid var(--line); color: var(--muted);
        margin-bottom: .55rem;
    }
    .step .t { font-weight: 600; font-size: .95rem; color: var(--text); }
    .step .s { font-size: .78rem; color: var(--muted); }
    .step.done { border-color: rgba(57,217,138,.4); background: rgba(57,217,138,.06); }
    .step.done .dot { background: var(--ok); border-color: var(--ok); color: #04150c; }
    .step.fail { border-color: rgba(255,90,106,.5); background: rgba(255,90,106,.08); }
    .step.fail .dot { background: var(--bad); border-color: var(--bad); color: #1a0508; }
    .step.skip { opacity: .45; }

    /* ---------- tool header ---------- */
    .tool-head {
        border: 1px solid var(--line); border-radius: 18px;
        padding: 1.1rem 1.3rem; margin: .4rem 0 1rem;
        background: linear-gradient(120deg, rgba(255,122,69,.10), rgba(106,147,255,.07));
    }
    .tool-head .fn { font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 1.05rem; color: #ffc9a8; }
    .tool-head .ds { color: var(--muted); margin-top: .35rem; line-height: 1.55; }

    /* ---------- activity ---------- */
    .activity-row {
        display: flex; gap: .8rem; align-items: flex-start;
        padding: .8rem 0; border-bottom: 1px solid var(--line);
    }
    .activity-row:last-child { border-bottom: 0; }
    .pip { width: 9px; height: 9px; border-radius: 50%; margin-top: .45rem; background: var(--steel); flex: none; }
    .pip.ok { background: var(--ok); } .pip.bad { background: var(--bad); }
    .activity-title { font-weight: 600; color: var(--text); }
    .activity-desc { font-size: .87rem; color: var(--muted); margin-top: .1rem; overflow-wrap: anywhere; }
    .activity-time { font-size: .76rem; color: #626c91; margin-top: .2rem; }

    /* ---------- inputs ---------- */
    .stTextArea textarea, .stTextInput input {
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        font-family: "Space Grotesk", sans-serif !important;
        font-size: 1rem !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--ember) !important;
        box-shadow: 0 0 0 3px rgba(255,122,69,.18) !important;
    }
    ::placeholder { color: #5f6a91 !important; }

    /* ---------- buttons ---------- */
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 12px;
        min-height: 2.75rem;
        font-weight: 600;
        font-family: "Space Grotesk", sans-serif;
        background: var(--surface-2);
        color: var(--text);
        border: 1px solid var(--line);
        transition: transform .12s, border-color .15s, box-shadow .15s;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        border-color: rgba(255,122,69,.6); color: #fff; transform: translateY(-1px);
    }
    div.stButton > button[kind="primary"] {
        background: var(--forge); border: 0; color: #fff;
        box-shadow: 0 8px 28px rgba(255, 79, 123, .35);
    }
    div.stButton > button[kind="primary"]:hover { box-shadow: 0 10px 34px rgba(255, 79, 123, .55); }
    .chips div.stButton > button {
        min-height: 2.2rem; font-size: .85rem; font-weight: 500;
        border-radius: 999px; color: var(--muted); background: transparent;
    }

    /* ---------- alerts, code, expander ---------- */
    [data-testid="stAlert"] {
        border-radius: 14px; border: 1px solid var(--line);
        background: var(--surface-2);
    }
    [data-testid="stCode"], [data-testid="stCode"] pre {
        border-radius: 14px !important;
        background: #0a0e1d !important;
        border: 1px solid var(--line);
        font-family: "JetBrains Mono", ui-monospace, monospace !important;
    }
    [data-testid="stExpander"] {
        border: 1px solid var(--line); border-radius: 14px; background: rgba(255,255,255,.02);
    }
    [data-testid="stExpander"] summary:hover { color: var(--ember); }
    [data-testid="stJson"] { background: #0a0e1d; border-radius: 12px; padding: .5rem; }
    .stSpinner > div { border-top-color: var(--ember) !important; }
    [data-testid="stCaptionContainer"] { color: var(--muted); }

    :focus-visible { outline: 2px solid var(--steel) !important; outline-offset: 2px; }
    @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }

    @media (max-width: 760px) {
        .block-container { padding: 1rem .8rem 2rem; }
        .pipe { grid-template-columns: repeat(2, 1fr); }
        .step::after { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
def add_activity(title: str, description: str, tone: str = "info") -> None:
    st.session_state.activity.insert(
        0,
        {
            "title": title,
            "description": description,
            "time": datetime.now().strftime("%d %b, %H:%M"),
            "tone": tone,
        },
    )
    st.session_state.activity = st.session_state.activity[:8]


def safe_filename(task: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", task.lower())[:5]
    stem = "_".join(words) or "generated_tool"
    return f"{stem[:55]}.py"


def render_pipeline(result: dict | None) -> None:
    """Four-stage tracker that reflects what the agent actually did."""
    status = (result or {}).get("status")
    labels = [
        ("Search", "Approved tools"),
        ("Generate", "New candidate"),
        ("Validate", "Safety checks"),
        ("Save", "Tool registry"),
    ]
    if status is None:
        states = ["", "", "", ""]
    elif status == "existing_tools_found":
        states = ["done", "skip", "skip", "skip"]
    elif status == "success":
        states = ["done", "done", "done", "done"]
    elif status == "validation_failed":
        states = ["done", "done", "fail", "skip"]
    else:
        states = ["fail", "skip", "skip", "skip"]

    icons = {"done": "✓", "fail": "✕", "skip": "–", "": ""}
    cells = []
    for i, ((title, sub), state) in enumerate(zip(labels, states), start=1):
        mark = icons[state] or str(i)
        cells.append(
            f'<div class="step {state}"><div class="dot">{mark}</div>'
            f'<div class="t">{title}</div><div class="s">{sub}</div></div>'
        )
    st.markdown(f'<div class="pipe">{"".join(cells)}</div>', unsafe_allow_html=True)


def show_result(result: dict) -> None:
    """Render the actual response returned by agent.process_task."""
    status = result.get("status", "unknown")

    render_pipeline(result)

    if result.get("retrieval_warning"):
        st.warning(result["retrieval_warning"])

    if status == "existing_tools_found":
        st.info(result.get("message", "Approved tool candidates found."))
        tools = result.get("tools", [])
        if not tools:
            st.caption("The agent returned no tool details.")
        for index, tool in enumerate(tools, start=1):
            with st.container(border=True):
                st.markdown(f"**{index}. {tool.get('name', tool.get('tool_name', 'Unnamed tool'))}**")
                if tool.get("description"):
                    st.write(tool["description"])
                if tool.get("similarity_score") is not None:
                    st.caption(f"Similarity score: {tool['similarity_score']}")
                if tool.get("version") is not None:
                    st.caption(f"Version: {tool['version']}")
        return

    candidate = result.get("tool") or result.get("candidate")

    if status == "success":
        st.success(result.get("message", "Tool generated, validated, and saved."))
    elif status == "validation_failed":
        st.error(result.get("message", "Validation failed. The candidate was not saved."))
    else:
        st.error(
            result.get(
                "message",
                result.get("error", f"Task finished with status: {status}"),
            )
        )

    if candidate:
        filename = (
            candidate.get("tool_name")
            or candidate.get("name")
            or safe_filename(st.session_state.current_task)
        )
        description = candidate.get("description", "No description provided.")
        st.markdown(
            f'<div class="tool-head"><div class="fn">{html.escape(str(filename))}</div>'
            f'<div class="ds">{html.escape(str(description))}</div></div>',
            unsafe_allow_html=True,
        )

        source = candidate.get("code", "")
        if source:
            st.code(source, language="python", line_numbers=True)
            st.download_button(
                "Download Python file",
                data=source,
                file_name=filename if str(filename).endswith(".py") else f"{filename}.py",
                mime="text/x-python",
                key=f"download_{hash(source)}",
            )

        validation = result.get("validation")
        if validation is not None:
            with st.expander("Validation report", expanded=(status == "validation_failed")):
                st.json(validation)

        if result.get("saved") is not None:
            with st.expander("Registry details"):
                st.json(result["saved"])


def run_agent(task: str) -> None:
    """Run ToolSmith's agent and display actionable errors."""

    if not isinstance(task, str) or not task.strip():
        st.warning("Describe the tool you need, then press Generate.")
        return

    task = task.strip()
    st.session_state.current_task = task
    st.session_state.runs += 1
    add_activity("Task submitted", task)

    try:
        from agent import process_task

        with st.spinner(
            "Searching approved tools, generating, validating, and saving..."
        ):
            result = process_task(task)

        if not isinstance(result, dict):
            raise TypeError("Agent returned an invalid response.")

        st.session_state.agent_result = result
        status = result.get("status", "unknown")

        if status in ("success", "existing_tools_found"):
            add_activity("Agent finished", f"Workflow status: {status}", "ok")
        else:
            error = result.get("error") or result.get("message") or status
            add_activity("Agent failed", str(error), "bad")

        # Keep successfully generated tools in the session library.
        candidate = result.get("tool") or result.get("candidate")

        if (
            status == "success"
            and isinstance(candidate, dict)
            and candidate.get("code")
        ):
            known = {
                item.get("code")
                for item in st.session_state.saved_tools
            }

            if candidate["code"] not in known:
                st.session_state.saved_tools.insert(
                    0,
                    {
                        "name": (
                            candidate.get("tool_name")
                            or candidate.get("name")
                            or safe_filename(task)
                        ),
                        "task": task,
                        "code": candidate["code"],
                        "saved_at": datetime.now().strftime("%d %b, %H:%M"),
                    },
                )

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"

        st.session_state.agent_result = {
            "status": "failed",
            "stage": "application",
            "error": error_message,
            "message": "ToolSmith could not complete the request.",
        }

        add_activity("Application error", error_message, "bad")
        st.error(f"ToolSmith error: {error_message}")



def use_example(text: str) -> None:
    st.session_state.home_task = text


def stat_card(number: str, label: str) -> str:
    return f'<div class="stat"><div class="n">{html.escape(number)}</div><div class="l">{html.escape(label)}</div></div>'


# -----------------------------
# Sidebar navigation
# -----------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">✦</div>'
        '<div><div class="brand-name">ToolSmith</div>'
        '<div class="brand-sub">AI-powered tool creation</div></div></div>',
        unsafe_allow_html=True,
    )

    page_options = ["Home", "New Task", "Tool Library"]
    selected_page = st.radio(
        "Navigation",
        page_options,
        index=page_options.index(st.session_state.page)
        if st.session_state.page in page_options
        else 0,
        label_visibility="collapsed",
    )
    st.session_state.page = selected_page

    st.write("")
    st.markdown(
        f'<div class="side-stat"><b>{len(st.session_state.saved_tools)}</b>'
        f'<span>tools saved this session</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("Describe a task, review the result, reuse approved tools.")


# -----------------------------
# Pages
# -----------------------------
if st.session_state.page == "Home":
    st.markdown('<div class="hero">Forge tools from<br>plain language.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Tell ToolSmith what you need. It checks approved tools first, '
        'and only generates, validates, and saves a new one when nothing fits.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="composer"):
        home_task = st.text_area(
            "Task description",
            placeholder="Example: Create a tool that converts Celsius to Fahrenheit...",
            height=120,
            key="home_task",
            label_visibility="collapsed",
        )
        btn_col, chip_col = st.columns([1, 3.2], gap="medium", vertical_alignment="center")
        with btn_col:
            if st.button("✦  Generate tool", type="primary", use_container_width=True, key="home_generate"):
                st.session_state.page = "Home"
                run_agent(home_task)
        with chip_col:
            st.markdown('<div class="chips">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            examples = [
                ("Celsius → Fahrenheit", "Create a tool that converts Celsius to Fahrenheit."),
                ("Clean a CSV", "Create a tool that removes duplicate rows from a CSV file."),
                ("Slugify text", "Create a tool that turns a title into a URL-friendly slug."),
            ]
            for col, (label, text) in zip((c1, c2, c3), examples):
                with col:
                    st.button(label, key=f"ex_{label}", on_click=use_example, args=(text,), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    m1, m2, m3 = st.columns(3, gap="medium")
    last_status = (st.session_state.agent_result or {}).get("status", "none yet").replace("_", " ")
    m1.markdown(stat_card(str(len(st.session_state.saved_tools)), "Tools saved this session"), unsafe_allow_html=True)
    m2.markdown(stat_card(str(st.session_state.runs), "Tasks run"), unsafe_allow_html=True)
    m3.markdown(stat_card(last_status.capitalize(), "Last result"), unsafe_allow_html=True)

    st.write("")
    st.markdown("### How a task flows")
    render_pipeline(st.session_state.agent_result)

    if st.session_state.agent_result:
        st.markdown("### Latest result")
        show_result(st.session_state.agent_result)

    st.markdown("### Recent activity")
    if not st.session_state.activity:
        st.caption("Nothing yet. Submit a task above and its progress will show up here.")
    else:
        with st.container(border=True):
            rows = "".join(
                f'<div class="activity-row"><div class="pip {html.escape(item.get("tone", "info"))}"></div>'
                f'<div><div class="activity-title">{html.escape(item["title"])}</div>'
                f'<div class="activity-desc">{html.escape(item["description"])}</div>'
                f'<div class="activity-time">{html.escape(item["time"])}</div></div></div>'
                for item in st.session_state.activity[:5]
            )
            st.markdown(rows, unsafe_allow_html=True)


elif st.session_state.page == "New Task":
    st.markdown('<div class="hero small">Create your next tool.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Submit a task to the agent. Review the matching tools, '
        'validation results, and generated source below.</div>',
        unsafe_allow_html=True,
    )

    if "new_task_text" not in st.session_state:
        st.session_state.new_task_text = st.session_state.current_task

    def _clear_task() -> None:
        st.session_state.new_task_text = ""
        st.session_state.current_task = ""
        st.session_state.agent_result = None

    with st.container(border=True, key="composer"):
        task = st.text_area(
            "Task description",
            placeholder="Describe the task you want the tool to perform...",
            height=140,
            key="new_task_text",
            label_visibility="collapsed",
        )
        col1, col2, _ = st.columns([1.4, 1, 3])
        with col1:
            create_clicked = st.button("✦  Generate tool", type="primary", use_container_width=True)
        with col2:
            st.button("Clear", use_container_width=True, on_click=_clear_task)

    if create_clicked:
        run_agent(task)

    if st.session_state.agent_result:
        st.write("")
        show_result(st.session_state.agent_result)
    else:
        st.write("")
        render_pipeline(None)


else:  # Tool Library
    st.markdown(
        '<div class="hero small">Your tool library.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Approved tools from the backend registry, '
        'along with tools generated in this session.</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search saved tools",
        placeholder="Search by tool name or description...",
        label_visibility="collapsed",
        key="library_search",
    )

    # Load approved tools from the persistent backend registry.
    registry_tools = []

    try:
        from registry import load_registry

        registry_data = load_registry()
        registry_groups = registry_data.get("tools", {})

        if isinstance(registry_groups, dict):
            for tool_name, versions in registry_groups.items():
                if not isinstance(versions, list):
                    continue

                for tool in versions:
                    if not isinstance(tool, dict):
                        continue

                    validation = tool.get("validation", {})
                    if (
                        validation.get("passed") is True
                        and validation.get("status") == "success"
                    ):
                        registry_tools.append({
                            **tool,
                            "name": tool.get("name", tool_name),
                            "description": tool.get("description", ""),
                            "source": "Backend registry",
                        })

    except Exception as exc:
        st.error(f"Could not load the backend registry: {exc}")

    # Merge session tools without duplicating registry entries.
    merged_tools = {}
    for tool in registry_tools:
        key = (
            tool.get("name", ""),
            tool.get("version"),
        )
        merged_tools[key] = tool

    for item in st.session_state.saved_tools:
        key = (item.get("name", ""), item.get("version"))
        if key not in merged_tools:
            merged_tools[key] = {
                **item,
                "source": "Current session",
            }

    all_tools = list(merged_tools.values())

    filtered = [
        tool for tool in all_tools
        if query.lower() in (
            str(tool.get("name", ""))
            + " "
            + str(tool.get("description", ""))
            + " "
            + str(tool.get("task", ""))
        ).lower()
    ]

    st.caption(f"{len(filtered)} approved or session tools shown")

    if not filtered:
        st.info("No matching tools found. Generate a tool or change your search.")
    else:
        for index, tool in enumerate(filtered):
            name = tool.get("name", "Unnamed tool")
            description = tool.get("description", "")
            version = tool.get("version", "Session")
            source = tool.get("source", "Backend registry")

            with st.container(border=True):
                first, second = st.columns(
                    [4, 1],
                    vertical_alignment="center",
                )

                with first:
                    st.markdown(f"**`{name}`**")
                    if description:
                        st.caption(description)
                    st.caption(f"Version: {version} · Source: {source}")

                with second:
                    if st.button(
                        "Open",
                        key=f"open_library_{index}_{name}",
                        use_container_width=True,
                    ):
                        st.session_state.current_task = description or name
                        st.session_state.new_task_text = description or name
                        st.session_state.agent_result = {
                            "status": "success",
                            "message": f"Opened {name} from the Tool Library.",
                            "tool": {
                                "tool_name": name,
                                "description": description,
                                "code": tool.get("code", ""),
                            },
                        }
                        st.session_state.page = "New Task"
                        st.rerun()

                with st.expander("View source"):
                    code = tool.get("code", "")
                    code_path = tool.get("code_path")

                    if not code and code_path:
                        from pathlib import Path

                        source_path = Path(__file__).resolve().parent / code_path
                        try:
                            source_path = source_path.resolve()
                            generated_root = (
                                Path(__file__).resolve().parent
                                / "tools"
                                / "generated"
                            ).resolve()

                            if (
                                source_path.is_relative_to(generated_root)
                                and source_path.is_file()
                            ):
                                code = source_path.read_text(encoding="utf-8")
                            else:
                                st.error("Tool source path is invalid.")
                        except OSError as exc:
                            st.error(f"Could not read tool source: {exc}")

                    if code:
                        st.code(code, language="python", line_numbers=True)
                        st.download_button(
                            "Download Python file",
                            data=code,
                            file_name=f"{name}.py",
                            mime="text/x-python",
                            key=f"download_library_{index}_{name}",
                        )
                    else:
                        st.warning("Source code is not available for this entry.")

        else:
         for index, item in enumerate(filtered):
            with st.container(border=True):
                first, second = st.columns([4, 1], vertical_alignment="center")
                with first:
                    st.markdown(f"**`{item.get('name', 'Unnamed tool')}`**")
                    st.caption(item.get("task", ""))
                    st.caption(f"Saved {item.get('saved_at', 'during this session')}")
                with second:
                    if st.button("Open", key=f"open_saved_{index}", use_container_width=True):
                        st.session_state.current_task = item.get("task", "")
                        st.session_state.new_task_text = item.get("task", "")
                        st.session_state.agent_result = {
                            "status": "success",
                            "message": "Opened a tool saved in this session.",
                            "tool": {
                                "tool_name": item.get("name", "saved_tool.py"),
                                "description": item.get("task", ""),
                                "code": item.get("code", ""),
                            },
                        }
                        st.session_state.page = "New Task"
                        st.rerun()
                with st.expander("View source"):
                    st.code(item.get("code", ""), language="python", line_numbers=True)

st.caption("ToolSmith · Review generated code before use. Validation does not guarantee that code is safe or correct.")
