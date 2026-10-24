"""ToolSmith - minimal UI.

Two tabs:
  Create  - describe a task, get an existing or newly generated tool
  Library - browse, search and download tools

Backend contract (unchanged from the original app.py):
  agent.process_task(task: str) -> dict with a "status" of
    "existing_tools_found" | "success" | "validation_failed" | other (error)
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# Config - adjust these if your backend uses different names
# ---------------------------------------------------------------------------
MAX_TASK_CHARS = 1000

# Optional: the function in executor.py that runs a tool.
# Expected call: RUN_FUNCTION(code: str, user_input: str) -> anything printable.
# If executor.py or the function does not exist, the "Run" box is simply hidden.
RUN_FUNCTION_NAMES = ("run_tool", "execute_tool", "execute")

# Optional: functions in registry.py that list saved tools.
# Each should return a list of dicts (name, description, code, version...).
REGISTRY_LIST_NAMES = ("list_tools", "get_all_tools", "list_approved_tools")

EXAMPLES = [
    "Convert Celsius to Fahrenheit",
    "Remove duplicate rows from a CSV file",
    "Turn a title into a URL-friendly slug",
]

st.set_page_config(page_title="ToolSmith", page_icon="🔧", layout="centered")

# One small style block: tighter width, quieter chrome. Nothing else.
st.markdown(
    """
    <style>
      #MainMenu, footer {visibility: hidden;}
      .block-container {max-width: 820px; padding-top: 2rem;}
      div.stButton > button {border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
st.session_state.setdefault("task", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("session_tools", [])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def short_key(text: str) -> str:
    """Stable widget key (Python's built-in hash() changes every run)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def filename_from(task: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", task.lower())[:5]
    return ("_".join(words) or "generated_tool") + ".py"


def get_candidate(result: dict) -> dict | None:
    cand = result.get("tool") or result.get("candidate")
    return cand if isinstance(cand, dict) else None


def tool_name(tool: dict, fallback: str = "tool.py") -> str:
    return tool.get("tool_name") or tool.get("name") or fallback


def get_runner():
    """Return the executor function if one exists, else None."""
    try:
        import executor
    except Exception:
        return None
    for name in RUN_FUNCTION_NAMES:
        fn = getattr(executor, name, None)
        if callable(fn):
            return fn
    return None


def load_registry_tools() -> list[dict]:
    """Tools stored by the backend. Falls back to nothing if unavailable."""
    try:
        import registry
    except Exception:
        return []
    for name in REGISTRY_LIST_NAMES:
        fn = getattr(registry, name, None)
        if callable(fn):
            try:
                tools = fn()
                if isinstance(tools, dict):
                    tools = list(tools.values())
                return [t for t in tools if isinstance(t, dict)]
            except Exception:
                return []
    return []


def run_agent(task: str) -> None:
    task = task.strip()
    if not task:
        st.warning("Describe the tool you need first.")
        return
    if len(task) > MAX_TASK_CHARS:
        st.warning(f"Keep the description under {MAX_TASK_CHARS} characters.")
        return

    st.session_state.task = task
    try:
        from agent import process_task

        with st.status("Searching, generating and validating...", expanded=False) as status:
            result = process_task(task)
            if not isinstance(result, dict):
                raise TypeError("The agent returned an unexpected response.")
            status.update(label="Done", state="complete")
    except Exception as exc:  # show a readable error instead of a stack trace
        result = {
            "status": "error",
            "message": f"{type(exc).__name__}: {exc}",
        }

    st.session_state.result = result

    cand = get_candidate(result)
    if result.get("status") == "success" and cand and cand.get("code"):
        known = {t["code"] for t in st.session_state.session_tools}
        if cand["code"] not in known:
            st.session_state.session_tools.insert(
                0,
                {
                    "name": tool_name(cand, filename_from(task)),
                    "description": cand.get("description") or task,
                    "code": cand["code"],
                    "saved_at": datetime.now().strftime("%d %b %H:%M"),
                },
            )


def render_code_block(name: str, code: str) -> None:
    """Code, download button and optional run box for one tool."""
    key = short_key(code)
    st.code(code, language="python")

    left, right = st.columns([1, 3])
    with left:
        st.download_button(
            "Download .py",
            data=code,
            file_name=name if name.endswith(".py") else f"{name}.py",
            mime="text/x-python",
            key=f"dl_{key}",
        )

    runner = get_runner()
    if runner:
        with st.expander("Run this tool"):
            st.caption("This executes generated code. Review it before running.")
            value = st.text_input("Input", key=f"in_{key}")
            if st.button("Run", key=f"run_{key}"):
                try:
                    st.write(runner(code, value))
                except Exception as exc:
                    st.error(f"{type(exc).__name__}: {exc}")


def render_result(result: dict) -> None:
    status = result.get("status", "unknown")

    if result.get("retrieval_warning"):
        st.warning(result["retrieval_warning"])

    # Existing approved tools matched the task
    if status == "existing_tools_found":
        st.success("Found existing tools that match. Nothing new was generated.")
        tools = result.get("tools") or []
        if not tools:
            st.caption("No tool details were returned.")
        for tool in tools:
            title = tool_name(tool, tool.get("tool_name", "Unnamed tool"))
            meta = []
            if tool.get("version") is not None:
                meta.append(f"version {tool['version']}")
            if tool.get("similarity_score") is not None:
                meta.append(f"match {tool['similarity_score']}")
            with st.expander(f"{title}" + (f"  ({', '.join(meta)})" if meta else "")):
                if tool.get("description"):
                    st.write(tool["description"])
                if tool.get("code"):
                    render_code_block(title, tool["code"])
        return

    # Generated tool
    if status == "success":
        st.success(result.get("message", "Tool generated, validated and saved."))
    elif status == "validation_failed":
        st.error(result.get("message", "The generated tool failed validation and was not saved."))
    else:
        st.error(result.get("message") or result.get("error") or f"Failed with status: {status}")

    cand = get_candidate(result)
    if cand:
        name = tool_name(cand, filename_from(st.session_state.task))
        st.subheader(name)
        if cand.get("description"):
            st.write(cand["description"])
        if cand.get("code"):
            render_code_block(name, cand["code"])

    if result.get("validation") is not None:
        with st.expander("Validation report", expanded=(status == "validation_failed")):
            st.json(result["validation"])


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
st.title("ToolSmith")
st.caption("Describe a task. ToolSmith reuses an approved tool or builds and tests a new one.")

create_tab, library_tab = st.tabs(["Create", "Library"])

with create_tab:
    st.text_area(
        "What should the tool do?",
        key="task",
        height=110,
        max_chars=MAX_TASK_CHARS,
        placeholder="Example: Convert a list of temperatures from Celsius to Fahrenheit",
    )

    # Example chips fill the text box
    def _use_example(text: str) -> None:
        st.session_state.task = text

    cols = st.columns(len(EXAMPLES))
    for col, text in zip(cols, EXAMPLES):
        col.button(text, on_click=_use_example, args=(text,), use_container_width=True, key=f"ex_{short_key(text)}")

    if st.button("Generate tool", type="primary"):
        run_agent(st.session_state.task)

    if st.session_state.result:
        st.divider()
        render_result(st.session_state.result)

        if st.session_state.result.get("status") in ("validation_failed", "error", "failed"):
            if st.button("Try again"):
                run_agent(st.session_state.task)
                st.rerun()

with library_tab:
    backend_tools = load_registry_tools()
    session_tools = st.session_state.session_tools

    # Merge, de-duplicate by code
    seen: set[str] = set()
    all_tools: list[dict] = []
    for tool in session_tools + backend_tools:
        code = tool.get("code", "")
        marker = code or tool_name(tool)
        if marker in seen:
            continue
        seen.add(marker)
        all_tools.append(tool)

    query = st.text_input("Search tools", placeholder="Search by name or description")
    q = query.strip().lower()
    shown = [
        t for t in all_tools
        if not q or q in f"{tool_name(t)} {t.get('description', '')}".lower()
    ]

    if not shown:
        st.info("No tools yet. Generate one in the Create tab.")
    for tool in shown:
        name = tool_name(tool)
        with st.expander(name):
            if tool.get("description"):
                st.write(tool["description"])
            caption = [str(tool[k]) for k in ("version", "saved_at") if tool.get(k) is not None]
            if caption:
                st.caption(" | ".join(caption))
            if tool.get("code"):
                render_code_block(name, tool["code"])

st.caption("Generated code is tested, not guaranteed safe. Review it before using it.")
