import html

import pandas as pd
import streamlit as st

import db
import tools
import ui
from agent import MissingAPIKeyError, SmartDeskAgent

st.set_page_config(page_title=ui.APP_NAME, page_icon="🧠", layout="wide")
ui.inject_css()
db.init_db()

# ---------- Session state ----------
st.session_state.setdefault("messages", [])
st.session_state.setdefault("tasks", [])
st.session_state.setdefault("agent", None)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("username", None)
st.session_state.setdefault("failed_logins", 0)
st.session_state.setdefault("msg_count", 0)

MAX_FAILED_LOGINS = 5
MAX_MESSAGES_PER_SESSION = 50
SUGGESTIONS = [
    "What's my total revenue?",
    "Which product sells best?",
    "Add a task: review the README",
]


# ---------- Auth ----------
def render_auth():
    ui.page_header(
        "SECURE ACCESS", "Welcome to", ui.APP_NAME,
        "Log in or create an account to continue.",
    )
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            if st.session_state.failed_logins >= MAX_FAILED_LOGINS:
                st.error("Too many failed attempts. Please try again later.")
            else:
                uid = db.authenticate(u, p)
                if uid:
                    st.session_state.user_id = uid
                    st.session_state.username = u.strip().lower()
                    st.session_state.tasks = db.list_tasks(uid)
                    st.session_state.agent = None
                    st.session_state.failed_logins = 0
                    st.rerun()
                else:
                    st.session_state.failed_logins += 1
                    st.error("Invalid username or password.")

    with tab_signup:
        with st.form("signup_form"):
            new_u = st.text_input("Choose a username")
            new_p = st.text_input("Choose a password (min 8 characters)", type="password")
            created = st.form_submit_button("Create account")
        if created:
            ok, msg = db.register_user(new_u, new_p)
            (st.success if ok else st.error)(msg)


if st.session_state.user_id is None:
    render_auth()
    st.stop()

# ---------- Sidebar (logged-in users only) ----------
ui.sidebar_logo()
st.sidebar.caption(f"Signed in as **{st.session_state.username}**")
if st.sidebar.button("Log out"):
    st.session_state.clear()
    st.rerun()

page = st.sidebar.radio("Navigate", ["AI Chat", "Sales Analyzer"], label_visibility="collapsed")
st.sidebar.caption("AI provider: Google Gemini")

st.sidebar.subheader("My Tasks")
if st.session_state.tasks:
    for t in st.session_state.tasks:
        ui.task_card(t["description"])
else:
    st.sidebar.caption("No tasks yet.")

if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    st.session_state.agent = None
    st.rerun()


# ---------- Pages ----------
def render_chat():
    ui.page_header(
        "BUILT WITH PYTHON • GEMINI • PANDAS",
        "Your productivity desk, staffed by",
        "AI.",
        "Chat with an assistant that calls real Python tools for sales analysis "
        "and task management, so numbers come from code, never from guesses.",
    )
    ui.chips(["Gemini function calling", "Pandas-powered analytics", "Safe tool whitelist"])

    if st.session_state.agent is None:
        try:
            st.session_state.agent = SmartDeskAgent(
                st.session_state.tasks, user_id=st.session_state.user_id
            )
        except MissingAPIKeyError as e:
            st.error(str(e))
            return

    ui.status_pill(f"AI Active • 2 tools • {len(st.session_state.messages)} messages")

    if not st.session_state.messages:
        cols = st.columns(len(SUGGESTIONS))
        for i, (col, text) in enumerate(zip(cols, SUGGESTIONS)):
            if col.button(text, key=f"sugg_{i}"):
                st.session_state.pending_prompt = text
                st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            for t in m.get("tools_used", []):
                with st.expander(f"🔧 Tool used: {t['name']}"):
                    st.json(t["result"])

    typed = st.chat_input("Ask about sales, add a task, or just chat...")
    prompt = typed or st.session_state.pop("pending_prompt", None)
    if prompt:
        if st.session_state.msg_count >= MAX_MESSAGES_PER_SESSION:
            st.warning("Message limit reached for this session. Log out and back in to continue.")
        else:
            st.session_state.msg_count += 1
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    out = st.session_state.agent.chat(prompt)
            st.session_state.messages.append(
                {"role": "assistant", "content": out["reply"], "tools_used": out["tools_used"]}
            )
            st.rerun()  # refresh so the sidebar task list updates


def render_sales():
    ui.page_header(
        "PANDAS + NUMPY • NO INVENTED NUMBERS",
        "Sales",
        "Analyzer",
        "Every figure below is calculated in Python from your CSV.",
    )
    uploaded = st.file_uploader("Upload a CSV (date, product, quantity, sales)", type="csv")
    try:
        df = tools.load_sales(uploaded) if uploaded else tools.load_sales()
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return

    s = tools.compute_sales_stats(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"{s['total_sales']:,.2f}")
    c2.metric("Average Sales", f"{s['average_sales']:,.2f}")
    c3.metric("Total Records", s["total_records"])
    c4.metric("Best Seller (revenue)", s["top_product_by_revenue"])

    st.subheader("Sales by product")
    st.bar_chart(pd.Series(s["sales_by_product"]), color="#6D5EF5")

    st.subheader("Insights")
    top_rev = html.escape(s["top_product_by_revenue"])
    top_qty = html.escape(s["top_product_by_quantity"])
    ui.insight(f"<b>{top_rev}</b> leads in revenue ({s['top_product_revenue']:,.2f}).")
    ui.insight(f"<b>{top_qty}</b> sells the most units.")
    ui.insight(f"Median sale is {s['median_sales']:,.2f} vs average {s['average_sales']:,.2f}.")

if page == "AI Chat":
    render_chat()
else:
    render_sales()