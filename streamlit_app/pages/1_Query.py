import streamlit as st
import pandas as pd
import requests
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from components.translation import t
from components.layout import apply_layout
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

# ============================================================
#  GLOBAL LAYOUT (theme, header, sidebar, footer, language)
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # use global language selection
# ============================================================
# CONSTANTS
# ============================================================
API_BASE_URL = "http://127.0.0.1:8000"
HISTORY_FILE = "streamlit_app/history.csv"

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


def get_database_info():
    try:
        response = requests.get(f"{API_BASE_URL}/db-info", timeout=10)
        if response.status_code == 200:
            st.session_state.database_info = response.json()
            return st.session_state.database_info
        else:
            st.session_state.database_info = None
            return None
    except Exception:
        st.session_state.database_info = None
        return None


def log_question(question, sql_query, success, valid_sql=False, rows_returned=0,
                 error_message=None, confidence=None, confidence_label=None):
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


# Backend health
if not check_api_health():
    st.error(t("backend_not_running", lang))
    st.code("uvicorn main:app --reload")
    st.stop()

db_path = st.session_state.get("user_database", "data/my_database.sqlite")
is_user_db = "user_database" in st.session_state
st.markdown(
    f"<p style='color:gray;font-size:0.9rem;'>"
    f"<b>Active Database:</b> {os.path.basename(db_path)} "
    f"{'(User Uploaded)' if is_user_db else '(Demo Database)'}"
    f"</p>",
    unsafe_allow_html=True
)

# ============================================================
# SAMPLE QUERIES
# ============================================================
try:
    db_path = st.session_state.get("user_database", "data/my_database.sqlite")
    resp = requests.get(f"{API_BASE_URL}/sample-queries", params={"database_path": db_path})
    sample_queries = resp.json().get("sample_queries", [])
except Exception:
    sample_queries = ["Show all tables", "Count total records", "List first 5 rows"]

st.markdown(f'<div class="section-title">{t("quick_queries", lang)}</div>', unsafe_allow_html=True)
quick_cols = st.columns(2)
for i, q in enumerate(sample_queries[:4]):
    if quick_cols[i % 2].button(q, key=f"sample_{i}"):
        st.session_state.last_question = q
        st.session_state.generated_sql = ""
        st.session_state.last_result = None

# ============================================================
# MAIN INPUT
# ============================================================
st.markdown(f'<div class="section-title">{t("your_question", lang)}</div>', unsafe_allow_html=True)
user_question = st.text_area(
    label=t("placeholder", lang),
    value=st.session_state.get("last_question", ""),
    height=100,
    label_visibility="collapsed"
)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button(t("generate_sql", lang), type="primary", key="generate_sql_btn", width='stretch'):
        if not user_question.strip():
            st.warning(t("enter_question_first", lang))
        else:
            st.session_state.last_question = user_question
            with st.spinner(t("generating_sql", lang)):
                try:
                    db_path = st.session_state.get("user_database", "data/my_database.sqlite")
                    payload = {"question": user_question, "database_path": db_path}
                    res = requests.post(f"{API_BASE_URL}/test-query", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.generated_sql = data["sql"]
                        st.session_state.last_result = data
                        log_question(
                            question=user_question,
                            sql_query=data["sql"],
                            success=bool(data.get("execution_result")),
                            valid_sql=data["valid"],
                            rows_returned=len(data["execution_result"]) if data["execution_result"] else 0,
                            confidence=data.get("confidence"),
                            confidence_label=data.get("confidence_label"),
                        )
                        st.success(t("sql_generated_ok", lang))
                    else:
                        st.error(f"{t('api_error', lang)}: {res.text}")
                except Exception as e:
                    st.error(f"{t('request_failed', lang)}: {e}")

with col_btn2:
    if st.session_state.get("generated_sql") and st.button(t("clear_results", lang), key="clear_results_btn", width='stretch'):
        st.session_state.generated_sql = ""
        st.session_state.last_result = None
        st.rerun()

# ============================================================
# RESULTS DISPLAY
# ============================================================
if st.session_state.get("generated_sql") and st.session_state.get("last_result"):
    result = st.session_state.last_result

    st.markdown(f'<div class="section-title">{t("generated_sql", lang)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sql-display">{result["sql"]}</div>', unsafe_allow_html=True)

    # Confidence badge
    if result.get("confidence"):
        label = result["confidence_label"]
        color = {"High": "#4caf50", "Medium": "#ff9800", "Low": "#f44336"}.get(label, "#9e9e9e")
        st.markdown(
            f'<span class="status-badge" style="background-color:{color}20; color:{color};">'
            f'{t("confidence_label", lang).format(conf=result["confidence"], label=label)}'
            f'</span>',
            unsafe_allow_html=True
        )

    # ========================================================
    # FEEDBACK SECTION
    # ========================================================
    st.markdown(f'<div class="section-title">{t("feedback_tab", lang)}</div>', unsafe_allow_html=True)

    if "show_feedback_form" not in st.session_state:
        st.session_state.show_feedback_form = False

    fb_col1, fb_col2 = st.columns(2)
    with fb_col1:
        if st.button(t("looks_good", lang), key="btn_looks_good", width='stretch'):
            requests.post(f"{API_BASE_URL}/feedback", json={
                "question": user_question,
                "generated_sql": result["sql"],
                "verdict": "up",
                "comment": None,
                "user_correction": None
            })
            st.success(t("thanks_feedback", lang))
            st.session_state.show_feedback_form = False

    with fb_col2:
        if st.button(t("needs_improvement", lang), key="btn_needs_improvement", width='stretch'):
            st.session_state.show_feedback_form = not st.session_state.show_feedback_form

    if st.session_state.show_feedback_form:
        st.markdown('<div class="feedback-area">', unsafe_allow_html=True)
        comment = st.text_input(
            t("what_was_wrong", lang),
            key="fb_comment",
            placeholder=t("optional_explanation", lang)
        )
        correction = st.text_area(
            t("corrected_sql_optional", lang),
            key="fb_correction",
            height=100
        )
        if st.button(t("submit feedback", lang), type="primary", key="btn_submit_feedback", width='stretch'):
            requests.post(f"{API_BASE_URL}/feedback", json={
                "question": user_question,
                "generated_sql": result["sql"],
                "verdict": "down",
                "comment": comment or None,
                "user_correction": correction or None
            })
            st.success(t("feedback_saved_down", lang))
            st.session_state.show_feedback_form = False
        st.markdown('</div>', unsafe_allow_html=True)

    # ========================================================
    # METRICS SECTION
    # ========================================================
    st.markdown(f'<div class="section-title">{t("execution", lang)}</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{"✓" if result["valid"] else "✗"}</div>'
            f'<div class="metric-label">{t("valid_sql", lang)}</div></div>',
            unsafe_allow_html=True
        )
    with m2:
        executed = result["execution_result"] is not None
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{"✓" if executed else "✗"}</div>'
            f'<div class="metric-label">{t("execution", lang)}</div></div>',
            unsafe_allow_html=True
        )
    with m3:
        rows = len(result["execution_result"]) if result["execution_result"] else 0
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{rows}</div>'
            f'<div class="metric-label">{t("rows", lang)}</div></div>',
            unsafe_allow_html=True
        )

    if result.get("error"):
        st.error(f"{t('exec_error', lang)}: {result['error']}")

    # ========================================================
    # SUMMARY + RESULTS TABLE
    # ========================================================
    if result["execution_result"]:
        st.markdown(f'<div class="section-title">{t("results", lang)}</div>', unsafe_allow_html=True)

        if st.button(t("generate_summary", lang), key="btn_generate_summary", width='stretch'):
            with st.spinner(t("generating_sql", lang)):
                try:
                    db_path = st.session_state.get("user_database", "data/my_database.sqlite")
                    payload = {
                        "question": user_question,
                        "sql_query": result["sql"],
                        "results": result["execution_result"],
                        "database_path": db_path
                    }
                    res = requests.post(f"{API_BASE_URL}/quick-insights", json=payload)
                    if res.status_code == 200:
                        insights = res.json()["insights"]
                        st.markdown(
                            f'<div class="summary-box"><h4>{t("summary_box_title", lang)}</h4>'
                            + "".join(f"<p>• {insight}</p>" for insight in insights)
                            + '</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.warning(t("summary_warning", lang))
                except Exception as e:
                    st.error(f"{t('summary_failed', lang)}: {e}")

        df = pd.DataFrame(result["execution_result"])
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        AgGrid(df, gridOptions=gb.build(), height=min(400, 25 * len(df) + 150), theme="alpine")

        st.download_button(
            "📥 " + t("download_results_csv", lang),
            df.to_csv(index=False).encode("utf-8"),
            f"sqlwhisper_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

# ============================================================
# FOOTER
# ============================================================
render_footer()
