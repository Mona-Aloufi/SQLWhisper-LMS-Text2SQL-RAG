import streamlit as st
import os
from components.translation import t
from components.layout import apply_layout

# ============================================================
#  PAGE CONFIG
# ============================================================
st.set_page_config(page_title="SQLWhisper - Home", layout="wide")

# ============================================================
#  GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # language from session

# ============================================================
#  PAGE STYLE
# ============================================================
st.markdown("""
<style>
.main-container {
    padding: 2.5rem 3rem;
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 18px;
    box-shadow: 0 6px 20px rgba(106, 13, 173, 0.08);
    margin-top: 2rem;
}
.welcome-box {
    background: #fde7f3;
    border-left: 5px solid #d63384;
    border-radius: 12px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 10px rgba(214, 51, 132, 0.1);
}
.welcome-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #d63384;
    margin-bottom: 0.8rem;
    line-height: 1.2;
}
.welcome-sub {
    font-size: 1.1rem;
    color: #6a1b9a;
    margin-bottom: 0;
}
.feature-box {
    padding: 0.8rem 1.2rem;
    border-radius: 12px;
    background: #f3e5f5;
    color: #4A148C;
    font-weight: 600;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 8px rgba(106, 13, 173, 0.05);
    font-size: 0.9rem;
}
.feature-box strong { color: #6A1B9A; }
section.main > div:first-child { background: transparent !important; box-shadow: none !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  MAIN CONTENT
# ============================================================
st.markdown(f"""
<div class="welcome-box" style="margin-top:0;">
    <div class="welcome-title">{t("welcome_title", lang)}</div>
    <div class="welcome-sub">{t("welcome_sub", lang)}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="feature-box">{t("feature_secure", lang)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="feature-box">{t("feature_ai", lang)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="feature-box">{t("feature_insights", lang)}</div>', unsafe_allow_html=True)

# ============================================================
#  BUTTONS (Upload / Default)
# ============================================================
col1, col2 = st.columns([1, 1])

# ---------- Upload Database ----------
with col1:
    st.subheader(t("upload_schema_btn", lang))
    uploaded_file = st.file_uploader(" ", type=["sqlite", "db", "csv"], key="uploader_home")
    if uploaded_file:
        # Save uploaded file
        os.makedirs("data", exist_ok=True)
        upload_path = os.path.join("data", uploaded_file.name)
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Store in session
        st.session_state["user_database"] = upload_path

        st.success(t("upload_success", lang).format(file=uploaded_file.name))
        st.info(t("upload_info", lang))

        # ✅ Go to Data Dashboard
        st.switch_page("pages/4_Data_Dashboard.py")

# ---------- Default Database ----------
with col2:
    if st.button(t("default_schema_btn", lang), key="default_btn", use_container_width=True):
        # Set demo DB
        st.session_state["user_database"] = "data/my_database.sqlite"
        st.success(t("default_info", lang))

        # ✅ Go to Data Dashboard
        st.switch_page("pages/4_Data_Dashboard.py")

# ============================================================
#  FOOTER
# ============================================================
render_footer()

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import sqlite3
# from pathlib import Path
# import numpy as np
# import requests
# import os
# from st_aggrid import AgGrid, GridOptionsBuilder
# from PIL import Image
# from components.translation import t  # Translation helper
# from components.header import render_header
# from components.sidebar import render_sidebar
# from components.footer import render_footer

# # ============================================================
# #  PATHS & CONSTANTS
# # ============================================================
# logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
# HISTORY_FILE = "streamlit_app/history.csv"
# API_BASE_URL = "http://127.0.0.1:8000"
# theme_path = os.path.join(os.path.dirname(__file__), "style", "theme.css")

# # ============================================================
# #  PAGE CONFIGURATION
# # ============================================================
# st.set_page_config(page_title="SQLWhisper", page_icon=logo_path, layout="wide")

# # ============================================================
# #  LOAD CUSTOM THEME
# # ============================================================
# if os.path.exists(theme_path):
#     with open(theme_path) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# else:
#     st.warning("theme.css not found in streamlit_app/style/")

# # ============================================================
# #  LANGUAGE SELECTION
# # ============================================================
# if "lang" not in st.session_state:
#     st.session_state.lang = "en"

# lang = st.sidebar.selectbox(" Language / اللغة", ["en", "ar"], index=0, key="lang_select")
# st.session_state.lang = lang

# # RTL adjustment for Arabic
# if st.session_state.lang == "ar":
#     st.markdown("<style>html{direction:rtl;text-align:right;}</style>", unsafe_allow_html=True)
# else:
#     st.markdown("<style>html{direction:ltr;text-align:left;}</style>", unsafe_allow_html=True)

# # ============================================================
# #  HEADER (LOGO + TITLE)
# # ============================================================
# render_header(st.session_state.lang)
# # header_col1, header_col2 = st.columns([0.2, 0.8])
# # with header_col1:
# #     try:
# #         logo = Image.open(logo_path)
# #         st.image(logo, width=80)
# #     except:
# #         st.write("LOGO")
# # with header_col2:
# #     st.markdown(f'<h1 class="app-title">{t("app_title", lang)}</h1>', unsafe_allow_html=True)
# #     st.markdown(f'<p class="app-subtitle">{t("app_subtitle", lang)}</p>', unsafe_allow_html=True)

# # ============================================================
# #  SESSION STATE
# # ============================================================
# for key, value in {
#     "generated_sql": "",
#     "last_question": "",
#     "last_result": None,
#     "database_info": None,
#     "api_health": None
# }.items():
#     if key not in st.session_state:
#         st.session_state[key] = value

# # ============================================================
# # HELPERS
# # ============================================================
# def check_api_health():
#     try:
#         response = requests.get(f"{API_BASE_URL}/health", timeout=5)
#         st.session_state.api_health = response.status_code == 200
#         return st.session_state.api_health
#     except:
#         st.session_state.api_health = False
#         return False


# def get_database_info():
#     try:
#         response = requests.get(f"{API_BASE_URL}/db-info", timeout=10)
#         if response.status_code == 200:
#             st.session_state.database_info = response.json()
#             return st.session_state.database_info
#         else:
#             st.session_state.database_info = None
#             return None
#     except Exception:
#         st.session_state.database_info = None
#         return None


# def log_question(question, sql_query, success, valid_sql=False, rows_returned=0,
#                  error_message=None, confidence=None, confidence_label=None):
#     expected_cols = [
#         "timestamp", "question", "sql_query", "success", "valid_sql",
#         "rows_returned", "error_message", "confidence", "confidence_label"
#     ]
#     row = {
#         "timestamp": pd.Timestamp.now().isoformat(),
#         "question": question,
#         "sql_query": sql_query,
#         "success": success,
#         "valid_sql": valid_sql,
#         "rows_returned": rows_returned,
#         "error_message": error_message or "",
#         "confidence": confidence,
#         "confidence_label": confidence_label,
#     }

#     df = pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame(columns=expected_cols)
#     for col in expected_cols:
#         if col not in df.columns:
#             df[col] = None
#     df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
#     df.to_csv(HISTORY_FILE, index=False)

# # ============================================================
# #  SIDEBAR
# # ============================================================
# render_sidebar(st.session_state.lang, get_database_info)
# # st.sidebar.markdown(f'<div class="sidebar-header"><h3>{t("database_info", lang)}</h3></div>', unsafe_allow_html=True)

# # if st.sidebar.button(t("load_schema", lang), width='stretch'):
# #     with st.spinner(t("loading_schema", lang)):
# #         db_info = get_database_info()
# #         if db_info:
# #             st.success(t("db_connected", lang))
# #             st.caption(f"**Tables:** {', '.join(db_info['tables'])}")
# #         else:
# #             st.error(t("db_failed", lang))

# # ============================================================
# # MAIN TABS
# # ============================================================
# tabs = st.tabs([
#     t("query_tab", lang),
#     t("history_tab", lang),
#     t("feedback_tab", lang),
#     t("dashboard_tab", lang),
#     t("about_tab", lang)
# ])

# # ============================================================
# # TAB 1: QUERY
# # ============================================================
# with tabs[0]:
#     if not check_api_health():
#         st.error(t("backend_not_running", lang))
#         st.code("uvicorn main:app --reload")
#         st.stop()

#     # Sample queries
#     try:
#         sample_queries = requests.get(f"{API_BASE_URL}/sample-queries").json()["sample_queries"]
#     except:
#         sample_queries = ["Show all tables", "Count total records", "List first 5 rows", "Describe table schema"]

#     st.markdown(f'<div class="section-title">{t("quick_queries", lang)}</div>', unsafe_allow_html=True)
#     quick_cols = st.columns(2)
#     for i, q in enumerate(sample_queries[:4]):
#         if quick_cols[i % 2].button(q, key=f"sample_{i}", width='stretch'):
#             st.session_state.last_question = q
#             st.session_state.generated_sql = ""
#             st.session_state.last_result = None

#     st.markdown(f'<div class="section-title">{t("your_question", lang)}</div>', unsafe_allow_html=True)
#     user_question = st.text_area(
#         label=t("placeholder", lang),
#         value=st.session_state.last_question,
#         height=100,
#         label_visibility="collapsed"
#     )

#     col_btn1, col_btn2 = st.columns(2)
#     with col_btn1:
#         if st.button(t("generate_sql", lang), type="primary", width='stretch'):
#             if not user_question.strip():
#                 st.warning(t("enter_question_first", lang))
#             else:
#                 st.session_state.last_question = user_question
#                 with st.spinner(t("generating_sql", lang)):
#                     try:
#                         res = requests.post(f"{API_BASE_URL}/test-query", json={"question": user_question})
#                         if res.status_code == 200:
#                             data = res.json()
#                             st.session_state.generated_sql = data["sql"]
#                             st.session_state.last_result = data
#                             log_question(
#                                 question=user_question,
#                                 sql_query=data["sql"],
#                                 success=bool(data.get("execution_result")),
#                                 valid_sql=data["valid"],
#                                 rows_returned=len(data["execution_result"]) if data["execution_result"] else 0,
#                                 confidence=data.get("confidence"),
#                                 confidence_label=data.get("confidence_label"),
#                             )
#                             st.success(t("sql_generated_ok", lang))
#                         else:
#                             st.error(f"{t('api_error', lang)}: {res.text}")
#                     except Exception as e:
#                         st.error(f"{t('request_failed', lang)}: {e}")

#     with col_btn2:
#         if st.session_state.generated_sql and st.button(t("clear_results", lang), width='stretch'):
#             st.session_state.generated_sql = ""
#             st.session_state.last_result = None
#             st.rerun()

#     # RESULTS DISPLAY
#     if st.session_state.generated_sql and st.session_state.last_result:
#         result = st.session_state.last_result

#         st.markdown(f'<div class="section-title">{t("generated_sql", lang)}</div>', unsafe_allow_html=True)
#         st.markdown(f'<div class="sql-display">{result["sql"]}</div>', unsafe_allow_html=True)

#         # Confidence badge
#         if result.get("confidence"):
#             label = result["confidence_label"]
#             color = {"High": "#4caf50", "Medium": "#ff9800", "Low": "#f44336"}.get(label, "#9e9e9e")
#             st.markdown(
#                 f'<span class="status-badge" style="background-color:{color}20; color:{color};">'
#                 f'{t("confidence_label", lang).format(conf=result["confidence"], label=label)}'
#                 f'</span>',
#                 unsafe_allow_html=True
#             )

#         # Feedback section
#         st.markdown(f'<div class="section-title">{t("feedback_tab", lang)}</div>', unsafe_allow_html=True)

#         # Session state to track when to show correction boxes
#         if "show_feedback_form" not in st.session_state:
#             st.session_state.show_feedback_form = False

#         fb_col1, fb_col2 = st.columns(2)

#         with fb_col1:
#             if st.button(t("looks_good", lang), use_container_width=True):
#                 requests.post(f"{API_BASE_URL}/feedback", json={
#                     "question": user_question,
#                     "generated_sql": result["sql"],
#                     "verdict": "up",
#                     "comment": None,
#                     "user_correction": None
#                 })
#                 st.success(t("thanks_feedback", lang))
#                 st.session_state.show_feedback_form = False  # hide form if it was open

#         with fb_col2:
#             # When user clicks "Needs Improvement", toggle the form
#             if st.button(t("needs_improvement", lang), use_container_width=True):
#                 st.session_state.show_feedback_form = not st.session_state.show_feedback_form

#         # Show text inputs only if "Needs Improvement" was clicked
#         if st.session_state.show_feedback_form:
#             st.markdown('<div class="feedback-area">', unsafe_allow_html=True)
#             comment = st.text_input(
#                 t("what_was_wrong", lang),
#                 key="fb_comment",
#                 placeholder=t("optional_explanation", lang)
#             )
#             correction = st.text_area(
#                 t("corrected_sql_optional", lang),
#                 key="fb_correction",
#                 height=100
#             )
#             if st.button(t("submit feedback", lang), type="primary", use_container_width=True):
#                 requests.post(f"{API_BASE_URL}/feedback", json={
#                     "question": user_question,
#                     "generated_sql": result["sql"],
#                     "verdict": "down",
#                     "comment": comment or None,
#                     "user_correction": correction or None
#                 })
#                 st.success(t("feedback_saved_down", lang))
#                 st.session_state.show_feedback_form = False
#             st.markdown('</div>', unsafe_allow_html=True)


#         # Metrics row
#         st.markdown(f'<div class="section-title">{t("execution", lang)}</div>', unsafe_allow_html=True)
#         m1, m2, m3 = st.columns(3)
#         with m1:
#             valid = result["valid"]
#             st.markdown(f'<div class="metric-card"><div class="metric-value">{"✓" if valid else "✗"}</div><div class="metric-label">{t("valid_sql", lang)}</div></div>', unsafe_allow_html=True)
#         with m2:
#             executed = result["execution_result"] is not None
#             st.markdown(f'<div class="metric-card"><div class="metric-value">{"✓" if executed else "✗"}</div><div class="metric-label">{t("execution", lang)}</div></div>', unsafe_allow_html=True)
#         with m3:
#             rows = len(result["execution_result"]) if result["execution_result"] else 0
#             st.markdown(f'<div class="metric-card"><div class="metric-value">{rows}</div><div class="metric-label">{t("rows", lang)}</div></div>', unsafe_allow_html=True)

#         if result.get("error"):
#             st.error(f"{t('exec_error', lang)}: {result['error']}")

#         if result["execution_result"]:
#             st.markdown(f'<div class="section-title">{t("results", lang)}</div>', unsafe_allow_html=True)

#             # Summary on demand
#             if st.button(t("generate_summary", lang), width='stretch'):
#                 with st.spinner(t("generating_sql", lang)):
#                     try:
#                         payload = {
#                             "question": user_question,
#                             "sql_query": result["sql"],
#                             "results": result["execution_result"]
#                         }
#                         res = requests.post(f"{API_BASE_URL}/quick-insights", json=payload)
#                         if res.status_code == 200:
#                             insights = res.json()["insights"]
#                             st.markdown(
#                                 f'<div class="summary-box"><h4>{t("summary_box_title", lang)}</h4>'
#                                 + "".join(f"<p>• {insight}</p>" for insight in insights)
#                                 + '</div>',
#                                 unsafe_allow_html=True
#                             )
#                         else:
#                             st.warning(t("summary_warning", lang))
#                     except Exception as e:
#                         st.error(f"{t('summary_failed', lang)}: {e}")

#             # Results table
#             df = pd.DataFrame(result["execution_result"])
#             gb = GridOptionsBuilder.from_dataframe(df)
#             gb.configure_default_column(filterable=True, sortable=True, resizable=True)
#             AgGrid(df, gridOptions=gb.build(), height=min(400, 25 * len(df) + 150), theme="alpine")

#             # Download
#             st.download_button(
#                 "📥 " + t("download_results_csv", lang),
#                 df.to_csv(index=False).encode("utf-8"),
#                 f"sqlwhisper_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
#                 "text/csv",
#                 width='stretch'
#             )

# # ============================================================
# # TAB 2: HISTORY
# # ============================================================
# with tabs[1]:
#     st.markdown(f'<div class="section-title">{t("history_tab", lang)}</div>', unsafe_allow_html=True)

#     if os.path.exists(HISTORY_FILE):
#         df = pd.read_csv(HISTORY_FILE)

#         if not df.empty:
#             # Translate content if Arabic selected
#             if lang == "ar":
#                 df["success"] = df["success"].replace(t("success_labels", lang))
#                 df["valid_sql"] = df["valid_sql"].replace(t("valid_sql_labels", lang))
#                 df["confidence_label"] = df["confidence_label"].replace(t("confidence_labels", lang))
#                 df.rename(columns=t("history_columns", lang), inplace=True)
#             else:
#                 df.rename(columns=t("history_columns", lang), inplace=True)

#             AgGrid(df.sort_values(by=df.columns[0], ascending=False), height=500, theme="alpine")
#         else:
#             st.info(t("no_history_yet", lang))
#     else:
#         st.info(t("no_query_history", lang))

# # ============================================================
# #  TAB 3: FEEDBACK
# # ============================================================
# with tabs[2]:
#     st.markdown(f'<div class="section-title">{t("user_feedback_review", lang)}</div>', unsafe_allow_html=True)

#     try:
#         conn = sqlite3.connect("data/my_database.sqlite")
#         df = pd.read_sql("SELECT * FROM sql_feedback ORDER BY created_at DESC", conn)
#         conn.close()

#         if not df.empty:
#             df["verdict"] = df["verdict"].replace(t("verdict_labels", lang))
#             df.rename(columns=t("feedback_columns", lang), inplace=True)
#             st.dataframe(df, width='stretch')
#         else:
#             st.info(t("no_feedback", lang))
#     except Exception as e:
#         st.error(f"{t('error_loading_feedback', lang)}: {e}")

# # ============================================================
# # TAB 4: DASHBOARD
# # ============================================================
# with tabs[3]:
#     st.markdown(f'<div class="section-header"><h2>{t("system_db_dashboard", lang)}</h2></div>', unsafe_allow_html=True)

#     DB_PATH = Path("data/my_database.sqlite")

#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         # ---------- Database Overview ----------
#         cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#         tables = [row[0] for row in cursor.fetchall()]
#         db_stats = []
#         for table in tables:
#             try:
#                 cursor.execute(f"SELECT COUNT(*) FROM {table}")
#                 count = cursor.fetchone()[0]
#                 db_stats.append({"Table": table, "Rows": count})
#             except Exception:
#                 db_stats.append({"Table": table, "Rows": "?"})

#         df_db_stats = pd.DataFrame(db_stats)

#         st.subheader(t("database_overview", lang))
#         col1, col2 = st.columns(2)
#         col1.metric(t("total_tables", lang), len(tables))
#         total_rows = df_db_stats["Rows"].replace("?", 0).astype(int).sum()
#         col2.metric(t("total_rows", lang), total_rows)

#         # ---------- Bar Chart — Table Sizes ----------
#         if not df_db_stats.empty:
#             chart = px.bar(
#                 df_db_stats,
#                 x="Table",
#                 y="Rows",
#                 title=t("total_rows", lang),
#                 color="Table",
#                 text="Rows",
#                 template="plotly_white"
#             )
#             chart.update_traces(textposition="outside")
#             st.plotly_chart(chart, use_container_width=True)

#         # ---------- Schema Explorer ----------
#         st.subheader(t("schema_details", lang))
#         schema_data = []
#         for table in tables:
#             cursor.execute(f"PRAGMA table_info({table})")
#             cols = cursor.fetchall()
#             for col in cols:
#                 schema_data.append({"Table": table, "Column": col[1], "Type": col[2]})
#         df_schema = pd.DataFrame(schema_data)
#         st.dataframe(df_schema, use_container_width=True, height=300)

#         # ---------- Query & Model Insights ----------
#         st.subheader(t("query_model_insights", lang))
#         if os.path.exists("streamlit_app/history.csv"):
#             df_hist = pd.read_csv("streamlit_app/history.csv")

#             # Core metrics
#             total_queries = len(df_hist)
#             success_rate = (df_hist["success"].sum() / total_queries * 100) if total_queries > 0 else 0
#             avg_conf = np.mean([r for r in df_hist.get("confidence", []) if pd.notnull(r)]) if "confidence" in df_hist.columns else None

#             c1, c2, c3 = st.columns(3)
#             c1.metric(t("total_queries", lang), total_queries)
#             c2.metric(t("success_rate", lang), f"{success_rate:.1f}%")
#             c3.metric("Avg Confidence" if lang == "en" else "متوسط الثقة", f"{avg_conf:.1f}%" if avg_conf else "N/A")

#             # ---------- Trend chart for query success ----------
#             df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"], errors="coerce")
#             df_hist = df_hist.sort_values("timestamp")

#             if len(df_hist) > 1:
#                 # Trend of queries over time
#                 fig_q = px.line(
#                     df_hist,
#                     x="timestamp",
#                     y="success",
#                     markers=True,
#                     title=t("query_success_trend", lang),
#                     template="plotly_white"
#                 )
#                 fig_q.update_yaxes(title=t("success", lang))
#                 st.plotly_chart(fig_q, use_container_width=True)

#                 # ---------- Confidence trend ----------
#                 if "confidence" in df_hist.columns and df_hist["confidence"].notna().any():
#                     fig_conf = px.line(
#                         df_hist,
#                         x="timestamp",
#                         y="confidence",
#                         title=t("model_conf_trend", lang),
#                         template="plotly_white",
#                         markers=True,
#                         line_shape="spline"
#                     )
#                     fig_conf.update_yaxes(range=[0, 100])
#                     st.plotly_chart(fig_conf, use_container_width=True)
#                 else:
#                     st.info(t("confidence_unavailable", lang))
#             else:
#                 st.info(t("no_query_yet_run", lang))
#         else:
#             st.info(t("no_query_history", lang))

#         conn.close()
#     except Exception as e:
#         st.error(f"{t('error_loading_dashboard', lang)}: {e}")

# # ============================================================
# # TAB 5: ABOUT
# # ============================================================
# with tabs[4]:
#     st.markdown(f'<div class="section-title">{t("about_sqlwhisper", lang)}</div>', unsafe_allow_html=True)
#     st.markdown(t("about_rich_html", lang), unsafe_allow_html=True)

# # ============================================================
# #  FOOTER
# # ============================================================
# # st.markdown("""
# # <hr style='margin-top:3rem; border-top:1px solid #e0e0e0;'>
# # <div style='text-align:center; color:#6A0DAD; font-weight:600; font-size:0.95rem;'>
# #     © 2025 Made with 💜 by <span style='color:#8A2BE2;'>SQLWhisper Team</span>
# # </div>
# # """, unsafe_allow_html=True)
# render_footer()
