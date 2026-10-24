import streamlit as st

st.set_page_config(page_title="ToolSmith", page_icon="✦", layout="wide")

# Demo state: keeps button actions visible while this session is open
for key, default in {
    "page": "Home", "task": "", "generated": False,
    "tests_run": False, "saved": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "activity" not in st.session_state:
    st.session_state.activity = [
        ("Received task", "Extract tables from this PDF and save as CSV", "2 min ago"),
        ("Generated tool", "Created extract_pdf_tables.py", "1 min ago"),
        ("Running tests", "Demo: 3/3 tests passed", "50 sec ago"),
        ("Tool saved", "Added to library for future use", "Just now"),
    ]

st.markdown("""
<style>
#MainMenu,footer,header{visibility:hidden}
[data-testid="stAppViewContainer"]{background:linear-gradient(120deg,#f8f9fd,#edf2fc)}
.block-container{max-width:1600px;padding:18px 24px 30px}
[data-testid="stHorizontalBlock"]{gap:14px}
.panel{background:rgba(255,255,255,.84);border:1px solid #e5e9f3;border-radius:23px;padding:22px;height:100%}
.brand{font-size:25px;font-weight:800;margin:10px 0 30px;color:#11152c}
.hero{font-size:clamp(34px,3.5vw,58px);line-height:1.1;font-weight:850;letter-spacing:-2px;color:#080a10;margin:18px 0 12px}
.gradient{background:linear-gradient(90deg,#6b2cff,#458eff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{font-size:17px;line-height:1.5;color:#858da0}
.stat-num{font-size:27px;font-weight:800;color:#10152d}.stat-label{font-size:12px;color:#737d96}
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
