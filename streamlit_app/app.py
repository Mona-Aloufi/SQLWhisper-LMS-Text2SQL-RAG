# streamlit_app/app.py
import streamlit as st
import pandas as pd
import requests
import re
import os
import json
from st_aggrid import AgGrid, GridOptionsBuilder
from PIL import Image

# Page configuration
st.set_page_config(page_title="SQLWhisper", page_icon="💜", layout="centered")

# Custom CSS for enhanced purple theme
st.markdown("""
<style>
    .main-header {
        color: #6a0dad;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 3rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(106, 13, 173, 0.3);
    }
    .sub-header {
        color: #8a2be2;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.2rem;
        font-style: italic;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e6f7ff;
        border: 2px solid #6a0dad;
        color: #6a0dad;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffe6e6;
        border: 2px solid #ff4444;
        color: #cc0000;
        margin: 1rem 0;
    }
    .sql-box {
        background-color: #f5f0ff;
        padding: 1.5rem;
        border-radius: 0.8rem;
        border-left: 6px solid #8a2be2;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(138, 43, 226, 0.1);
        color: #4b0082;
        font-size: 1.1rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #6a0dad, #8a2be2);
        padding: 1.5rem;
        border-radius: 0.8rem;
        border: none;
        text-align: center;
        color: white;
        box-shadow: 0 4px 8px rgba(106, 13, 173, 0.3);
    }
    .purple-button {
        background: linear-gradient(135deg, #6a0dad, #8a2be2);
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(106, 13, 173, 0.3);
    }
    .purple-button:hover {
        background: linear-gradient(135deg, #5a0cad, #7a1bd2);
        box-shadow: 0 4px 8px rgba(106, 13, 173, 0.4);
    }
    .section-header {
        color: #6a0dad;
        border-bottom: 3px solid #8a2be2;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .sidebar-header {
        color: #6a0dad;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title + optional logo
try:
    logo = Image.open("streamlit_app/logo.png")
    st.image(logo, width=100)
except Exception:
    pass

st.markdown('<div class="main-header"><h1>SQLWhisper</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header"><h4>From Questions To Queries - Instantly</h4></div>', unsafe_allow_html=True)

# API config
API_BASE_URL = "http://127.0.0.1:8000"

# History file
HISTORY_FILE = "streamlit_app/history.csv"

def log_question(question, sql_query, success, valid_sql=False, rows_returned=0, error_message=None):
    row = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "question": question,
        "sql_query": sql_query,
        "success": success,
        "valid_sql": valid_sql,
        "rows_returned": rows_returned,
        "error_message": error_message or ""
    }
    
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        expected_cols = ["timestamp", "question", "sql_query", "success", "valid_sql", "rows_returned", "error_message"]
        if list(df.columns) != expected_cols:
            df = pd.DataFrame(columns=expected_cols)
    else:
        df = pd.DataFrame(columns=expected_cols)
    
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

# Session state
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

# Helper functions
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
    except Exception as e:
        st.session_state.database_info = None
        return None

# Sidebar - Simplified
with st.sidebar:
    st.markdown('<div class="sidebar-header">Database Information</div>', unsafe_allow_html=True)
    
    if st.button("Load Database Schema", use_container_width=True):
        with st.spinner("Loading database schema..."):
            db_info = get_database_info()
            if db_info:
                st.success(f"Connected to database")
                st.write(f"**Tables:** {', '.join(db_info['tables'])}")
                st.write(f"**Total tables:** {db_info['total_tables']}")
            else:
                st.error("Failed to load database info")

# Tabs - Removed Test tab
tab1, tab2, tab3 = st.tabs(["Query", "History", "About"])

# Tab 1: Query
with tab1:
    st.markdown('<div class="section-header"><h2>Ask a Question</h2></div>', unsafe_allow_html=True)

    if not check_api_health():
        st.error("FastAPI backend is not running! Please start the server first.")
        st.code("python app.py")
        st.stop()

    # Get sample queries
    try:
        response = requests.get(f"{API_BASE_URL}/sample-queries")
        if response.status_code == 200:
            sample_queries = response.json()["sample_queries"]
        else:
            sample_queries = [
                "Show all tables in the database",
                "Count the total number of records",
                "List the first 5 rows from all tables",
                "What is the database schema?",
            ]
    except:
        sample_queries = [
            "Show all tables in the database",
            "Count the total number of records", 
            "List the first 5 rows",
            "What is the database structure?",
        ]

    # Suggested queries in a more elegant layout
    st.write("### Quick Start Queries")
    cols = st.columns(2)
    for i, q in enumerate(sample_queries[:4]):
        col_idx = i % 2
        if cols[col_idx].button(q, key=f"suggest_{i}", use_container_width=True):
            st.session_state.last_question = q
            st.session_state.generated_sql = ""
            st.session_state.last_result = None

    st.markdown("---")
    
    # User input section
    user_question = st.text_area(
        "### Your Question", 
        value=st.session_state.last_question or "",
        height=120,
        placeholder="Describe what you want to know about your data...\nExamples:\n- Show all customers from London\n- Count orders by status\n- Find the top 5 products by sales\n- List employees hired in the last month"
    )

    # Action buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Generate SQL Query", type="primary", use_container_width=True):
            if not user_question.strip():
                st.warning("Please enter a question first.")
            else:
                st.session_state.last_question = user_question
                with st.spinner("Analyzing your question and generating SQL..."):
                    try:
                        payload = {"question": user_question}
                        response = requests.post(f"{API_BASE_URL}/test-query", json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.generated_sql = data["sql"]
                            st.session_state.last_result = data
                            
                            log_question(
                                user_question, 
                                data["sql"], 
                                True, 
                                data["valid"],
                                len(data["execution_result"]) if data["execution_result"] else 0
                            )
                            
                            st.success("SQL query generated successfully!")
                        else:
                            error_msg = f"API Error: {response.text}"
                            st.error(error_msg)
                            log_question(user_question, "", False, error_message=error_msg)
                            
                    except Exception as e:
                        error_msg = f"Request failed: {e}"
                        st.error(error_msg)
                        log_question(user_question, "", False, error_message=error_msg)

    with col2:
        if st.session_state.generated_sql:
            if st.button("Clear Results", use_container_width=True):
                st.session_state.generated_sql = ""
                st.session_state.last_result = None
                st.rerun()

    # Display results
    if st.session_state.generated_sql and st.session_state.last_result:
        result = st.session_state.last_result
        
        st.markdown("---")
        st.markdown('<div class="section-header"><h2>Generated SQL</h2></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sql-box">{result["sql"]}</div>', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-box">SQL Syntax<br><strong>VALID</strong></div>' 
                       if result["valid"] 
                       else '<div style="background: linear-gradient(135deg, #ff6b6b, #ff4444); padding: 1.5rem; border-radius: 0.8rem; text-align: center; color: white;">SQL Syntax<br><strong>INVALID</strong></div>', 
                       unsafe_allow_html=True)
        
        with col2:
            if result["execution_result"] is not None:
                st.markdown('<div class="metric-box">Execution<br><strong>SUCCESS</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background: linear-gradient(135deg, #ffa726, #ff9800); padding: 1.5rem; border-radius: 0.8rem; text-align: center; color: white;">Execution<br><strong>FAILED</strong></div>', unsafe_allow_html=True)
        
        with col3:
            if result["execution_result"]:
                st.markdown(f'<div class="metric-box">Results<br><strong>{len(result["execution_result"])} ROWS</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-box">Results<br><strong>NO DATA</strong></div>', unsafe_allow_html=True)
        
        # Execution error if any
        if result["error"]:
            st.markdown(f'<div class="error-box">Execution Error: {result["error"]}</div>', unsafe_allow_html=True)
        
        # Show results table
        if result["execution_result"]:
            st.markdown("---")
            st.markdown('<div class="section-header"><h2>Query Results</h2></div>', unsafe_allow_html=True)
            df = pd.DataFrame(result["execution_result"])
            
            # Use AgGrid for interactive table
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(
                filterable=True, 
                sortable=True, 
                resizable=True,
                minWidth=100
            )
            grid_options = gb.build()
            
            AgGrid(
                df, 
                gridOptions=grid_options, 
                height=min(400, 35 * len(df) + 100), 
                fit_columns_on_grid_load=False,
                theme="streamlit"
            )
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"query_result_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )
        
        # Raw output expander
        with st.expander("View Raw Model Output"):
            st.text(result.get("raw_output", "No raw output available"))

# Tab 2: History
with tab2:
    st.markdown('<div class="section-header"><h2>Query History</h2></div>', unsafe_allow_html=True)
    
    try:
        if os.path.exists(HISTORY_FILE):
            df_hist = pd.read_csv(HISTORY_FILE)
            
            if not df_hist.empty:
                # Calculate metrics
                total_queries = len(df_hist)
                successful_queries = len(df_hist[df_hist['success'] == True])
                valid_sql_queries = len(df_hist[df_hist['valid_sql'] == True])
                success_rate = (successful_queries / total_queries) * 100
                
                # Metrics in purple theme
                col1, col2, col3, col4 = st.columns(4)
                col1.markdown(f'<div class="metric-box">Total Queries<br><strong>{total_queries}</strong></div>', unsafe_allow_html=True)
                col2.markdown(f'<div class="metric-box">Successful<br><strong>{successful_queries}</strong></div>', unsafe_allow_html=True)
                col3.markdown(f'<div class="metric-box">Valid SQL<br><strong>{valid_sql_queries}</strong></div>', unsafe_allow_html=True)
                col4.markdown(f'<div class="metric-box">Success Rate<br><strong>{success_rate:.1f}%</strong></div>', unsafe_allow_html=True)
                
                # Display history table
                df_display = df_hist.copy()
                df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                gb = GridOptionsBuilder.from_dataframe(df_display)
                gb.configure_default_column(
                    filterable=True, 
                    sortable=True, 
                    resizable=True,
                    minWidth=100
                )
                
                grid_options = gb.build()
                
                AgGrid(
                    df_display, 
                    gridOptions=grid_options, 
                    height=400,
                    theme="streamlit"
                )
                
                # Download button
                csv = df_hist.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Complete History", 
                    csv, 
                    file_name="sqlwhisper_complete_history.csv", 
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No query history yet. Start by asking questions in the Query tab!")
        else:
            st.info("No history yet. Your first query will create the history file.")
            
    except Exception as e:
        st.error(f"Error loading history: {e}")

# Tab 3: About
with tab3:
    st.markdown('<div class="section-header"><h2>About SQLWhisper</h2></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f5f0ff, #e6e6ff); padding: 2rem; border-radius: 1rem; border-left: 6px solid #8a2be2;'>
    <h3 style='color: #6a0dad; margin-top: 0;'>AI-Powered SQL Query Generation</h3>
    
    SQLWhisper transforms your natural language questions into precise SQL queries, 
    making database interaction intuitive and accessible to everyone.
    
    <h4 style='color: #6a0dad;'>Key Features:</h4>
    <ul>
    <li><strong>Natural Language Processing</strong> - Ask questions in plain English</li>
    <li><strong>Smart Schema Detection</strong> - Automatically understands your database structure</li>
    <li><strong>SQL Validation</strong> - Ensures generated queries are syntactically correct</li>
    <li><strong>Instant Execution</strong> - Run queries and see results immediately</li>
    <li><strong>Interactive Results</strong> - Filter, sort, and explore your data</li>
    </ul>
    
    <h4 style='color: #6a0dad;'>Technical Excellence:</h4>
    <ul>
    <li>Built with FastAPI for robust backend performance</li>
    <li>Powered by advanced open-source language models</li>
    <li>Real-time SQL syntax validation</li>
    <li>Comprehensive query history and analytics</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # System status in a clean layout
    st.markdown("---")
    st.subheader("System Status")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        if check_api_health():
            st.markdown('<div class="success-box"><strong>Backend Status:</strong> Operational</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box"><strong>Backend Status:</strong> Not Available</div>', unsafe_allow_html=True)
    
    with status_col2:
        if st.session_state.database_info:
            st.markdown(f'<div class="success-box"><strong>Database:</strong> Connected ({len(st.session_state.database_info["tables"])} tables)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box"><strong>Database:</strong> Not Loaded</div>', unsafe_allow_html=True)