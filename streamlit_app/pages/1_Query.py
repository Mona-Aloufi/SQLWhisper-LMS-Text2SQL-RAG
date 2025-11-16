import streamlit as st
import pandas as pd
import requests
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from components.translation import t
from components.layout import apply_layout
from components.footer import render_footer

# ============================================================
#  GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
# CONSTANTS
# ============================================================
API_BASE_URL = "http://127.0.0.1:8000"
HISTORY_FILE = "streamlit_app/history.csv"

# ============================================================
# SAFE SESSION DEFAULTS
# ============================================================
defaults = {
    "db_path": None,
    "file_id": None,
    "db_credentials": None,
    "db_type": None,
    "db_connected": False,
    "api_health": False,
    "auto_execute": False,
    "last_question": "",
    "generated_sql": "",
    "last_result": None,
    "show_feedback_form": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ============================================================
# HELPERS
# ============================================================
def check_api_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        st.session_state.api_health = response.status_code == 200
        return st.session_state.api_health
    except:
        st.session_state.api_health = False
        return False


def log_question(question, sql_query, success, valid_sql=False,
                 rows_returned=0, error_message=None,
                 confidence=None, confidence_label=None):

    expected_cols = [
        "timestamp", "question", "sql_query", "success", "valid_sql",
        "rows_returned", "error_message", "confidence", "confidence_label"
    ]

    row = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "question": question,
        "sql_query": sql_query,
        "success": success,
        "valid_sql": valid_sql,
        "rows_returned": rows_returned,
        "error_message": error_message or "",
        "confidence": confidence,
        "confidence_label": confidence_label,
    }

    df = pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame(columns=expected_cols)

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

# ============================================================
# MAIN CONTENT
# ============================================================
st.markdown(f'<div class="section-title">{t("query_tab", lang)}</div>', unsafe_allow_html=True)

# Backend check
if not check_api_health():
    st.error(t("backend_not_running", lang))
    st.code("uvicorn app:app --reload")
    st.stop()

# Ensure DB connected
if not st.session_state.db_connected or not st.session_state.file_id:
    st.warning("No database connected. Please upload or connect first.")
    st.stop()

file_id = st.session_state.file_id
db_type = st.session_state.db_type

# DB label
if db_type == "sqlite":
    db_label = os.path.basename(st.session_state.db_path or "Unknown SQLite DB")
else:
    creds = st.session_state.db_credentials or {}
    db_label = f"{creds.get('user','?')}@{creds.get('host','?')}/{creds.get('database','?')}"

st.markdown(
    f"<p style='color:gray;font-size:0.9rem;'><b>Active Database:</b> {db_label}</p>",
    unsafe_allow_html=True
)

# ============================================================
# SAMPLE QUERIES
# ============================================================
try:
    resp = requests.get(f"{API_BASE_URL}/sample-queries")
    sample_queries = resp.json().get("sample_queries", [])
except:
    sample_queries = ["Show all tables", "Count total records", "List first 5 rows"]

st.markdown(f'<div class="section-title">{t("quick_queries", lang)}</div>', unsafe_allow_html=True)

quick_cols = st.columns(2)
for i, q in enumerate(sample_queries[:4]):
    if quick_cols[i % 2].button(q, key=f"sample_{i}"):
        st.session_state.last_question = q
        st.session_state.generated_sql = ""
        st.session_state.last_result = None
        st.session_state.show_feedback_form = False

# ============================================================
# MAIN INPUT
# ============================================================
st.markdown(f'<div class="section-title">{t("your_question", lang)}</div>', unsafe_allow_html=True)

user_question = st.text_area(
    label=t("placeholder", lang),
    value=st.session_state.last_question,
    height=100,
    label_visibility="collapsed"
)

col_btn1, col_btn2 = st.columns(2)

# ============================================================
# GENERATE SQL
# ============================================================
with col_btn1:
    if st.button(t("generate_sql", lang), type="primary", use_container_width=True):

        if not user_question.strip():
            st.warning(t("enter_question_first", lang))
        else:
            st.session_state.last_question = user_question

            with st.spinner(t("generating_sql", lang)):
                try:
                    payload = {"question": user_question, "file_id": file_id}
                    res = requests.post(f"{API_BASE_URL}/text2sql", json=payload)

                    if res.status_code == 200:
                        data = res.json()

                        st.session_state.generated_sql = data["sql"]
                        st.session_state.last_result = data
                        st.session_state.show_feedback_form = False

                        log_question(
                            question=user_question,
                            sql_query=data["sql"],
                            success=data["valid"],
                            valid_sql=data["valid"],
                            confidence=data.get("confidence"),
                            confidence_label=data.get("confidence_label")
                        )

                        st.success(t("sql_generated_ok", lang))

                    else:
                        st.error(f"{t('api_error', lang)}: {res.text}")

                except Exception as e:
                    st.error(f"{t('request_failed', lang)}: {e}")

# ============================================================
# CLEAR BUTTON
# ============================================================
with col_btn2:
    if st.button(t("clear_results", lang), use_container_width=True):
        st.session_state.last_question = ""
        st.session_state.generated_sql = ""
        st.session_state.last_result = None
        st.session_state.show_feedback_form = False
        st.rerun()

# ============================================================
# RESULTS DISPLAY
# ============================================================
if st.session_state.generated_sql and st.session_state.last_result:

    result = st.session_state.last_result

    # SQL output
    st.markdown(f'<div class="section-title">{t("generated_sql", lang)}</div>', unsafe_allow_html=True)
    st.code(result["sql"], language="sql")

    # Confidence badge
    if result.get("confidence") is not None:
        label = result.get("confidence_label")
        color = {"High": "#4caf50", "Medium": "#ff9800", "Low": "#f44336"}.get(label, "#9e9e9e")
        st.markdown(
            f'<span style="background-color:{color}20; color:{color}; padding:6px 12px;'
            f'border-radius:8px; font-weight:600;">'
            f'Confidence: {result["confidence"]:.2f} ({label})</span>',
            unsafe_allow_html=True
        )

    # ============================================================
    # EXECUTE SQL
    # ============================================================
    with st.spinner(t("executing", lang)):
        try:
            exec_res = requests.post(
                f"{API_BASE_URL}/execute-sql",
                json={"sql": result["sql"], "file_id": file_id}
            )
            exec_json = exec_res.json()

            if exec_json.get("error"):
                st.error(f"Execution Error: {exec_json['error']}")
                rows, columns = [], []
            else:
                rows = exec_json.get("rows", [])
                columns = exec_json.get("columns", [])
                st.success("Query executed successfully")

        except Exception as e:
            st.error(f"Execution Error: {e}")
            rows, columns = [], []

    # Update history once rows are known
    log_question(
        question=user_question,
        sql_query=result["sql"],
        success=True,
        valid_sql=result["valid"],
        rows_returned=len(rows),
        confidence=result.get("confidence"),
        confidence_label=result.get("confidence_label")
    )

    # ============================================================
    # METRICS
    # ============================================================
    st.markdown(f'<div class="section-title">{t("execution", lang)}</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric(t("valid_sql", lang), "✓" if result["valid"] else "✗")
    m2.metric(t("execution", lang), "✓" if rows else "✗")
    m3.metric(t("rows", lang), len(rows))

    # ============================================================
    # SUMMARY + INSIGHTS
    # ============================================================
    if rows:
        st.markdown(f'<div class="section-title">{t("results", lang)}</div>', unsafe_allow_html=True)

        # ---------- FULL NATURAL SUMMARY ----------
        if st.button(t("generate_summary", lang), key="btn_generate_summary", use_container_width=True):
            with st.spinner("Generating natural-language summary..."):
                try:
                    summary_payload = {
                        "question": user_question,
                        "sql_query": result["sql"],
                        "results": rows
                    }
                    s_res = requests.post(f"{API_BASE_URL}/generate-summary", json=summary_payload)

                    if s_res.status_code == 200:
                        summary = s_res.json().get("summary", "")
                        st.markdown(
                            f'<div class="summary-box"><h4>{t("summary_box_title", lang)}</h4>'
                            f'<p>{summary}</p></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.warning("Could not generate summary.")

                except Exception as e:
                    st.error(f"Summary Error: {e}")

        # ---------- QUICK INSIGHTS ----------
        if st.button("📌 Quick Insights", key="btn_insights", use_container_width=True):
            with st.spinner("Generating insights..."):
                try:
                    qi = requests.post(
                        f"{API_BASE_URL}/quick-insights",
                        json={"results": rows, "question": user_question}
                    ).json()

                    insights = qi.get("insights", [])
                    st.markdown(
                        '<div class="summary-box"><h4>Insights</h4>' +
                        "".join(f"<p>• {i}</p>" for i in insights) +
                        "</div>",
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Insights Error: {e}")

        # ---------- TABLE ----------
        df = pd.DataFrame(rows, columns=columns)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        AgGrid(df, gridOptions=gb.build(), height=min(400, 25 * len(df) + 150), theme="alpine")

        # ---------- DOWNLOAD ----------
        st.download_button(
            "📥 " + t("download_results_csv", lang),
            df.to_csv(index=False).encode("utf-8"),
            f"sqlwhisper_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

    # ============================================================
    # FEEDBACK — MOVED TO BOTTOM
    # ============================================================
    st.markdown(f'<div class="section-title">{t("feedback_tab", lang)}</div>', unsafe_allow_html=True)

    fb1, fb2 = st.columns(2)
    with fb1:
        if st.button(t("looks_good", lang), key="good_btn", use_container_width=True):
            requests.post(f"{API_BASE_URL}/feedback", json={
                "question": user_question,
                "generated_sql": result["sql"],
                "verdict": "up",
                "comment": None,
                "user_correction": None
            })
            st.success(t("thanks_feedback", lang))
            st.session_state.show_feedback_form = False

    with fb2:
        if st.button(t("needs_improvement", lang), key="bad_btn", use_container_width=True):
            st.session_state.show_feedback_form = not st.session_state.show_feedback_form

    # Feedback form
    if st.session_state.show_feedback_form:
        st.markdown('<div class="feedback-area">', unsafe_allow_html=True)

        fb_comment = st.text_input(
            t("what_was_wrong", lang),
            key="fb_comment",
            placeholder=t("optional_explanation", lang)
        )

        fb_correction = st.text_area(
            t("corrected_sql_optional", lang),
            key="fb_correction",
            height=100
        )

        if st.button(t("submit feedback", lang), type="primary", use_container_width=True):
            requests.post(f"{API_BASE_URL}/feedback", json={
                "question": user_question,
                "generated_sql": result["sql"],
                "verdict": "down",
                "comment": fb_comment or None,
                "user_correction": fb_correction or None
            })
            st.success(t("feedback_saved_down", lang))
            st.session_state.show_feedback_form = False

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
render_footer()
