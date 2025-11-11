import streamlit as st
import requests
from components.layout import apply_layout
from components.translation import t
import os
# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | Chatbot", page_icon="💬", layout="wide")

# ============================================================
# GLOBAL LAYOUT (header, sidebar, theme, language)
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang
# ============================================================
# CONSTANTS
# ============================================================
API_BASE_URL = "http://127.0.0.1:8000"

# ============================================================
# STYLE
# ============================================================
st.markdown("""
<style>
.main-box {
    background: rgba(255,255,255,0.9);
    padding: 2rem;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(106,13,173,0.08);
    margin-top: 1.5rem;
}
.user-bubble, .bot-bubble {
    padding: 0.9rem 1.2rem;
    border-radius: 12px;
    margin-bottom: 0.8rem;
    max-width: 80%;
    word-wrap: break-word;
}
.user-bubble {
    background: #E6D8FF;
    color: #3A0068;
    align-self: flex-end;
}
.bot-bubble {
    background: #F3E5F5;
    color: #4A148C;
    border-left: 4px solid #7B1FA2;
    align-self: flex-start;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNCTIONS
# ============================================================
def backend_available():
    """Check if FastAPI backend is running."""
    try:
        # Prefer a lightweight health check endpoint if available
        r = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def send_to_model(message):
    """Send message to FastAPI backend (/chat) and handle structured responses."""
    try:
        db_path = st.session_state.get("user_database", "data/my_database.sqlite")
        payload = {"message": message, "database_path": db_path}
        res = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=45)


        if res.status_code == 200:
            try:
                payload = res.json()
            except Exception:
                return {"reply": t("chat_error_no_reply", lang)}

            # ✅ Return entire payload (includes reply, rows, sql, etc.)
            if isinstance(payload, dict):
                return payload
            else:
                return {"reply": str(payload)}

        else:
            return {"reply": f"{t('chat_error_server', lang)} ({res.status_code})"}

    except requests.exceptions.ConnectionError:
        return {"reply": t("chat_error_connection", lang)}
    except Exception as e:
        return {"reply": f"{t('chat_error_connection', lang)} ({e})"}



# ============================================================
# HEADER
# ============================================================
st.markdown(f'<div class="section-header"><h2>🤖 {t("chatbot_title", lang)}</h2></div>', unsafe_allow_html=True)
st.markdown(f'<p class="page-subtitle">{t("chatbot_subtitle", lang)}</p>', unsafe_allow_html=True)
active_db = st.session_state.get("user_database", "data/my_database.sqlite")
st.caption(f"**Active Database:** {os.path.basename(active_db)}")
# ============================================================
# AUTO-CHECK BACKEND
# ============================================================
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = backend_available()

if not st.session_state.backend_connected:
    st.error(t("backend_not_running", lang))
    render_footer()
    st.stop()

# ============================================================
# STEP 1 — SCHEMA CHOICE (INITIAL GREETING)
# ============================================================
if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if not st.session_state.chat_initialized:
    st.markdown(
        f"""
        <div class='bot-bubble'>
            👋 {t("chatbot_greeting", lang)}<br>
            {t("chatbot_schema_question", lang)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Upload / Default buttons — no hidden boxes now
    col1, col2 = st.columns(2)

    with col1:
        uploaded = st.file_uploader(
            t("upload_prompt", lang),
            type=["sqlite", "csv", "db"],
            label_visibility="collapsed",  # hides the text label
            key="schema_uploader"
        )
        if uploaded:
            # Save uploaded DB to temporary folder
            temp_path = os.path.join("data", uploaded.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded.getbuffer())

            # Save path to session state
            st.session_state.user_database = temp_path
            st.success(f"{uploaded.name} uploaded successfully and ready to use.")
            st.session_state.chat_initialized = True
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": t("chatbot_ready_after_upload", lang)
            })
            st.rerun()
        else:
            st.button(t("upload_schema_btn", lang), use_container_width=True, disabled=True)

    with col2:
        if st.button(t("use_default_btn", lang), use_container_width=True):
            st.session_state.chat_initialized = True
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": t("chatbot_default_reply", lang)
            })
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    render_footer()
    st.stop()


# ============================================================
# STEP 2 — NORMAL CHAT MODE
# ============================================================
st.markdown('<div class="main-box">', unsafe_allow_html=True)

for msg in st.session_state.chat_history:
    role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    align = "flex-end" if msg["role"] == "user" else "flex-start"
    st.markdown(
        f"""
        <div style='display:flex;justify-content:{align};'>
            <div class='{role_class}'>{msg["content"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

user_input = st.chat_input(t("chat_placeholder", lang))

if user_input:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Send to backend
    with st.spinner(t("chat_generating", lang)):
        reply = send_to_model(user_input)

    # Handle backend response
    if isinstance(reply, dict):
        reply_text = reply.get("reply", "")
        rows = reply.get("rows", [])
        sql_query = reply.get("sql", "")
        can_summarize = reply.get("can_summarize", False)

        # Store latest results for continuity
        if rows:
            st.session_state.last_rows = rows
        if sql_query:
            st.session_state.last_sql = sql_query

        # 🟣 Clean the LLM reply (remove robotic ending)
        if "Would you like me to summarize" in reply_text:
            reply_text = reply_text.split("Would you like")[0].strip()

        # 🟣 Display main AI answer
        st.session_state.chat_history.append({"role": "assistant", "content": reply_text})
        
    #  Show sample table preview before summarizing
    if rows:
        st.markdown("##### 📊 Sample Results Preview")
        try:
            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(df.head())  # show first few rows
        except Exception:
            st.json(rows)

    # Auto-summary (optional, feels more natural)
    if can_summarize and rows:
        with st.spinner("Summarizing results..."):
            res = requests.post(
                f"{API_BASE_URL}/chat/summary",
                json={
                    "question": user_input,
                    "sql": sql_query,
                    "rows": rows,
                },
            )
            if res.status_code == 200:
                summary = res.json().get("reply", "")
                if summary:
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": summary}
                    )

        st.rerun()  # Refresh UI to maintain conversation

st.markdown('</div>', unsafe_allow_html=True)
render_footer()
