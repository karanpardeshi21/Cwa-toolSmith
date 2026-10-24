import streamlit as st

st.set_page_config(
    page_title="ToolSmith",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(125deg, #f8f9fc, #edf2fc);
}
.block-container {
    max-width: 1600px;
    padding: 18px 24px 30px;
}
.stApp { color: #11162e; }
h1, h2, h3, p { color: #11162e; }
[data-testid="stHorizontalBlock"] { gap: 12px; }

.panel {
    background: rgba(255,255,255,.76);
    border: 1px solid rgba(220,226,240,.85);
    border-radius: 24px;
    padding: 22px;
    height: 100%;
}
.sidebar {
    background: rgba(255,255,255,.72);
    border: 1px solid #e9edf5;
    border-radius: 28px;
    padding: 24px 18px;
    min-height: 890px;
}
.brand {
    font-size: 25px;
    font-weight: 750;
    color: #080d24;
    margin: 24px 0 32px;
}
.brand span { color: #392dff; font-size: 35px; }
.nav {
    padding: 13px 12px;
    margin: 8px 0;
    border-radius: 14px;
    font-size: 15px;
    color: #4b5265;
}
.nav.active { background: #edf0ff; color: #1725ce; }
.hero {
    font-size: clamp(35px, 3.6vw, 59px);
    line-height: 1.12;
    letter-spacing: -2.5px;
    font-weight: 800;
    color: #080808;
    margin: 30px 0 12px;
}
.gradient {
    background: linear-gradient(90deg,#6c2cff,#458eff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    color: #858d9e;
    font-size: 18px;
    line-height: 1.5;
}
.stats-title {
    font-size: 21px;
    font-weight: 700;
    line-height: 1.35;
    margin: 28px 0 55px;
}
.stat-number { font-size: 27px; font-weight: 750; }
.stat-label { font-size: 12px; color: #737d99; }
.stat-divider { border-left: 1px solid #dce2f2; padding-left: 12px; }
.section-title {
    font-size: 20px;
    font-weight: 750;
    margin-bottom: 22px;
    color: #101010;
}
.activity {
    display: flex;
    gap: 13px;
    margin-bottom: 28px;
}
.activity-icon {
    min-width: 42px;
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #eef1ff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
}
.activity-title { font-weight: 650; font-size: 14px; }
.activity-desc { color: #7b8497; font-size: 12px; margin-top: 5px; }
.time { color: #8790a2; font-size: 11px; white-space: nowrap; }
.code-window {
    background: #1d2024;
    color: #f4f5f7;
    border-radius: 15px;
    padding: 17px;
    min-height: 245px;
    overflow: hidden;
    font-family: monospace;
    font-size: 12px;
    line-height: 1.9;
    white-space: pre-wrap;
}
.pill {
    background: #e4fbef;
    color: #06743e;
    padding: 8px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
}
.run-step {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 18px 0;
    font-size: 13px;
}
.done { color: #0acb70; font-size: 19px; }
.wait { color: #aeb6c6; font-size: 19px; }
.stButton button {
    border-radius: 13px;
    min-height: 42px;
    border: 1px solid #e0e5ef;
    background: rgba(255,255,255,.8);
    color: #11162e;
}
.stButton button:hover {
    border-color: #969bff;
    color: #3025dc;
}
.stTextArea textarea {
    background: rgba(255,255,255,.8);
    border: 1px solid #e4e8f1;
    border-radius: 16px;
}
@media(max-width: 900px) {
    .sidebar { min-height: auto; }
    .hero { margin-top: 8px; }
}
</style>
""", unsafe_allow_html=True)

# -------- Main page layout --------
sidebar, main = st.columns([0.78, 4.5], gap="medium")

with sidebar:
    st.markdown("""
    <div class="sidebar">
        <div style="font-size:12px;color:#a1a7b5">🔴 🟡 🟢</div>
        <div class="brand"><span>✦</span> ToolSmith</div>
        <div class="nav active">⌂ &nbsp; Home</div>
        <div class="nav">⊞ &nbsp; New Task</div>
        <div class="nav">▤ &nbsp; Tool Library</div>
        <div style="margin-top:245px;font-size:80px;text-align:center;
                    color:#d5dcff">◇</div>
        <div style="font-size:22px;font-weight:750;line-height:1.25;
                    margin-top:10px">
            Build<br>Smarter Tools<br>Every Day.
        </div>
    </div>
    """, unsafe_allow_html=True)

with main:
    top_left, top_right = st.columns([1.65, 1], gap="medium")

    with top_left:
        st.markdown("""
        <div class="hero">
            Turn ideas into <span class="gradient">tools.</span>
        </div>
        <div class="subtitle">
            ToolSmith is an AI agent that creates, tests, and reuses
            its own tools to solve real tasks.
        </div>
        """, unsafe_allow_html=True)

        task = st.text_area(
            "Task",
            placeholder="Describe what you want to do...",
            height=105,
            label_visibility="collapsed",
            key="task_input",
        )

        generate_col, attach_col = st.columns([5, 1])

        with attach_col:
            st.button("＋", help="Attachment placeholder")

        with generate_col:
            generate = st.button(
                "↑  Generate tool",
                type="primary",
                use_container_width=True,
            )

        if generate:
            if task.strip():
                st.session_state["task"] = task.strip()
                st.session_state["run_status"] = "Planning"
                st.info(
                    "Task captured. Connect your tool-generation "
                    "backend to generate a real candidate."
                )
            else:
                st.warning("Enter a task first.")

    with top_right:
        st.markdown("""
        <div class="panel" style="min-height:300px;
             background:linear-gradient(140deg,#e9eaff,#f8faff)">
            <div style="font-size:12px;color:#6d79b1">
                TOOL LIBRARY
            </div>
            <div class="stats-title">
                A growing library<br>of capabilities.
            </div>
            <div style="font-size:65px;text-align:right;
                        color:#a8b9ff">◉</div>
            <hr style="border-color:#dce2f2">
            <div style="display:flex;justify-content:space-between;
                        gap:8px">
                <div><div class="stat-number">24</div>
                    <div class="stat-label">Tools Created</div></div>
                <div class="stat-divider">
                    <div class="stat-number">18</div>
                    <div class="stat-label">Tests Passed</div></div>
                <div class="stat-divider">
                    <div class="stat-number">92%</div>
                    <div class="stat-label">Success Rate</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    activity_col, code_col, run_col = st.columns(
        [1.12, 1.22, 0.75],
        gap="small",
    )

    with activity_col:
        st.markdown("""
        <div class="panel">
            <div class="section-title">Recent Activity</div>
            <div class="activity">
                <div class="activity-icon">✦</div>
                <div><div class="activity-title">Received task</div>
                <div class="activity-desc">
                    “Extract tables from this PDF and save as CSV”
                </div></div>
            </div>
            <div class="activity">
                <div class="activity-icon" style="background:#e6fbf1">
                    &lt;/&gt;
                </div>
                <div><div class="activity-title">Generated tool</div>
                <div class="activity-desc">Created extract_pdf_tables.py</div>
                </div>
            </div>
            <div class="activity">
                <div class="activity-icon" style="background:#e6fbf1">
                    ✓
                </div>
                <div><div class="activity-title">Running tests</div>
                <div class="activity-desc">3/3 tests passed</div></div>
            </div>
            <div class="activity" style="margin-bottom:0">
                <div class="activity-icon" style="background:#f0f2f6">
                    ▱
                </div>
                <div><div class="activity-title">Tool saved</div>
                <div class="activity-desc">
                    Added to library for future use
                </div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with code_col:
        st.markdown("""
        <div class="panel">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;gap:8px;margin-bottom:15px">
                <div style="font-size:13px;font-weight:650">
                    🐍 &nbsp; extract_pdf_tables.py
                </div>
                <span class="pill">✓ Test Passed</span>
            </div>
            <div class="code-window"><span style="color:#9da8b7">
1</span>  <span style="color:#ff827c">import</span> fitz
<span style="color:#9da8b7">2</span>  <span style="color:#ff827c">import</span> pandas <span style="color:#69c9ff">as</span> pd
<span style="color:#9da8b7">3</span>
<span style="color:#9da8b7">4</span>  <span style="color:#ff827c">def</span> extract_tables(pdf_path):
<span style="color:#9da8b7">5</span>      doc = fitz.open(pdf_path)
<span style="color:#9da8b7">6</span>      tables = []
<span style="color:#9da8b7">7</span>      <span style="color:#ff827c">for</span> page <span style="color:#ff827c">in</span> doc:
<span style="color:#9da8b7">8</span>          <span style="color:#ff827c">for</span> table <span style="color:#ff827c">in</span> page.find_tables():
<span style="color:#9da8b7">9</span>              df = pd.DataFrame(table.extract())
<span style="color:#9da8b7">10</span>             tables.append(df)
<span style="color:#9da8b7">11</span>
<span style="color:#9da8b7">12</span> <span style="color:#ff827c">return</span> pd.concat(tables)
            </div>
        """, unsafe_allow_html=True)

        run_tests_col, save_col = st.columns(2)

        with run_tests_col:
            if st.button("▷  Run Tests", use_container_width=True):
                st.info("Connect the test runner to execute real tests.")

        with save_col:
            if st.button("▱  Save to Library", use_container_width=True):
                st.info("Connect the registry writer to save approved tools.")

    with run_col:
        st.markdown("""
        <div class="panel" style="min-height:245px">
            <div class="section-title">Current Run</div>
            <div style="display:flex;align-items:center;
                        justify-content:center;margin:20px 0">
                <div style="width:105px;height:105px;border-radius:50%;
                    border:9px solid #e8ebf5;
                    border-top-color:#8f9dff;
                    border-right-color:#4c78ff;
                    border-bottom-color:#8f9dff;
                    display:flex;align-items:center;
                    justify-content:center;font-size:23px;
                    font-weight:750">3/4</div>
            </div>
            <div class="run-step"><span class="done">●</span> Planning</div>
            <div class="run-step"><span class="done">●</span> Generating tool</div>
            <div class="run-step"><span style="color:#3479ff">◯</span>
                Running tests</div>
            <div class="run-step"><span class="wait">◯</span>
                Saving to library</div>
        </div>
        """, unsafe_allow_html=True)
