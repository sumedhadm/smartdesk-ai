import html

import streamlit as st

APP_NAME = "SmartDesk AI"  # rename here in one place

CSS = """
<style>
:root {
  --bg:#0B1020; --card:#121933; --line:rgba(255,255,255,.08);
  --accent:#6D5EF5; --text:#E6E9F5; --muted:#9AA3C7; --green:#22C55E;
}
.stApp {
  background:
    radial-gradient(900px 480px at 85% -10%, rgba(109,94,245,.28), transparent 60%),
    radial-gradient(700px 400px at -5% 10%, rgba(34,197,94,.08), transparent 55%),
    var(--bg);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1100px; }
[data-testid="stSidebar"] { background:#0E1428; border-right:1px solid var(--line); }

.badge {
  display:inline-flex; align-items:center; gap:8px; padding:6px 14px;
  border:1px solid rgba(109,94,245,.45); background:rgba(109,94,245,.12);
  border-radius:999px; font-family:ui-monospace,Consolas,monospace;
  font-size:.72rem; letter-spacing:.06em; color:#C4B8FF;
}
.dot { width:8px; height:8px; border-radius:50%; background:var(--accent); display:inline-block; }
.dot.live { background:var(--green); box-shadow:0 0 8px var(--green); }
.hero-title {
  font-size:clamp(2rem,4.5vw,3.3rem); line-height:1.1; font-weight:800;
  margin:.9rem 0 .6rem; color:#fff;
}
.grad {
  background:linear-gradient(90deg,#8B7BFF,#C4B5FD);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.hero-sub { color:var(--muted); font-size:1.05rem; max-width:650px; line-height:1.6; }
.chips { display:flex; flex-wrap:wrap; gap:8px 20px; margin:1rem 0 1.2rem; color:var(--muted); font-size:.9rem; }
.chips b { color:var(--green); margin-right:6px; }
.status {
  display:inline-flex; align-items:center; gap:8px; color:var(--muted); font-size:.85rem;
  padding:8px 14px; background:var(--card); border:1px solid var(--line);
  border-radius:999px; margin-bottom:1rem;
}
.logo { display:flex; align-items:center; gap:10px; font-weight:700; font-size:1.15rem; margin-bottom:1rem; }
.logo i {
  display:grid; place-items:center; width:36px; height:36px; border-radius:10px;
  background:linear-gradient(135deg,#6D5EF5,#22D3EE); font-style:normal;
}
.task {
  padding:8px 12px; margin-bottom:8px; background:var(--card);
  border:1px solid var(--line); border-radius:10px; font-size:.9rem;
}
.insight {
  background:var(--card); border:1px solid var(--line); border-left:3px solid var(--accent);
  border-radius:12px; padding:12px 16px; margin-bottom:10px;
}

[data-testid="stMetric"] {
  background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px 18px;
}
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stChatMessage"] {
  background:var(--card); border:1px solid var(--line); border-radius:16px; padding:12px 16px;
}
[data-testid="stChatMessage"]:has([data-testid*="-user"], [data-testid*="AvatarUser"]) {
  background:linear-gradient(135deg, rgba(109,94,245,.35), rgba(109,94,245,.18));
  border-color:rgba(109,94,245,.5);
}
.stButton > button {
  width:100%; border-radius:12px; border:1px solid rgba(109,94,245,.5);
  background:rgba(109,94,245,.12); color:var(--text); transition:.15s;
}
.stButton > button:hover {
  background:var(--accent); border-color:var(--accent); color:#fff; transform:translateY(-1px);
}
[data-testid="stFileUploader"] section {
  background:var(--card); border:1px dashed rgba(109,94,245,.5); border-radius:14px;
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_logo():
    st.sidebar.markdown(
        f'<div class="logo"><i>🧠</i>{html.escape(APP_NAME)}</div>',
        unsafe_allow_html=True,
    )


def page_header(badge: str, title: str, highlight: str, subtitle: str = ""):
    # No indentation or blank lines inside this HTML, or Markdown breaks it
    st.markdown(
        f"""<div class="badge"><span class="dot live"></span>{html.escape(badge)}</div>
<h1 class="hero-title">{html.escape(title)} <span class="grad">{html.escape(highlight)}</span></h1>
<p class="hero-sub">{html.escape(subtitle)}</p>""",
        unsafe_allow_html=True,
    )


def chips(items: list[str]):
    inner = "".join(f"<span><b>✓</b>{html.escape(i)}</span>" for i in items)
    st.markdown(f'<div class="chips">{inner}</div>', unsafe_allow_html=True)


def status_pill(text: str):
    st.markdown(
        f'<div class="status"><span class="dot live"></span>{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def task_card(description: str):
    st.sidebar.markdown(
        f'<div class="task">• {html.escape(description)}</div>', unsafe_allow_html=True
    )


def insight(safe_html: str):
    """Caller must html.escape any dynamic values before passing them in."""
    st.markdown(f'<div class="insight">{safe_html}</div>', unsafe_allow_html=True)