"""ToolSmith - Streamlit UI.

Two tabs:
  Create  - describe a task; reuse an approved tool or generate, validate
            and save a new one.
  Library - browse, search, download and run approved tools stored in the
            registry (tool_registry/registry.json).

Backend contract:
  agent.process_task(task) -> dict whose "status" is one of
    "existing_tools_found" | "success" | "validation_failed" |
    "save_failed" | "failed"
  executor.execute_tool(name, input_data: dict) -> dict
  registry.load_registry() -> {"tools": {name: [version records]}}

Run with:  streamlit run app.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
GENERATED_ROOT = (BASE_DIR / "tools" / "generated").resolve()
MAX_TASK_CHARS = 1000

EXAMPLES = [
    "Convert Celsius to Fahrenheit",
    "Remove duplicate rows from a CSV file",
    "Turn a title into a URL-friendly slug",
]

st.set_page_config(page_title="ToolSmith", page_icon="🔧", layout="centered")

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
# Session state
# ---------------------------------------------------------------------------
# "task_input" is the key of the text area. It may only be changed from
# widget callbacks (on_click), never after the widget is drawn.
st.session_state.setdefault("task_input", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("pending_run", False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_demo_input(tool: dict) -> tuple[str, str]:
    """Returns (json_demo_str, literal_demo_str) for tool input."""
    tests = tool.get("tests")
    if isinstance(tests, list) and len(tests) > 0 and isinstance(tests[0], dict) and "input" in tests[0]:
        test_in = tests[0]["input"]
        json_demo = json.dumps(test_in)
        if isinstance(test_in, dict):
            val = next(iter(test_in.values())) if test_in else []
            literal_demo = str(val)
        else:
            literal_demo = str(test_in)
        return json_demo, literal_demo

    name = str(tool.get("name") or tool.get("tool_name") or "").lower()
    schema = tool.get("input_schema") or {}
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}

    if "number" in name or "sum" in name or "add" in name:
        if "a" in props and "b" in props:
            return '{"a": 10, "b": 25}', "[10, 25]"
        return '{"a": 5, "b": 15}', "[5, 15]"
    if "deviation" in name or "stat" in name or "mean" in name or "average" in name:
        return '{"numbers": [10, 20, 30, 40, 50]}', "[10, 20, 30, 40, 50]"
    if "duplicate" in name or "dedupe" in name or "search" in name:
        return '{"ids": [1, 2, 2, 3, 4, 4, 5]}', "[1, 2, 2, 3, 4, 4, 5]"
    if "sort" in name:
        return '{"list": [64, 34, 25, 12, 22, 11, 90]}', "[64, 34, 25, 12, 22, 11, 90]"
    if "celsius" in name or "temperature" in name:
        return '{"celsius": 25}', "25"
    if "csv" in name or "clean" in name or "row" in name:
        return '{"csv_content": "name, age\\nAlice, 30\\n, \\nBob, 25"}', '"name, age\\nAlice, 30\\n, \\nBob, 25"'
    if "slug" in name or "title" in name or "url" in name or "text" in name:
        return '{"title": "ToolSmith Hackathon Project!"}', '"ToolSmith Hackathon Project!"'

    if props:
        sample = {}
        literal_sample = []
        for prop, spec in props.items():
            ptype = spec.get("type") if isinstance(spec, dict) else "string"
            if ptype == "array":
                sample[prop] = [1, 2, 3, 4, 5]
                literal_sample = [1, 2, 3, 4, 5]
            elif ptype == "number" or ptype == "integer":
                sample[prop] = 42
                literal_sample.append(42)
            else:
                sample[prop] = "sample_value"
                literal_sample.append("sample_value")
        return json.dumps(sample), str(literal_sample if len(literal_sample) > 1 else (literal_sample[0] if literal_sample else "sample"))

    return '{"a": 10, "b": 20}', "[10, 20]"


def short_key(text: str) -> str:
    """Stable widget key (Python's built-in hash() changes every run)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def tool_label(tool: dict) -> str:
    return str(tool.get("tool_name") or tool.get("name") or "unnamed_tool")


def get_candidate(result: dict) -> dict | None:
    cand = result.get("tool") or result.get("candidate")
    return cand if isinstance(cand, dict) else None


def load_code(tool: dict) -> str:
    """Return tool source: inline 'code' if present, else read 'code_path'.

    Only files inside tools/generated are ever read.
    """
    code = tool.get("code")
    if isinstance(code, str) and code.strip():
        return code

    rel = tool.get("code_path")
    if not isinstance(rel, str) or not rel.strip():
        return ""

    try:
        path = (BASE_DIR / rel).resolve()
        if (
            path.is_relative_to(GENERATED_ROOT)
            and path.is_file()
            and path.suffix == ".py"
        ):
            return path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        pass
    return ""


def load_library() -> tuple[list[dict], str | None]:
    """Latest approved version of every tool in the registry."""
    try:
        from registry import load_registry

        data = load_registry()
    except Exception as exc:
        return [], f"Could not load the registry: {type(exc).__name__}: {exc}"

    tools_by_name = data.get("tools", {})
    library: list[dict] = []

    for name, versions in tools_by_name.items():
        if not isinstance(versions, list):
            continue

        approved = [
            record
            for record in versions
            if isinstance(record, dict)
            and isinstance(record.get("validation"), dict)
            and record["validation"].get("passed") is True
            and isinstance(record.get("version"), int)
            and not isinstance(record.get("version"), bool)
        ]
        if not approved:
            continue

        latest = max(approved, key=lambda record: record["version"])
        library.append(
            {
                **latest,
                "name": latest.get("name", name),
                "approved_versions": len(approved),
            }
        )

    library.sort(key=lambda t: str(t.get("created_at", "")), reverse=True)
    return library, None


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
def use_example(text: str) -> None:
    """Callback: fill the text box (allowed because it runs before the rerun)."""
    st.session_state.task_input = text


def queue_run() -> None:
    """Callback: ask the Create tab to run the agent again."""
    st.session_state.pending_run = True


def run_agent(task: str) -> None:
    task = task.strip()

    if not task:
        st.warning("Describe the tool you need first.")
        return

    if len(task) > MAX_TASK_CHARS:
        st.warning(f"Keep the description under {MAX_TASK_CHARS} characters.")
        return

    try:
        # Imported lazily so the UI still loads (and explains the problem)
        # when a backend dependency such as `groq` is not installed.
        from agent import process_task

        with st.spinner("Searching, generating and validating..."):
            result = process_task(task)

        if not isinstance(result, dict):
            raise TypeError("The agent returned an unexpected response.")

    except Exception as exc:
        result = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }

    st.session_state.result = result


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_run_box(
    tool_name: str,
    key: str,
    input_schema: object = None,
    tool_record: dict | None = None,
) -> None:
    """Run a registered tool through executor.execute_tool."""
    with st.expander("▶️ Run this tool & Input", expanded=True):
        st.caption(
            "Runs the approved tool in a separate Python process. Process "
            "isolation is used — review the code before running."
        )

        tool_meta_str = f"{tool_name} {tool_record.get('description', '') if tool_record else ''} {str(input_schema)}".lower()
        is_file_tool = any(kw in tool_meta_str for kw in ["csv", "pdf", "image", "jpeg", "jpg", "png", "file", "excel", "txt", "xlsx"])

        input_type_tabs = ["📁 File Upload"] if is_file_tool else []
        input_type_tabs.extend(["JSON object", "Python literal (list, etc.)", "Raw Text / String"])

        selected_tab = st.radio(
            "Input Mode",
            input_type_tabs,
            horizontal=True,
            key=f"mode_{key}",
        )

        payload = None

        if selected_tab == "📁 File Upload":
            st.info("📂 **Smart File Import**: Upload a file for this tool.")
            allowed_types = ["csv", "txt"]
            if "pdf" in tool_meta_str:
                allowed_types.append("pdf")
            if any(img in tool_meta_str for img in ["image", "jpeg", "jpg", "png", "convert"]):
                allowed_types.extend(["png", "jpg", "jpeg"])
            if "excel" in tool_meta_str or "xlsx" in tool_meta_str:
                allowed_types.extend(["xlsx", "xls"])

            uploaded_file = st.file_uploader("Choose a file...", type=allowed_types, key=f"file_{key}")
            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                try:
                    payload = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    payload = file_bytes

            if not st.button("Run Tool", key=f"run_{key}", type="primary"):
                return
            if payload is None:
                st.warning("Please upload a file first.")
                return

        else:
            json_demo, literal_demo = get_demo_input(tool_record or {})
            active_demo = (
                json_demo
                if selected_tab == "JSON object"
                else (literal_demo if selected_tab == "Python literal (list, etc.)" else "name, age\nAlice, 30\n, \nBob, 25")
            )

            col_demo, col_btn = st.columns([3, 1], vertical_alignment="center")
            with col_demo:
                st.caption("💡 **Demo Input Example:**")
                st.code(active_demo, language="json" if selected_tab == "JSON object" else "python" if selected_tab == "Python literal (list, etc.)" else "text")
            with col_btn:
                if st.button("📋 Use Demo", key=f"load_demo_{key}", use_container_width=True):
                    st.session_state[f"in_{key}"] = active_demo

            if input_schema:
                with st.expander("View Input Schema", expanded=False):
                    st.json(input_schema)

            textarea_key = f"in_{key}"
            if textarea_key not in st.session_state:
                st.session_state[textarea_key] = active_demo

            raw = st.text_area(
                "Input data",
                key=textarea_key,
                height=90,
            )

            if not st.button("Run Tool", key=f"run_{key}", type="primary"):
                return

            # Parse input based on selected mode
            try:
                if selected_tab == "JSON object":
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        st.error('JSON input must be an object, e.g. {"a": 2, "b": 3}.')
                        return
                elif selected_tab == "Python literal (list, etc.)":
                    try:
                        payload = json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        payload = eval(raw, {"__builtins__": None}, {})
                        if not isinstance(payload, (dict, list, tuple, int, float, str, bool, type(None))):
                            st.error("Invalid Python literal input.")
                            return
                else:
                    payload = raw
            except Exception as exc:
                st.error(f"Invalid input: {type(exc).__name__}: {exc}")
                return

        try:
            from executor import execute_tool

            outcome = execute_tool(tool_name, payload)
        except Exception as exc:
            st.error(f"{type(exc).__name__}: {exc}")
            return

        if outcome.get("status") == "success":
            st.success(f"Ran {outcome.get('tool_name')} v{outcome.get('version')}.")
            st.json(outcome.get("output", {}))
        else:
            st.error(outcome.get("error", "Tool execution failed."))


def _render_tool_contents(tool: dict, prefix: str, runnable: bool) -> None:
    name = tool_label(tool)
    code = load_code(tool)
    key = f"{prefix}_{short_key(name + str(tool.get('version', '')) + code)}"

    meta = []
    if tool.get("version") is not None:
        meta.append(f"version {tool['version']}")
    if tool.get("similarity_score") is not None:
        meta.append(f"match {tool['similarity_score']}")
    if tool.get("approved_versions", 0) > 1:
        meta.append(f"{tool['approved_versions']} approved versions")
    if meta:
        st.caption(" · ".join(meta))

    if tool.get("description"):
        st.write(tool["description"])

    if tool.get("compatibility_reason"):
        st.caption(tool["compatibility_reason"])

    if not code:
        st.warning("Source code is not available for this tool.")
        return

    if runnable:
        render_run_box(name, key, tool.get("input_schema"), tool_record=tool)

    with st.expander("📄 View Source Code"):
        st.code(code, language="python", line_numbers=True)

    st.download_button(
        "Download .py",
        data=code,
        file_name=f"{name}.py",
        mime="text/x-python",
        key=f"dl_{key}",
    )


def render_tool(tool: dict, prefix: str, runnable: bool, compact: bool = False) -> None:
    """One tool card: compact expander or full container."""
    name = tool_label(tool)
    version = tool.get("version", 1)
    desc = tool.get("description", "")
    short_desc = (desc[:65] + "...") if len(desc) > 65 else desc

    if compact:
        label = f"🔧 `{name}` (v{version})" + (f" — {short_desc}" if short_desc else "")
        with st.expander(label, expanded=False):
            _render_tool_contents(tool, prefix, runnable)
    else:
        with st.container(border=True):
            st.markdown(f"**`{name}`**")
            _render_tool_contents(tool, prefix, runnable)


def render_result(result: dict) -> None:
    status = result.get("status", "unknown")

    if result.get("retrieval_warning"):
        st.warning(result["retrieval_warning"])

    # --- Reused approved tools -------------------------------------------
    if status == "existing_tools_found":
        st.success("Found existing approved tools. Nothing new was generated.")
        st.caption(result.get("message", ""))

        for tool in result.get("tools") or []:
            render_tool(tool, prefix="found", runnable=True)

        rejected = result.get("rejected_tools") or []
        if rejected:
            with st.expander(f"{len(rejected)} candidate(s) rejected"):
                for item in rejected:
                    st.markdown(
                        f"- `{item.get('name', 'Unknown')}` - "
                        f"{item.get('reason', '')}"
                    )
        return

    # --- Newly generated, validated and saved ----------------------------
    cand = get_candidate(result)

    if status == "success":
        st.success(result.get("message", "Tool generated, validated and saved."))
        saved = result.get("saved") or {}
        if saved:
            st.caption(
                f"Saved as {saved.get('tool_name')} v{saved.get('version')} "
                f"({saved.get('code_path')})"
            )

    elif status == "validation_failed":
        st.error(
            result.get("message")
            or "The generated tool failed validation and was not saved."
        )
        errors = (result.get("validation") or {}).get("errors") or []
        for err in errors:
            st.markdown(f"- {err}")

    elif status == "save_failed":
        st.error(result.get("message") or "Validation passed, but saving failed.")
        saved = result.get("saved") or {}
        if saved.get("error"):
            st.markdown(f"- {saved['error']}")

    else:
        message = (
            result.get("error")
            or result.get("message")
            or f"Failed with status: {status}"
        )
        st.error(message)
        if "GroqClientError" in message or "GROQ_API_KEY" in message:
            st.info(
                "Check that GROQ_API_KEY is set in the .env file in the "
                "project root, then restart the app."
            )

    if cand:
        # Only a saved (registered) tool can be run through the executor.
        render_tool(cand, prefix="gen", runnable=(status == "success"))

        tests = cand.get("tests")
        if isinstance(tests, list) and tests:
            with st.expander(f"Generated test cases ({len(tests)})"):
                st.json(tests)

    if result.get("validation") is not None:
        with st.expander(
            "Validation report",
            expanded=(status == "validation_failed"),
        ):
            st.json(result["validation"])

    if status not in ("success", "existing_tools_found"):
        st.button("Try again", on_click=queue_run)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
st.title("ToolSmith")
st.caption(
    "Describe a task. ToolSmith reuses an approved tool or builds and tests a new one."
)

create_tab, library_tab = st.tabs(["Create", "Library"])

with create_tab:
    st.text_area(
        "What should the tool do?",
        key="task_input",
        height=110,
        max_chars=MAX_TASK_CHARS,
        placeholder="Example: Add two numbers",
    )

    example_cols = st.columns(len(EXAMPLES))
    for col, text in zip(example_cols, EXAMPLES):
        col.button(
            text,
            on_click=use_example,
            args=(text,),
            key=f"ex_{short_key(text)}",
        )

    generate_clicked = st.button("Generate tool", type="primary")
    retry_requested = st.session_state.pop("pending_run", False)

    if generate_clicked or retry_requested:
        run_agent(st.session_state.task_input)

    if st.session_state.result:
        st.divider()
        render_result(st.session_state.result)

with library_tab:
    library, library_error = load_library()

    if library_error:
        st.error(library_error)

    query = st.text_input(
        "Search tools",
        placeholder="Search by name or description",
        key="library_search",
    )
    q = query.strip().lower()

    shown = [
        tool
        for tool in library
        if not q
        or q in f"{tool.get('name', '')} {tool.get('description', '')}".lower()
    ]

    st.caption(f"{len(shown)} approved tool(s)")

    if not shown and not library_error:
        st.info("No tools yet. Generate one in the Create tab.")

    for tool in shown:
        render_tool(tool, prefix="lib", runnable=True, compact=True)

st.caption(
    "Generated code is tested, not guaranteed safe. Review it before using it."
)