
import streamlit as st
from datetime import datetime
import html, re, textwrap

st.set_page_config(page_title="ToolSmith", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

DEFAULTS = {
    "page": "Home", "saved_tools": [], "generated": False, "current_task": "",
    "generated_code": "", "generated_filename": "custom_tool.py", "tests_run": False,
    "test_results": {}, "search_tools": "",
    "activity": [
        {"title":"Received task","description":"Extract tables from this PDF and save as CSV","time":"2 min ago","kind":"spark"},
        {"title":"Generated tool","description":"Created extract_pdf_tables.py","time":"1 min ago","kind":"code"},
        {"title":"Running tests","description":"3/3 tests passed","time":"50 sec ago","kind":"check"},
        {"title":"Tool saved","description":"Added to library for future use","time":"Just now","kind":"folder"},
    ],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
#MainMenu,footer,header{visibility:hidden}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 88% 4%,#c6d8ff4d,transparent 32%),#f4f6fb}
.block-container{max-width:1720px;padding:18px 22px 32px}
[data-testid="stHorizontalBlock"]{gap:14px;align-items:stretch}
.shell{background:#ffffffbd;border:1px solid #ffffffed;border-radius:30px;padding:18px;box-shadow:0 24px 80px #2336640e;min-height:calc(100vh - 54px)}
.sidebar-panel{background:#ffffff99;border:1px solid #ffffffed;border-radius:26px;padding:18px 14px;min-height:calc(100vh - 92px)}
.traffic{font-size:14px;letter-spacing:3px;margin:0 0 26px 6px}.brand{font-size:23px;font-weight:800;letter-spacing:-.9px;margin:0 0 28px 3px;color:#0b0d14}.brand-mark{color:#101943;font-size:31px;margin-right:9px;vertical-align:-2px}
.side-promo{margin-top:130px;padding:18px 4px 8px;color:#101943}.promo-art{height:170px;display:flex;align-items:center;justify-content:center;color:#a9baff;font-size:100px;text-shadow:0 10px 25px #526fff30;transform:rotate(-12deg)}.promo-title{font-size:21px;line-height:1.2;font-weight:800;letter-spacing:-.7px;margin-top:8px}
.hero{font-size:clamp(36px,3.6vw,60px);line-height:1.06;font-weight:800;letter-spacing:-2.6px;color:#080a10;margin:20px 0 13px}.gradient{background:linear-gradient(95deg,#6429f5,#3d83ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.subtitle{font-size:17px;line-height:1.5;color:#8790a1;max-width:800px;margin-bottom:22px}
.panel{background:#ffffffc7;border:1px solid #e8ecf4;border-radius:24px;padding:20px;box-shadow:0 8px 30px #27385f06;min-width:0}.section-title{font-size:20px;font-weight:800;letter-spacing:-.65px;margin:0 0 18px;color:#101116}.small-muted{font-size:12px;color:#7e879c}
.stats-panel{border-radius:24px;border:1px solid #dfe5f7;padding:24px;background:linear-gradient(140deg,#e1e5ffeb,#f8faffeb);min-height:340px;overflow:hidden}.stats-title{font-size:21px;font-weight:700;color:#101943;line-height:1.28;margin-top:48px;letter-spacing:-.5px}
.orb{float:right;margin-top:-94px;margin-right:-5px;width:112px;height:132px;border-radius:48% 52%;transform:rotate(-22deg);background:radial-gradient(circle at 32% 25%,#fffffffa,#bfccffb0 45%,#8ba3ff24 72%);border:1px solid #ffffffbf;box-shadow:inset -9px -8px 25px #647aff29,0 12px 30px #5e7fff21}
.stat-row{clear:both;display:flex;justify-content:space-between;gap:8px;border-top:1px solid #dbe2f4;margin-top:62px;padding-top:23px}.stat{flex:1;padding-left:12px;border-left:1px solid #dbe2f4}.stat:first-child{padding-left:0;border-left:0}.stat-num{font-size:25px;font-weight:800;color:#101943;letter-spacing:-1px}.stat-label{font-size:11px;color:#65708f;margin-top:4px;white-space:nowrap}
.activity{display:flex;gap:13px;align-items:flex-start;margin:0 0 22px}.activity-icon{width:42px;min-width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700;color:#18285f;background:#edf0ff}.activity-icon.code{background:#e7fbf1;color:#121923}.activity-icon.check{background:#e4fff0;color:#00a94e}.activity-icon.folder{background:#f0f2f6;color:#161b27}.activity-name{font-size:14px;font-weight:700;color:#151722;margin-top:2px}.activity-desc{font-size:12px;color:#7d8596;margin-top:5px;line-height:1.4;overflow-wrap:anywhere}.activity-time{font-size:11px;color:#858da0;white-space:nowrap;margin-left:auto;padding-top:4px}
.code-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}.file-name{font-size:13px;font-weight:600;color:#161a27}.status-pill{display:inline-block;background:#e5fbef;color:#08763e;padding:8px 11px;border-radius:13px;font-size:12px;font-weight:600;white-space:nowrap}
.code-window{background:linear-gradient(135deg,#202329,#17191e);color:#f3f4f8;border-radius:15px;padding:16px 17px;min-height:245px;max-height:310px;overflow:auto;font:11px/1.75 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre;border:1px solid #ffffff14}.code-window .ln{color:#8d94a3;display:inline-block;width:23px;user-select:none}
.run-title{font-size:19px;font-weight:800;color:#101116;margin:0 0 22px}.run-flex{display:flex;align-items:center;gap:16px}.ring{width:112px;height:112px;min-width:112px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:relative;background:conic-gradient(#a7b5ff 0 76%,#edf0f7 76% 100%)}.ring:before{content:"";position:absolute;inset:9px;background:#fff;border-radius:50%}.ring span{position:relative;color:#101943;font-size:22px;font-weight:800}.step-list{font-size:12px;line-height:2.6;color:#171b29}.step-dot{display:inline-flex;width:17px;height:17px;border-radius:50%;align-items:center;justify-content:center;margin-right:8px;font-size:10px;font-weight:800}.done{background:#b9f3d1;color:#07853d}.active{border:2px solid #4385ff;color:#4385ff}.pending{border:2px solid #c5cad5;color:#c5cad5}
div.stButton>button{border-radius:13px;min-height:42px;border:1px solid #e1e6f0;background:#ffffffe6;color:#101326;font-weight:600;box-shadow:none}div.stButton>button:hover{border-color:#9aa9ff;color:#3e3ae8;background:#fff}div.stButton>button[kind="primary"]{background:#111318;color:#fff;border:1px solid #111318}div.stButton>button[kind="primary"]:hover{background:#30333a;color:#fff}
.stTextArea textarea,.stTextInput input{border-radius:15px!important;background:#fffffff0!important;border:1px solid #e5e9f2!important;color:#171a28!important}.stTextArea textarea{min-height:100px;padding:16px!important}div[data-testid="stFileUploader"] section{border:1px solid #e6eaf3;border-radius:13px;background:#fff;padding:8px}
.empty-state{padding:28px;border:1px dashed #dce2ee;border-radius:18px;text-align:center;color:#788196;background:#ffffff80}
@media(max-width:1100px){.block-container{padding:12px}.hero{letter-spacing:-1.7px}.stats-panel{min-height:300px}.side-promo{margin-top:60px}.stat-label{white-space:normal}}
@media(max-width:700px){.shell{padding:10px;border-radius:20px}.hero{font-size:36px;letter-spacing:-1.4px}.subtitle{font-size:15px}.panel{padding:16px}.stats-title{margin-top:22px}.stat-row{margin-top:35px}.stat-num{font-size:21px}.stat-label{font-size:10px}}
</style>
''', unsafe_allow_html=True)

def add_activity(title, description, kind="spark"):
    stamp = datetime.now().strftime("%H:%M")
    st.session_state.activity.insert(0, {"title":title,"description":description,"time":f"Today, {stamp}","kind":kind})
    st.session_state.activity = st.session_state.activity[:8]

def slugify(task):
    words = re.findall(r"[a-zA-Z0-9]+", task.lower())[:4]
    return ("_".join(words) or "custom_tool") + ".py"

def starter_code(task):
    safe_task = task.replace(chr(10), " ").replace(chr(34), "'")[:180]
    return "\n".join([
        "from pathlib import Path", "", "def run(input_path: str) -> dict:",
        f"    # Starter template for: {safe_task}",
        "    source = Path(input_path)", "    if not source.exists():",
        "        raise FileNotFoundError(f'Input file not found: {source}')", "",
        "    # TODO: implement and validate task-specific processing.",
        "    return {'input': str(source), 'exists': source.is_file(),",
        "            'message': 'Starter template ready for implementation'}", "",
        "if __name__ == '__main__':",
        "    print('Template loaded. Implement task-specific logic before production use.')",
    ])

def render_code(code):
    rows = [f'<span class="ln">{i:02d}</span>{html.escape(line)}' for i,line in enumerate(code.splitlines() or [""],1)]
    st.markdown('<div class="code-window">' + "\n".join(rows) + '</div>', unsafe_allow_html=True)

def checks(code):
    return {"Contains a run() function":"def run(" in code,
            "Checks whether input exists":"exists()" in code,
            "Has a main entry point":"if __name__" in code}

def activity_item(item):
    symbols={"spark":"✦","code":"‹/›","check":"☑","folder":"▱"}
    kind=item.get("kind","spark")
    st.markdown(f'<div class="activity"><div class="activity-icon {kind}">{symbols.get(kind,"✦")}</div><div style="flex:1;min-width:0"><div class="activity-name">{html.escape(item["title"])}</div><div class="activity-desc">{html.escape(item["description"])}</div></div><div class="activity-time">{html.escape(item["time"])}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="shell">',unsafe_allow_html=True)
nav_col, main_col = st.columns([.78,4.5],gap="medium")
with nav_col:
    st.markdown('<div class="sidebar-panel"><div class="traffic"><span style="color:#ff6259">●</span> <span style="color:#ffca4d">●</span> <span style="color:#28cf62">●</span></div><div class="brand"><span class="brand-mark">✦</span>ToolSmith</div></div>',unsafe_allow_html=True)
    for label,symbol in [("Home","⌂"),("New Task","⊞"),("Tool Library","▤")]:
        if st.button(f"{symbol}   {label}",key="nav_"+label,use_container_width=True,type="primary" if st.session_state.page==label else "secondary"):
            st.session_state.page=label
            st.rerun()
    st.markdown('<div class="side-promo"><div class="promo-art">◇</div><div class="promo-title">Build<br>Smarter Tools<br>Every Day.</div></div>',unsafe_allow_html=True)

with main_col:
    st.markdown('<div style="display:flex;justify-content:flex-end;margin:2px 4px 14px"><div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#182d43,#e3b88b);display:flex;align-items:center;justify-content:center;color:white;font-size:18px">◒</div></div>',unsafe_allow_html=True)

    if st.session_state.page=="Tool Library":
        st.markdown('<div class="hero">Your tool <span class="gradient">library.</span></div><div class="subtitle">Find, inspect, and reuse tools you have saved.</div>',unsafe_allow_html=True)
        sc,cc=st.columns([4,1])
        with sc: st.text_input("Search tools",placeholder="Search by tool name or task...",key="search_tools")
        with cc: st.markdown(f'<div class="panel" style="padding:14px;margin-top:7px;text-align:center"><div class="stat-num">{len(st.session_state.saved_tools)}</div><div class="stat-label">Saved tools</div></div>',unsafe_allow_html=True)
        q=st.session_state.search_tools.strip().lower()
        matches=[t for t in st.session_state.saved_tools if q in (t["name"]+" "+t["task"]).lower()]
        if not matches:
            st.markdown('<div class="empty-state"><div style="font-size:34px;margin-bottom:8px">▤</div><b>No matching tools yet</b><br>Generate a starter template, then save it here.</div>',unsafe_allow_html=True)
        for i,t in enumerate(matches):
            with st.container(border=True):
                a,b,c=st.columns([4,1,1])
                with a:
                    st.markdown(f"**{t['name']}**")
                    st.caption(t["task"])
                    st.caption(f"Saved {t['saved_at']} · Stored for this session")
                with b:
                    if st.button("Open",key=f"open_{i}",use_container_width=True):
                        st.session_state.generated_code=t["code"]; st.session_state.generated_filename=t["name"]; st.session_state.current_task=t["task"]; st.session_state.generated=True; st.session_state.page="New Task"; st.rerun()
                with c:
                    if st.button("Delete",key=f"delete_{i}",use_container_width=True):
                        st.session_state.saved_tools=[x for x in st.session_state.saved_tools if x["name"]!=t["name"]]
                        add_activity("Tool removed",f"Removed {t['name']} from this session","folder"); st.rerun()

    elif st.session_state.page=="New Task":
        st.markdown('<div class="hero">Create your <span class="gradient">next tool.</span></div><div class="subtitle">Describe the task in plain language. Review the starter, run basic checks, and save it for reuse.</div>',unsafe_allow_html=True)
        with st.container(border=True):
            task=st.text_area("Task description",placeholder="For example: Extract tables from a PDF and save them as CSV...",height=130,key="new_task_input")
            upload=st.file_uploader("Optional input file",key="new_task_upload",help="Attach a sample input file for context.")
            a,b,_=st.columns([1.3,1.1,4])
            with a: create=st.button("↑  Generate tool",type="primary",use_container_width=True)
            with b: clear=st.button("Clear",use_container_width=True)
            if clear:
                st.session_state.new_task_input=""; st.session_state.generated=False; st.session_state.generated_code=""; st.session_state.tests_run=False; st.rerun()
            if create:
                if not task.strip(): st.warning("Describe the task before generating a tool.")
                else:
                    st.session_state.current_task=task.strip(); st.session_state.generated_filename=slugify(task.strip()); st.session_state.generated_code=starter_code(task.strip()); st.session_state.generated=True; st.session_state.tests_run=False
                    add_activity("Received task",task.strip(),"spark"); add_activity("Generated starter",st.session_state.generated_filename,"code")
                    st.success("Starter template created. This prototype does not call an AI model or implement task-specific logic.")
            if upload is not None: st.caption(f"Attached: {upload.name} · {upload.size:,} bytes")
        if st.session_state.generated:
            st.markdown('<div class="section-title" style="margin-top:22px">Generated tool</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="panel"><div class="code-head"><div class="file-name">🐍 {html.escape(st.session_state.generated_filename)}</div><div class="status-pill">Starter template</div></div>',unsafe_allow_html=True)
            render_code(st.session_state.generated_code); st.markdown("</div>",unsafe_allow_html=True)
            a,b,c=st.columns([1,1.3,1.2])
            with a:
                if st.button("▷  Run checks",use_container_width=True):
                    st.session_state.test_results=checks(st.session_state.generated_code); st.session_state.tests_run=True
                    add_activity("Checks completed",f"{sum(st.session_state.test_results.values())}/{len(st.session_state.test_results)} structural checks passed","check"); st.rerun()
            with b:
                if st.button("▱  Save to Library",use_container_width=True):
                    name=st.session_state.generated_filename
                    if not any(t["name"]==name for t in st.session_state.saved_tools):
                        st.session_state.saved_tools.append({"name":name,"task":st.session_state.current_task,"code":st.session_state.generated_code,"saved_at":datetime.now().strftime("%d %b %Y, %H:%M")})
                    add_activity("Tool saved",f"{name} added to this session's library","folder"); st.success("Saved to this session's Tool Library.")
            with c:
                st.download_button("↓  Download .py",data=st.session_state.generated_code,file_name=st.session_state.generated_filename,mime="text/x-python",use_container_width=True)
            if st.session_state.tests_run:
                st.success("Structural checks passed. They do not prove the tool correctly performs your task.")
                for label,passed in st.session_state.test_results.items(): st.write(("✓ " if passed else "✕ ")+label)

    else:
        left,right=st.columns([1.65,1],gap="medium")
        with left:
            st.markdown('<div class="hero">Turn ideas into <span class="gradient">tools.</span></div><div class="subtitle">ToolSmith is an AI agent that creates, tests, and reuses its own tools to solve real tasks.</div>',unsafe_allow_html=True)
            st.markdown('<div class="panel" style="padding:12px 18px 14px">',unsafe_allow_html=True)
            task=st.text_area("Describe your task",placeholder="Describe what you want to do...",height=92,key="home_task_input",label_visibility="collapsed")
            fc,gc=st.columns([1,5])
            with fc: uploaded=st.file_uploader("Attach file",key="home_upload",label_visibility="collapsed")
            with gc: clicked=st.button("↑",type="primary",use_container_width=True,help="Generate a tool from your task")
            st.markdown("</div>",unsafe_allow_html=True)
            if clicked:
                if not task.strip(): st.warning("Enter a task first.")
                else:
                    st.session_state.current_task=task.strip(); st.session_state.generated_filename=slugify(task.strip()); st.session_state.generated_code=starter_code(task.strip()); st.session_state.generated=True; st.session_state.tests_run=False; st.session_state.page="New Task"
                    add_activity("Received task",task.strip(),"spark"); add_activity("Generated starter",st.session_state.generated_filename,"code"); st.rerun()
            if uploaded is not None: st.caption(f"Attached: {uploaded.name}")
        with right:
            st.markdown(f'<div class="stats-panel"><div class="small-muted">TOOL LIBRARY</div><div class="stats-title">A growing library<br>of capabilities.</div><div class="orb"></div><div class="stat-row"><div class="stat"><div class="stat-num">{24+len(st.session_state.saved_tools)}</div><div class="stat-label">Tools Created</div></div><div class="stat"><div class="stat-num">{18+sum(1 for x in st.session_state.activity if x["title"]=="Checks completed")}</div><div class="stat-label">Tests Passed</div></div><div class="stat"><div class="stat-num">92%</div><div class="stat-label">Success Rate</div></div></div></div>',unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>",unsafe_allow_html=True)
        ac,co,ru=st.columns([1.25,1.35,.85],gap="small")
        with ac:
            st.markdown('<div class="panel"><div class="section-title">Recent Activity</div>',unsafe_allow_html=True)
            for item in st.session_state.activity[:4]:
                symbols={"spark":"✦","code":"‹/›","check":"☑","folder":"▱"}; k=item.get("kind","spark")
                st.markdown(f'<div class="activity"><div class="activity-icon {k}">{symbols.get(k,"✦")}</div><div style="flex:1;min-width:0"><div class="activity-name">{html.escape(item["title"])}</div><div class="activity-desc">{html.escape(item["description"])}</div></div><div class="activity-time">{html.escape(item["time"])}</div></div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        sample=textwrap.dedent('''\
            import fitz  # PyMuPDF
            import pandas as pd

            def extract_tables(pdf_path: str) -> pd.DataFrame:
                # Extract tables from a PDF and return as DataFrame
                doc = fitz.open(pdf_path)
                tables = []
                for page in doc:
                    for table in page.find_tables():
                        df = pd.DataFrame(table.extract())
                        tables.append(df)
                return pd.concat(tables, ignore_index=True)
        ''')
        with co:
            st.markdown('<div class="panel"><div class="code-head"><div class="file-name">🐍 extract_pdf_tables.py</div><div class="status-pill">✓ Demo preview</div></div>',unsafe_allow_html=True)
            render_code(sample); st.markdown("</div>",unsafe_allow_html=True)
            x,y=st.columns([1,1])
            with x:
                if st.button("▷  Run Checks",key="home_test",use_container_width=True):
                    result=checks(starter_code("Extract tables from a PDF and save as CSV")); add_activity("Checks completed",f"{sum(result.values())}/{len(result)} structural checks passed","check"); st.success(f"{sum(result.values())}/{len(result)} structural checks passed.")
            with y:
                if st.button("▱  Save to Library",key="home_save",use_container_width=True):
                    name="extract_pdf_tables.py"
                    if not any(t["name"]==name for t in st.session_state.saved_tools):
                        st.session_state.saved_tools.append({"name":name,"task":"Extract tables from a PDF and save as CSV","code":sample,"saved_at":datetime.now().strftime("%d %b %Y, %H:%M")})
                    add_activity("Tool saved",f"{name} added to your session library","folder"); st.success("Sample added to Tool Library.")
        with ru:
            st.markdown('<div class="panel"><div class="run-title">Current Run</div><div class="run-flex"><div class="ring"><span>3/4</span></div><div class="step-list"><div><span class="step-dot done">✓</span>Planning</div><div><span class="step-dot done">✓</span>Generating tool</div><div><span class="step-dot active"></span>Running tests</div><div><span class="step-dot pending"></span>Saving to library</div></div></div></div>',unsafe_allow_html=True)

st.markdown("</div>",unsafe_allow_html=True)
`
