import streamlit as st
import time
from datetime import datetime

# ToolSmith — single-file Streamlit UI
# Run: streamlit run app.py

st.set_page_config(
    page_title="ToolSmith",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Theme / CSS -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ink: #111827;
        --muted: #7b8495;
        --line: #e7eaf0;
        --blue: #5268f5;
        --blue-soft: #eef0ff;
        --green: #16834a;
        --green-soft: #e7f9ef;
        --surface: rgba(255,255,255,.82);
    }

    html { scroll-behavior: smooth !important; }
    [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse at 82% 0%, rgba(221,232,250,.62), transparent 33%),
          radial-gradient(ellipse at 5% 45%, rgba(238,235,251,.48), transparent 30%),
          #f8f9fb;
        color: var(--ink);
        font-family: 'DM Sans', 'Inter', sans-serif;
        scroll-behavior: smooth;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { right: 1rem; }
    [data-testid="stMainBlockContainer"] {
        padding-top: 1.35rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,.78);
        border-right: 1px solid rgba(226,230,238,.8);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    .brand {
        display:flex; align-items:center; gap:10px;
        padding: 8px 10px 24px 10px;
        color:#111827; font-size:22px; font-weight:700; letter-spacing:-.8px;
    }
    .brand-mark {
        display:inline-flex; align-items:center; justify-content:center;
        width:32px; height:32px; font-size:29px; line-height:1;
        color:#101b59;
    }
    .eyebrow {
        text-transform:uppercase; letter-spacing:1.7px;
        font-size:11px; font-weight:700; color:#7c8598; margin-bottom:12px;
    }
    .hero-title {
        font-size:clamp(36px, 4.2vw, 58px); line-height:1.04;
        letter-spacing:-2.4px; font-weight:700; color:#111318;
        margin:0 0 13px 0;
    }
    .hero-title .accent { color:#6075d7; }
    .subhead {
        color:#858d9d; font-size:17px; line-height:1.55;
        max-width:700px; margin:0 0 26px 0;
    }
    .panel {
        background:var(--surface); border:1px solid rgba(226,230,238,.88);
        border-radius:22px; padding:22px 24px;
        box-shadow:0 8px 30px rgba(28,39,70,.025);
        backdrop-filter:blur(16px);
    }
    .panel-title {
        font-size:17px; font-weight:700; letter-spacing:-.45px;
        margin:0 0 16px 0; color:#171a22;
    }
    .muted { color:var(--muted); }
    .metric {
        padding:3px 10px 3px 0;
        border-right:1px solid #e1e5ee;
    }
    .metric:last-child { border-right:none; }
    .metric-value { font-size:27px; font-weight:700; letter-spacing:-1px; color:#101b59; }
    .metric-label { color:#788195; font-size:12px; margin-top:1px; }
    .status-pill {
        display:inline-block; border-radius:999px; padding:6px 11px;
        background:var(--green-soft); color:var(--green); font-size:12px; font-weight:600;
    }
    .activity-row {
        display:flex; align-items:flex-start; gap:13px;
        padding:13px 0; border-bottom:1px solid #edf0f5;
    }
    .activity-row:last-child { border-bottom:0; padding-bottom:0; }
    .activity-icon {
        width:38px; height:38px; border-radius:14px; flex:0 0 38px;
        display:flex; align-items:center; justify-content:center;
        background:#f0f1ff; color:#5368ed; font-size:17px; font-weight:700;
    }
    .activity-icon.green { background:#e6f9ef; color:#16834a; }
    .activity-icon.gray { background:#f1f3f6; color:#252b36; }
    .activity-main { font-size:13px; font-weight:600; color:#171a22; }
    .activity-sub { font-size:12px; color:#858d9d; margin-top:3px; }
    .tool-card {
        background:rgba(255,255,255,.82); border:1px solid #e7eaf0;
        border-radius:17px; padding:17px; height:100%;
    }
    .tool-name { font-size:14px; font-weight:700; margin-bottom:5px; }
    .tool-desc { font-size:12px; color:#7b8495; line-height:1.45; min-height:34px; }
    .tag {
        display:inline-block; border-radius:999px; background:#f1f3f7;
        color:#697386; padding:4px 9px; font-size:10px; margin:8px 4px 0 0;
    }
    .code-head {
        display:flex; align-items:center; justify-content:space-between;
        font-size:13px; font-weight:600; margin-bottom:10px;
    }
    .code-window {
        background:#171a1f; color:#e6e8ec; border-radius:15px;
        padding:17px 18px; overflow-x:auto; font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
        font-size:11px; line-height:1.8; white-space:pre;
    }
    .code-comment { color:#858d9d; }
    .code-blue { color:#7cc8ff; }
    .code-red { color:#ff8a8a; }
    div.stButton > button {
        border-radius:12px; border:1px solid #e1e5ed; background:rgba(255,255,255,.9);
        color:#151923; padding:.55rem 1rem; min-height:40px;
        font-weight:600; transition:all .18s ease;
    }
    div.stButton > button:hover {
        border-color:#aeb9ff; color:#3048d8; background:#f7f8ff;
        transform:translateY(-1px); box-shadow:0 5px 14px rgba(53,70,160,.08);
    }
    div.stButton > button[kind="primary"] {
        background:#171a1f; color:white; border-color:#171a1f;
    }
    div.stButton > button[kind="primary"]:hover {
        background:#2a2e36; border-color:#2a2e36; color:white;
    }
    div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
        border:1px solid #e4e8ef; border-radius:13px; background:rgba(255,255,255,.86);
    }
    div[data-testid="stTextArea"] textarea:focus, div[data-testid="stTextInput"] input:focus {
        border-color:#aab6ff; box-shadow:0 0 0 2px rgba(91,112,245,.1);
    }
    div[data-testid="stProgressBar"] > div > div { background:#6478f5; }
    .small-note { font-size:11px; color:#9299a7; }
    hr { border-color:#e8ebf1 !important; }
    @media (max-width: 900px) {
        .hero-title { letter-spacing:-1.5px; }
        .panel { padding:17px; border-radius:18px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Session state -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "task_text" not in st.session_state:
    st.session_state.task_text = ""
if "runs" not in st.session_state:
    st.session_state.runs = [
        {"task": "Extract tables from PDF", "tool": "extract_pdf_tables.py", "status": "Passed", "time": "2 min ago"},
        {"task": "Generate tool: web_scraper.py", "tool": "web_scraper.py", "status": "Passed", "time": "18 min ago"},
        {"task": "Analyze product data", "tool": "analyze_csv.py", "status": "Saved", "time": "1 hr ago"},
    ]
if "tools" not in st.session_state:
    st.session_state.tools = [
        {"name":"extract_pdf_tables.py","desc":"Extract tables from PDF files and save as CSV.","category":"Files","icon":"▤","uses":12},
        {"name":"web_scraper.py","desc":"Collect structured data from websites.","category":"Web","icon":"◎","uses":7},
        {"name":"analyze_csv.py","desc":"Analyze tabular data and create quick summaries.","category":"Data","icon":"▥","uses":5},
        {"name":"fetch_api_data.py","desc":"Fetch and process data from REST APIs.","category":"API","icon":"⌘","uses":4},
    ]
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = "extract_pdf_tables.py"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">✦</span><span>ToolSmith</span></div>', unsafe_allow_html=True)
    nav_items = [("⌂", "Home"), ("＋", "New Task"), ("▤", "Tool Library")]
    for symbol, label in nav_items:
        if st.button(f"{symbol}   {label}", key=f"nav_{label}", use_container_width=True,
                     type="primary" if st.session_state.page == label else "secondary"):
            st.session_state.page = label
            st.rerun()
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="border:1px solid #e8ebf4;border-radius:18px;padding:18px 15px;background:linear-gradient(145deg,#f1f2ff,#fbfcff);">
          <div style="font-size:32px;color:#8796df;margin-bottom:12px;">◇</div>
          <div style="font-size:18px;font-weight:700;line-height:1.25;color:#101b59;">Build smarter tools.</div>
          <div style="font-size:12px;line-height:1.5;color:#7b8495;margin-top:8px;">Create once. Test automatically. Reuse whenever you need.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:22px'></div><div class='small-note'>OPEN SOURCE · BUILD · TEST · GROW</div>", unsafe_allow_html=True)

# ----------------------------- Shared helpers -----------------------------
def render_code():
    st.markdown(
        """
        <div class="code-window"><span class="code-comment">1</span>  <span class="code-red">import</span> fitz  <span class="code-comment"># PyMuPDF</span>
<span class="code-comment">2</span>  <span class="code-red">import</span> pandas <span class="code-red">as</span> pd

<span class="code-comment">3</span>
<span class="code-comment">4</span>  <span class="code-red">def</span> <span class="code-blue">extract_tables</span>(pdf_path: str) -> pd.DataFrame:
<span class="code-comment">5</span>      doc = fitz.open(pdf_path)
<span class="code-comment">6</span>      tables = []
<span class="code-comment">7</span>      <span class="code-red">for</span> page <span class="code-red">in</span> doc:
<span class="code-comment">8</span>          <span class="code-red">for</span> table <span class="code-red">in</span> page.find_tables():
<span class="code-comment">9</span>              tables.append(pd.DataFrame(table.extract()))
<span class="code-comment">10</span>     <span class="code-red">return</span> pd.concat(tables, ignore_index=True)</div>
        """,
        unsafe_allow_html=True,
    )

def activity(icon, title, subtitle, time_label, tone=""):
    st.markdown(
        f"""<div class="activity-row">
        <div class="activity-icon {tone}">{icon}</div>
        <div style="flex:1;min-width:0;">
          <div class="activity-main">{title}</div>
          <div class="activity-sub">{subtitle}</div>
        </div>
        <div class="activity-sub" style="white-space:nowrap;">{time_label}</div>
        </div>""",
        unsafe_allow_html=True,
    )

def page_heading(eyebrow, title, subtitle):
    st.markdown(
        f'<div class="eyebrow">{eyebrow}</div><h1 class="hero-title">{title}</h1><p class="subhead">{subtitle}</p>',
        unsafe_allow_html=True,
    )

# ----------------------------- Home -----------------------------
if st.session_state.page == "Home":
    left, right = st.columns([2.25, 1], gap="large")
    with left:
        st.markdown('<div class="eyebrow">TOOLSMITH</div><h1 class="hero-title">Turn ideas into <span class="accent">tools.</span></h1><p class="subhead">An AI agent that creates, tests, and reuses its own tools to solve real tasks.</p>', unsafe_allow_html=True)
        with st.container(border=True):
            task = st.text_area("Describe what you want to do", placeholder="e.g. Extract tables from a PDF and save as CSV...", height=105, label_visibility="collapsed", key="home_task")
            c1, c2 = st.columns([5, 1])
            with c1:
                st.caption("Automatic workflow · Plan → Build → Test → Save")
            with c2:
                if st.button("↑", type="primary", use_container_width=True, key="home_submit"):
                    if task.strip():
                        st.session_state.task_text = task.strip()
                        st.session_state.page = "New Task"
                        st.rerun()
                    else:
                        st.warning("Describe a task first.")
    with right:
        st.markdown(
            """
            <div class="panel" style="height:100%;background:linear-gradient(145deg,#e9edff,#f8faff);">
              <div style="font-size:30px;color:#7184df;margin-bottom:12px;">◇</div>
              <div style="font-size:19px;font-weight:700;color:#101b59;line-height:1.3;">A growing library<br>of capabilities.</div>
              <div style="height:28px"></div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;border-top:1px solid #dce2f3;padding-top:18px;">
                <div class="metric"><div class="metric-value">24</div><div class="metric-label">Tools created</div></div>
                <div class="metric"><div class="metric-value">18</div><div class="metric-label">Tests passed</div></div>
                <div class="metric"><div class="metric-value">92%</div><div class="metric-label">Success rate</div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    col_activity, col_code, col_run = st.columns([1.1, 1.25, .85], gap="medium")
    with col_activity:
        st.markdown('<div class="panel-title">Recent Activity</div>', unsafe_allow_html=True)
        with st.container(border=True):
            activity("✦", "Received task", "Extract tables from a PDF and save as CSV", "2 min ago")
            activity("</>", "Generated tool", "Created extract_pdf_tables.py", "1 min ago", "green")
            activity("✓", "Running tests", "3/3 tests passed", "50 sec ago", "green")
            activity("▱", "Tool saved", "Added to library for future use", "Just now", "gray")
    with col_code:
        with st.container(border=True):
            st.markdown('<div class="code-head"><span>extract_pdf_tables.py</span><span class="status-pill">✓ Tests passed</span></div>', unsafe_allow_html=True)
            render_code()
            b1, b2 = st.columns(2)
            with b1:
                if st.button("▶ Run tests", key="home_tests", use_container_width=True):
                    st.session_state.last_result = "Tests passed: 3/3"
                    st.toast("All 3 tests passed")
            with b2:
                if st.button("▱ Save to Library", key="home_save", use_container_width=True):
                    if not any(t["name"] == "extract_pdf_tables.py" for t in st.session_state.tools):
                        st.session_state.tools.insert(0, {"name":"extract_pdf_tables.py","desc":"Extract tables from PDF files and save as CSV.","category":"Files","icon":"▤","uses":1})
                    st.toast("Tool is available in your library")
    with col_run:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Current Run</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:28px;font-weight:700;color:#101b59;margin:4px 0;">3/4 <span style="font-size:12px;color:#7b8495;font-weight:500;">steps complete</span></div>', unsafe_allow_html=True)
            st.progress(.75)
            st.markdown("<div class='activity-sub'>✓ Planning</div><div class='activity-sub' style='margin-top:9px;'>✓ Generating tool</div><div class='activity-sub' style='margin-top:9px;color:#5368ed;'>◉ Running tests</div><div class='activity-sub' style='margin-top:9px;'>○ Saving to library</div>", unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="panel-title" style="font-size:14px;">Example tasks</div>', unsafe_allow_html=True)
            for example in ["Extract tables from a PDF", "Analyze a CSV file", "Scrape product data"]:
                if st.button(example, key=f"example_{example}", use_container_width=True):
                    st.session_state.task_text = example
                    st.session_state.page = "New Task"
                    st.rerun()

# ----------------------------- New Task -----------------------------
elif st.session_state.page == "New Task":
    main, side = st.columns([1.65, 1], gap="large")
    with main:
        page_heading("NEW TASK", 'What do you want to <span class="accent">do?</span>', "Describe your task in natural language. ToolSmith will create, test, and save the right tool for you.")
        with st.container(border=True):
            task_text = st.text_area("Task description", value=st.session_state.task_text, placeholder="e.g. Extract tables from a PDF and save as CSV...", height=180, label_visibility="collapsed", key="new_task_input")
            a, b = st.columns([1, 5])
            with a:
                st.caption("＋ Attach")
            with b:
                st.caption("Python tool · Automated tests")
            if st.button("Run Task  →", type="primary", use_container_width=True, key="run_task"):
                if not task_text.strip():
                    st.error("Enter a task description before running.")
                else:
                    st.session_state.task_text = task_text.strip()
                    with st.spinner("Planning, generating and testing your tool..."):
                        time.sleep(.7)
                    generated_name = "custom_tool.py"
                    st.session_state.last_result = f"Task received: {task_text.strip()}"
                    st.session_state.runs.insert(0, {"task": task_text.strip(), "tool": generated_name, "status": "Ready for review", "time": "Just now"})
                    st.success("Task processed in UI demo mode. Connect your agent backend to generate and execute real tools.")
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Example tasks</div>', unsafe_allow_html=True)
        examples = [
            ("▤", "Extract tables", "from a PDF"),
            ("◎", "Scrape a website", "for product data"),
            ("▥", "Analyze a CSV file", "and create insights"),
            ("▧", "Convert images", "to searchable text"),
        ]
        cols = st.columns(4, gap="small")
        for i, (ico, title, desc) in enumerate(examples):
            with cols[i]:
                if st.button(f"{ico}\n{title}\n{desc}", key=f"new_example_{i}", use_container_width=True):
                    st.session_state.task_text = f"{title} {desc}"
                    st.rerun()
    with side:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Task workflow</div>', unsafe_allow_html=True)
            steps = [("1", "Understand task", "Analyze the request"), ("2", "Generate tool", "Create Python code"), ("3", "Run tests", "Validate behavior"), ("4", "Save to library", "Reuse next time")]
            for n, title, sub in steps:
                st.markdown(f'<div class="activity-row"><div class="activity-icon">{n}</div><div><div class="activity-main">{title}</div><div class="activity-sub">{sub}</div></div></div>', unsafe_allow_html=True)
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="code-head"><span>Example generated tool</span><span class="status-pill">Preview</span></div>', unsafe_allow_html=True)
            render_code()
            st.caption("Preview only — connect your generation and test runner for live results.")

# ----------------------------- Tool Library -----------------------------
else:
    page_heading("TOOL LIBRARY", 'Your tools, ready to <span class="accent">use.</span>', "A growing collection of tools created and tested by ToolSmith.")
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search = st.text_input("Search tools", placeholder="Search by name or capability...", label_visibility="collapsed")
    with filter_col:
        categories = ["All", "Files", "Web", "Data", "API"]
        category = st.selectbox("Category", categories, label_visibility="collapsed")
    filtered = [
        tool for tool in st.session_state.tools
        if (search.lower() in (tool["name"] + " " + tool["desc"]).lower())
        and (category == "All" or tool["category"] == category)
    ]
    list_col, detail_col = st.columns([1.5, 1], gap="large")
    with list_col:
        if not filtered:
            st.info("No tools match your search.")
        for tool in filtered:
            with st.container(border=True):
                icon_col, text_col, action_col = st.columns([.45, 2.6, .8], vertical_alignment="center")
                with icon_col:
                    st.markdown(f'<div class="activity-icon">{tool["icon"]}</div>', unsafe_allow_html=True)
                with text_col:
                    st.markdown(f'<div class="tool-name">{tool["name"]}</div><div class="tool-desc">{tool["desc"]}</div><span class="tag">{tool["category"]}</span><span class="tag">{tool["uses"]} uses</span>', unsafe_allow_html=True)
                with action_col:
                    if st.button("Select", key=f"select_{tool['name']}", use_container_width=True):
                        st.session_state.selected_tool = tool["name"]
                        st.rerun()
                    if st.button("▶ Run", key=f"run_{tool['name']}", use_container_width=True):
                        st.toast(f"Run requested for {tool['name']} (demo mode)")
    with detail_col:
        selected = next((t for t in st.session_state.tools if t["name"] == st.session_state.selected_tool), None)
        if selected is None and st.session_state.tools:
            selected = st.session_state.tools[0]
            st.session_state.selected_tool = selected["name"]
        if selected:
            with st.container(border=True):
                st.markdown(f'<div class="panel-title">{selected["name"]}</div><div class="muted" style="font-size:13px;line-height:1.5;">{selected["desc"]}</div><div style="margin:12px 0;"><span class="tag">{selected["category"]}</span><span class="tag">Python</span></div>', unsafe_allow_html=True)
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Times used", selected["uses"])
                with m2:
                    st.metric("Tests passed", "100%")
                st.markdown('<div class="code-head"><span>Code preview</span><span class="small-note">Python</span></div>', unsafe_allow_html=True)
                render_code()
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                t1, t2 = st.columns(2)
                with t1:
                    if st.button("▶ Run Tool", use_container_width=True, key="detail_run"):
                        st.toast(f"Run requested for {selected['name']} (demo mode)")
                with t2:
                    if st.button("＋ Use in New Task", type="primary", use_container_width=True, key="use_new"):
                        st.session_state.task_text = f"Use {selected['name']} to: "
                        st.session_state.page = "New Task"
                        st.rerun()

st.markdown("<div style='height:22px'></div><div class='small-note' style='text-align:center;'>TOOLSMITH · BUILD · TEST · GROW</div>", unsafe_allow_html=True)
