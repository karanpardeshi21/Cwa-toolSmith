.section-title{font-size:20px;font-weight:800;margin-bottom:20px;color:#111}
.activity{display:flex;gap:12px;margin:0 0 23px;align-items:flex-start}
.activity-icon{width:40px;min-width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#edf0ff;font-size:18px}
.activity-name{font-size:14px;font-weight:750;color:#151827}.activity-desc{font-size:12px;color:#7d8597;margin-top:5px}
.code-window{background:#1e2025;color:#f5f6fa;border-radius:15px;padding:18px;font:12px/1.9 monospace;white-space:pre-wrap;overflow:auto;min-height:250px}
.pill{display:inline-block;background:#e4fbef;color:#087342;padding:8px 12px;border-radius:14px;font-size:12px;font-weight:700}
.small-muted{font-size:12px;color:#7c8598}
div.stButton>button{border-radius:13px;min-height:43px;border:1px solid #e1e6f0;background:rgba(255,255,255,.9);color:#11152d;font-weight:600}
div.stButton>button:hover{border-color:#9aa4ff;color:#3829dd}
.stTextArea textarea{border-radius:16px!important;background:#fff!important;border:1px solid #e4e8f2!important;color:#14172a!important}
@media(max-width:900px){.hero{font-size:34px;letter-spacing:-1px}}
</style>
""", unsafe_allow_html=True)

sidebar, main = st.columns([0.78, 4.5], gap="medium")

with sidebar:
    st.markdown('<div class="panel" style="min-height:850px;padding:22px 15px;"><div style="font-size:12px">🔴 🟡 🟢</div><div class="brand">✦ ToolSmith</div>', unsafe_allow_html=True)
    for label, symbol in [("Home", "⌂"), ("New Task", "⊞"), ("Tool Library", "▤")]:
        if st.button(f"{symbol}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
    st.markdown('<div style="margin-top:180px;text-align:center;font-size:76px;color:#d5dcff">◇</div><div style="font-size:21px;font-weight:800;line-height:1.25;margin-top:8px;color:#11152d">Build<br>Smarter Tools<br>Every Day.</div></div>', unsafe_allow_html=True)

with main:
    if st.session_state.page == "Tool Library":
        st.markdown('<div class="hero">Your tool <span class="gradient">library.</span></div><div class="subtitle">Find and reuse approved tools.</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        if st.session_state.saved:
            st.markdown("**generated_tool.py**")
            st.caption("Demo saved tool. Connect registry.py to load persistent real tools.")
        else:
            st.info("No demo tools saved yet. Generate a task, run the demo test, then save.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        top_left, top_right = st.columns([1.65, 1], gap="medium")
        with top_left:
            st.markdown('<div class="hero">Turn ideas into <span class="gradient">tools.</span></div><div class="subtitle">ToolSmith is an AI agent that creates, tests, and reuses its own tools to solve real tasks.</div>', unsafe_allow_html=True)
            task = st.text_area("Task", placeholder="Describe what you want to do...", height=100, label_visibility="collapsed", key="task_input")
            attach_col, generate_col = st.columns([1, 5])
            with attach_col:
                st.file_uploader("Attach", label_visibility="collapsed", help="Attach a file", key="upload")
            with generate_col:
                clicked = st.button("↑  Generate tool", type="primary", use_container_width=True)
            if clicked:
                if task.strip():
                    st.session_state.task = task.strip()
                    st.session_state.generated = True
                    st.session_state.tests_run = False
                    st.session_state.saved = False
                    st.session_state.activity.insert(0, ("Received task", task.strip(), "Just now"))
                    st.success("Task received. Demo mode: the AI backend has not been called.")
                else:
                    st.warning("Enter a task first.")

        with top_right:
            st.markdown("""
            <div class="panel" style="min-height:300px;background:linear-gradient(140deg,#e8eaff,#f9faff)">
              <div class="small-muted">TOOL LIBRARY</div>
              <div style="font-size:22px;font-weight:800;line-height:1.3;margin:25px 0 55px;color:#11152d">A growing library<br>of capabilities.</div>
              <div style="font-size:64px;text-align:right;color:#a8b9ff;line-height:1">◉</div><hr style="border-color:#dce2f2">
              <div style="display:flex;justify-content:space-between;gap:8px">
                <div><div class="stat-num">24</div><div class="stat-label">Tools Created</div></div>
                <div style="border-left:1px solid #dce2f2;padding-left:12px"><div class="stat-num">18</div><div class="stat-label">Tests Passed</div></div>
                <div style="border-left:1px solid #dce2f2;padding-left:12px"><div class="stat-num">92%</div><div class="stat-label">Success Rate</div></div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        activity_col, code_col, run_col = st.columns([1.12, 1.22, 0.75], gap="small")

        with activity_col:
            st.markdown('<div class="panel"><div class="section-title">Recent Activity</div>', unsafe_allow_html=True)
            icons = ["✦", "</>", "✓", "▱"]
            for i, (name, desc, when) in enumerate(st.session_state.activity[:4]):
                st.markdown(f'<div class="activity"><div class="activity-icon">{icons[min(i,3)]}</div><div style="flex:1"><div class="activity-name">{name}</div><div class="activity-desc">{desc}</div></div><div class="small-muted">{when}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with code_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            file_name = "generated_tool.py" if st.session_state.generated else "extract_pdf_tables.py"
            pill = "✓ Demo Test Passed" if st.session_state.tests_run else "Demo Preview"
            st.markdown(f'<div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:15px"><b>🐍 {file_name}</b><span class="pill">{pill}</span></div>', unsafe_allow_html=True)
            sample_code = """1  import fitz  # PyMuPDF
2  import pandas as pd
3
4  def extract_tables(pdf_path):
5      doc = fitz.open(pdf_path)
6      tables = []
7      for page in doc:
8          for table in page.find_tables():
9              df = pd.DataFrame(table.extract())
10             tables.append(df)
11
12     return pd.concat(tables, ignore_index=True)"""
            st.markdown(f'<div class="code-window">{sample_code}</div></div>', unsafe_allow_html=True)
            test_col, save_col = st.columns(2)
            with test_col:
                if st.button("▷  Run Tests", use_container_width=True):
                    st.session_state.tests_run = True
                    st.info("Demo only: no real code tests were executed.")
            with save_col:
                if st.button("▱  Save to Library", use_container_width=True):
                    if st.session_state.generated and st.session_state.tests_run:
                        st.session_state.saved = True
                        st.success("Demo tool saved for this session.")
                    else:
                        st.warning("Generate a task and run the demo test first.")

        with run_col:
            progress = 4 if st.session_state.saved else 3 if st.session_state.tests_run else 2 if st.session_state.generated else 1
            st.markdown('<div class="panel" style="min-height:245px"><div class="section-title">Current Run</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;font-size:36px;font-weight:800;margin:20px 0;color:#26376e">{progress}/4</div>', unsafe_allow_html=True)
            for i, step in enumerate(["Planning", "Generating tool", "Running tests", "Saving to library"], 1):
                symbol, color = ("●", "#0acb70") if i < progress or (st.session_state.saved and i == 4) else ("◉", "#3479ff") if i == progress else ("○", "#aeb6c6")
                st.markdown(f'<div style="display:flex;gap:10px;margin:15px 0;font-size:13px;color:#252a3b"><span style="color:{color};font-size:18px">{symbol}</span>{step}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.caption("Prototype UI: statistics are sample values. AI generation, real testing, and persistent saving need backend integration.")

