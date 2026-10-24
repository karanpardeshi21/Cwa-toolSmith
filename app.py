import html
import re
from datetime import datetime

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
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 88% 3%, rgba(190, 205, 255, .32), transparent 32%),
            #f5f7fc;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1450px;
        padding: 2rem clamp(1rem, 3vw, 2.5rem) 3rem;
    }
    [data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid #e8ebf4;
    }
    [data-testid="stSidebar"] > div { padding-top: 1.4rem; }
    .brand {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -.8px;
        color: #111528;
        padding: .3rem .4rem 1.6rem;
    }
    .brand-mark { color: #6544ed; margin-right: .45rem; }
    .eyebrow {
        color: #6d73a1;
        text-transform: uppercase;
        letter-spacing: .14em;
        font-size: .72rem;
        font-weight: 700;
    }
    .hero {
        font-size: clamp(2.25rem, 4vw, 3.65rem);
        line-height: 1.05;
        letter-spacing: -.055em;
        font-weight: 800;
        color: #101322;
        margin: .65rem 0 .85rem;
    }
    .gradient {
        background: linear-gradient(95deg, #6c36ec, #3988f5);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .subtitle {
        max-width: 760px;
        color: #747d91;
        font-size: 1rem;
        line-height: 1.65;
        margin-bottom: 1.5rem;
    }
    .panel {
        background: rgba(255,255,255,.92);
        border: 1px solid #e7eaf3;
        border-radius: 20px;
        padding: 1.2rem;
        box-shadow: 0 10px 32px rgba(32, 48, 91, .045);
    }
    .panel-title {
        font-size: 1.1rem;
        font-weight: 750;
        letter-spacing: -.025em;
        color: #171a2b;
        margin-bottom: .8rem;
    }
    .muted { color: #7c8497; font-size: .88rem; }
    .metric {
        border: 1px solid #e6e9f5;
        background: linear-gradient(145deg, #e9ebff, #fff);
        border-radius: 20px;
        padding: 1.35rem;
        min-height: 150px;
    }
    .metric-number {
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -.05em;
        color: #202750;
        margin-top: .5rem;
    }
    .activity-row {
        padding: .8rem 0;
        border-bottom: 1px solid #edf0f6;
    }
    .activity-row:last-child { border-bottom: 0; }
    .activity-title { font-weight: 650; color: #24283a; }
    .activity-desc { font-size: .85rem; color: #7c8497; margin-top: .2rem; overflow-wrap: anywhere; }
    .code-label {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: .85rem;
        color: #59617a;
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 12px;
        min-height: 2.7rem;
        font-weight: 650;
        border-color: #e0e5f0;
    }
    div.stButton > button[kind="primary"] {
        background: #171923;
        border-color: #171923;
    }
    .stTextArea textarea, .stTextInput input {
        border-radius: 12px !important;
        background: #fff !important;
    }
    div[data-testid="stFileUploader"] {
        border-radius: 12px;
    }
    @media (max-width: 700px) {
        .block-container { padding: 1rem .8rem 2rem; }
        .hero { letter-spacing: -.04em; }
        .panel { padding: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
def add_activity(title: str, description: str) -> None:
    st.session_state.activity.insert(
        0,
        {
            "title": title,
            "description": description,
            "time": datetime.now().strftime("%d %b, %H:%M"),
        },
    )
    st.session_state.activity = st.session_state.activity[:8]


def safe_filename(task: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", task.lower())[:5]
    stem = "_".join(words) or "generated_tool"
    return f"{stem[:55]}.py"


def show_result(result: dict) -> None:
    """Render the actual response returned by agent.process_task."""
    status = result.get("status", "unknown")

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
        st.error(result.get("message", "Validation failed. Candidate was not saved."))
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
        st.markdown("### Generated tool")
        st.markdown(f"**{filename}**")
        st.write(description)

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
            st.markdown("#### Validation")
            st.json(validation)

        if result.get("saved") is not None:
            with st.expander("Saved registry details"):
                st.json(result["saved"])


def run_agent(task: str) -> None:
    if not task or not task.strip():
        st.warning("Enter a task description first.")
        return

    st.session_state.current_task = task.strip()
    add_activity("Task submitted", task.strip())

    try:
        from agent import process_task

        with st.spinner("Searching existing tools, then generating and validating if needed..."):
            result = process_task(task.strip())

        st.session_state.agent_result = result
        status = result.get("status", "unknown")
        add_activity("Agent finished", f"Workflow status: {status}")
    except Exception as exc:
        st.session_state.agent_result = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
        add_activity("Agent error", f"{type(exc).__name__}: {exc}")


# -----------------------------
# Sidebar navigation
# -----------------------------
with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">✦</span>ToolSmith</div>', unsafe_allow_html=True)
    st.caption("AI-powered tool creation")
    st.divider()

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

    st.divider()
    st.markdown("**Build smarter tools.**")
    st.caption("Describe a task, review the agent's result, and reuse approved tools.")


# -----------------------------
# Pages
# -----------------------------
if st.session_state.page == "Home":
    st.markdown('<div class="eyebrow">Welcome to ToolSmith</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Turn ideas into<br><span class="gradient">useful tools.</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Describe what you need in plain language. ToolSmith searches for approved tools first, then can generate, validate, and save a new candidate when needed.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### What do you want to build?")
            home_task = st.text_area(
                "Task description",
                placeholder="Example: Create a tool that converts Celsius to Fahrenheit...",
                height=125,
                key="home_task",
            )
            if st.button("✦  Generate tool", type="primary", use_container_width=True, key="home_generate"):
                st.session_state.page = "Home"
                run_agent(home_task)

    with right:
        st.markdown('<div class="metric"><div class="eyebrow">Your workspace</div><div class="metric-number">' + str(len(st.session_state.saved_tools)) + '</div><div class="muted">Tools saved in this browser session</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="panel"><div class="panel-title">How it works</div><div class="muted">01 · Search approved tools<br><br>02 · Generate a candidate if needed<br><br>03 · Validate before saving<br><br>04 · Review and download the result</div></div>', unsafe_allow_html=True)

    if st.session_state.agent_result:
        st.divider()
        st.markdown("## Latest result")
        show_result(st.session_state.agent_result)

    st.divider()
    st.markdown("### Recent activity")
    if not st.session_state.activity:
        st.caption("Your recent activity will appear here.")
    else:
        for item in st.session_state.activity[:5]:
            st.markdown(
                f'<div class="activity-row"><div class="activity-title">{html.escape(item["title"])}</div><div class="activity-desc">{html.escape(item["description"])}</div><div class="muted">{html.escape(item["time"])}</div></div>',
                unsafe_allow_html=True,
            )


elif st.session_state.page == "New Task":
    st.markdown('<div class="eyebrow">Create</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Create your <span class="gradient">next tool.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Submit a task to the real agent workflow. Review the returned tool candidates, validation results, and generated source code below.</div>', unsafe_allow_html=True)

    default_task = st.session_state.current_task
    task = st.text_area(
        "Task description",
        value=default_task,
        placeholder="Describe the task you want the tool to perform...",
        height=140,
        key="new_task_text",
    )
    col1, col2, _ = st.columns([1.4, 1, 3])
    with col1:
        create_clicked = st.button("✦  Generate tool", type="primary", use_container_width=True)
    with col2:
        clear_clicked = st.button("Clear", use_container_width=True)

    if create_clicked:
        run_agent(task)

    if clear_clicked:
        st.session_state.current_task = ""
        st.session_state.agent_result = None
        st.rerun()

    if st.session_state.agent_result:
        st.divider()
        show_result(st.session_state.agent_result)


else:  # Tool Library
    st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Your tool <span class="gradient">library.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Tools saved from this UI session. The backend registry remains the source of approved generated tools.</div>', unsafe_allow_html=True)

    query = st.text_input("Search saved tools", placeholder="Search by filename or task...")
    saved = st.session_state.saved_tools
    filtered = [
        item for item in saved
        if query.lower() in (item.get("name", "") + " " + item.get("task", "")).lower()
    ]

    if not filtered:
        st.info("No tools saved in this UI session yet. A successful agent result is saved by the backend registry; use the download option to keep a local copy.")
    else:
        for index, item in enumerate(filtered):
            with st.container(border=True):
                first, second = st.columns([4, 1])
                with first:
                    st.markdown(f"**{item.get('name', 'Unnamed tool')}**")
                    st.caption(item.get("task", ""))
                    st.caption(f"Saved {item.get('saved_at', 'during this session')}")
                with second:
                    if st.button("Open", key=f"open_saved_{index}", use_container_width=True):
                        st.session_state.current_task = item.get("task", "")
                        st.session_state.agent_result = {
                            "status": "success",
                            "message": "Opened a tool saved in this UI session.",
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

st.caption("ToolSmith · Generated code should be reviewed before use. Validation does not guarantee that code is safe or correct.")
