import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from pathlib import Path
import numpy as np
import requests
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from PIL import Image

# Paths
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
HISTORY_FILE = "streamlit_app/history.csv"
API_BASE_URL = "http://127.0.0.1:8000"

# Page config
st.set_page_config(
    page_title="SQLWhisper",
    page_icon=logo_path,
    layout="wide"
)

# Custom CSS – modern, clean, professional
st.markdown("""
<style>
    /* Base reset */
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .app-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .app-header img {
        height: 60px;
    }
    .app-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4b0082;
        margin: 0;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #7e57c2;
        font-weight: 400;
        margin-top: 0.25rem;
    }

    /* Cards */
    .stCard {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(106, 13, 173, 0.08);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #f0f0f0;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6a0dad, #8a2be2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(106, 13, 173, 0.3);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* SQL box */
    .sql-display {
        background: #f9f7ff;
        border-left: 4px solid #8a2be2;
        padding: 1.2rem;
        border-radius: 8px;
        font-family: 'SF Mono', 'Consolas', 'Courier New', monospace;
        font-size: 1.05rem;
        line-height: 1.5;
        margin: 1.2rem 0;
        overflow-x: auto;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.2rem;
    }

    /* Summary box */
    .summary-box {
        background: #f8f9ff;
        border: 1px solid #e6e6ff;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1.2rem 0;
    }

    /* Section headers */
    .section-title {
        font-size: 1.4rem;
        color: #5a1a8c;
        margin: 1.8rem 0 1rem;
        font-weight: 600;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #f0f0ff;
    }

    /* Feedback area */
    .feedback-area {
        background: #faf9ff;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }

    /* Metrics */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 3px 10px rgba(106, 13, 173, 0.07);
        border: 1px solid #f3f3f3;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6a0dad;
        margin: 0.3rem 0;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #777;
        font-weight: 500;
    }

    /* Inputs */
    .stTextArea textarea, .stTextInput input {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #6a0dad !important;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER WITH LOGO (TOP-LEFT) ===
header_col1, header_col2 = st.columns([0.2, 0.8])
with header_col1:
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=80)
    except:
        st.write("LOGO")
with header_col2:
    st.markdown('<h1 class="app-title">SQLWhisper</h1>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">Transform natural language questions into accurate SQL queries</p>', unsafe_allow_html=True)

# === SESSION STATE & HELPERS ===
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "database_info" not in st.session_state:
    st.session_state.database_info = None
if "api_health" not in st.session_state:
    st.session_state.api_health = None

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

def log_question(question, sql_query, success, valid_sql=False, rows_returned=0, error_message=None, confidence=None, confidence_label=None):
    expected_cols = ["timestamp", "question", "sql_query", "success", "valid_sql", "rows_returned", "error_message", "confidence", "confidence_label"]
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

# === SIDEBAR ===
with st.sidebar:
    st.markdown('<div class="sidebar-header"><h3>Database</h3></div>', unsafe_allow_html=True)
    if st.button("Load Schema", use_container_width=True):
        with st.spinner("Fetching schema..."):
            db_info = get_database_info()
            if db_info:
                st.success("Schema loaded")
                st.caption(f"**Tables:** {', '.join(db_info['tables'])}")
            else:
                st.error("Failed to load schema")

# === TABS ===
tabs = st.tabs(["Query", "History", "Feedback", "Dashboard", "About"])

# === TAB 1: QUERY ===
with tabs[0]:
    if not check_api_health():
        st.error("Backend service is offline. Please start the FastAPI server.")
        st.code("uvicorn main:app --reload")
        st.stop()

    # Sample queries
    try:
        sample_queries = requests.get(f"{API_BASE_URL}/sample-queries").json()["sample_queries"]
    except:
        sample_queries = ["Show all tables", "Count total records", "List first 5 rows", "Describe table schema"]

    st.markdown('<div class="section-title">Quick Start</div>', unsafe_allow_html=True)
    quick_cols = st.columns(2)
    for i, q in enumerate(sample_queries[:4]):
        if quick_cols[i % 2].button(q, key=f"sample_{i}", use_container_width=True):
            st.session_state.last_question = q
            st.session_state.generated_sql = ""
            st.session_state.last_result = None

    st.markdown('<div class="section-title">Your Question</div>', unsafe_allow_html=True)
    user_question = st.text_area(
        label="Ask anything about your data...",
        value=st.session_state.last_question,
        height=100,
        label_visibility="collapsed"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Generate SQL", type="primary", use_container_width=True):
            if not user_question.strip():
                st.warning("Please enter a question.")
            else:
                st.session_state.last_question = user_question
                with st.spinner("Generating SQL query..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/test-query", json={"question": user_question})
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
                            st.success("SQL query generated and executed.")
                        else:
                            st.error(f"API Error: {res.text}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

    with col_btn2:
        if st.session_state.generated_sql and st.button("Clear", use_container_width=True):
            st.session_state.generated_sql = ""
            st.session_state.last_result = None
            st.rerun()

    # RESULTS DISPLAY
    if st.session_state.generated_sql and st.session_state.last_result:
        result = st.session_state.last_result

        st.markdown('<div class="section-title">Generated Query</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sql-display">{result["sql"]}</div>', unsafe_allow_html=True)

        # Confidence badge
        if result.get("confidence"):
            label = result["confidence_label"]
            color = {"High": "#4caf50", "Medium": "#ff9800", "Low": "#f44336"}.get(label, "#9e9e9e")
            st.markdown(f'<span class="status-badge" style="background-color:{color}20; color:{color};">Confidence: {result["confidence"]}% ({label})</span>', unsafe_allow_html=True)

        # Feedback section
        st.markdown('<div class="section-title">Feedback</div>', unsafe_allow_html=True)
        fb_col1, fb_col2 = st.columns(2)

        with fb_col1:
            if st.button("Accurate", use_container_width=True):
                requests.post(f"{API_BASE_URL}/feedback", json={
                    "question": user_question,
                    "generated_sql": result["sql"],
                    "verdict": "up",
                    "comment": None,
                    "user_correction": None
                })
                st.success("Thank you for your feedback.")

        with fb_col2:
            st.markdown('<div class="feedback-area">', unsafe_allow_html=True)
            comment = st.text_input("What was incorrect?", key="fb_comment", placeholder="Optional explanation")
            correction = st.text_area("Suggested SQL (optional)", key="fb_correction", height=100)
            if st.button("Needs Correction", use_container_width=True):
                requests.post(f"{API_BASE_URL}/feedback", json={
                    "question": user_question,
                    "generated_sql": result["sql"],
                    "verdict": "down",
                    "comment": comment or None,
                    "user_correction": correction or None
                })
                st.success("Correction submitted.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Metrics row
        st.markdown('<div class="section-title">Execution Metrics</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            valid = result["valid"]
            st.markdown(f'<div class="metric-card"><div class="metric-value">{"✓" if valid else "✗"}</div><div class="metric-label">Syntax Valid</div></div>', unsafe_allow_html=True)
        with m2:
            executed = result["execution_result"] is not None
            st.markdown(f'<div class="metric-card"><div class="metric-value">{"✓" if executed else "✗"}</div><div class="metric-label">Executed</div></div>', unsafe_allow_html=True)
        with m3:
            rows = len(result["execution_result"]) if result["execution_result"] else 0
            st.markdown(f'<div class="metric-card"><div class="metric-value">{rows}</div><div class="metric-label">Rows Returned</div></div>', unsafe_allow_html=True)

        if result.get("error"):
            st.error(f"Execution error: {result['error']}")

        if result["execution_result"]:
            st.markdown('<div class="section-title">Results</div>', unsafe_allow_html=True)

            # Summary on demand
            if st.button("Generate Summary", use_container_width=True):
                with st.spinner("Analyzing results..."):
                    try:
                        payload = {
                            "question": user_question,
                            "sql_query": result["sql"],
                            "results": result["execution_result"]
                        }
                        res = requests.post(f"{API_BASE_URL}/quick-insights", json=payload)
                        if res.status_code == 200:
                            insights = res.json()["insights"]
                            st.markdown('<div class="summary-box"><h4>Key Insights</h4>' + "".join(f"<p>• {insight}</p>" for insight in insights) + '</div>', unsafe_allow_html=True)
                        else:
                            st.warning("Could not generate summary.")
                    except Exception as e:
                        st.error(f"Summary failed: {e}")

            # Results table
            df = pd.DataFrame(result["execution_result"])
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(filterable=True, sortable=True, resizable=True)
            AgGrid(df, gridOptions=gb.build(), height=min(400, 25 * len(df) + 150), theme="alpine")

            # Download
            st.download_button(
                "📥 Download Results (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                f"sqlwhisper_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

# === OTHER TABS (Brief – can be expanded later) ===
with tabs[1]:  # History
    st.markdown('<div class="section-title">Query History</div>', unsafe_allow_html=True)
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        if not df.empty:
            AgGrid(df.sort_values("timestamp", ascending=False), height=500, theme="alpine")
        else:
            st.info("No history yet.")
    else:
        st.info("History will appear after your first query.")

with tabs[2]:  # Feedback
    st.markdown('<div class="section-title">User Feedback</div>', unsafe_allow_html=True)
    try:
        conn = sqlite3.connect("data/my_database.sqlite")
        df = pd.read_sql("SELECT * FROM sql_feedback ORDER BY created_at DESC", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df[["question", "verdict", "comment", "created_at"]], use_container_width=True)
        else:
            st.info("No feedback submitted yet.")
    except Exception as e:
        st.error(f"Could not load feedback: {e}")

with tabs[3]:  # Dashboard
    st.markdown('<div class="section-title">System Dashboard</div>', unsafe_allow_html=True)
    st.info("Enhanced analytics and database insights will appear here.")

with tabs[4]:  # About
    st.markdown('<div class="section-title">About SQLWhisper</div>', unsafe_allow_html=True)
    st.markdown("""
    **SQLWhisper** is an AI-powered natural language interface for databases.
    
    - Translate plain English questions into validated SQL
    - Execute queries safely (read-only)
    - Review, correct, and improve results collaboratively
    - Built with FastAPI, Streamlit, and open-source LLMs
    
    Designed for analysts, developers, and non-technical users alike.
    """)
