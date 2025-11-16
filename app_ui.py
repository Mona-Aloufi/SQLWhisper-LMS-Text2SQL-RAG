# app_ui.py - Simplified Testing UI for main.py endpoints
import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict, Any
import time
from datetime import datetime

# Set your FastAPI backend URL
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="SQLWhisper Testing UI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean CSS for modern UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stExpander {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .badge-success {
        background-color: #e6f4ea;
        color: #137333;
    }
    .badge-error {
        background-color: #fce8e6;
        color: #c5221f;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'current_schema' not in st.session_state:
    st.session_state.current_schema = None
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'auto_execute' not in st.session_state:
    st.session_state.auto_execute = True
if 'last_generated_sql' not in st.session_state:
    st.session_state.last_generated_sql = None

# Helper function for status badges
def status_badge(status: str, label: str):
    if status == "success":
        return f'<span class="status-badge badge-success">{label}</span>'
    elif status == "error":
        return f'<span class="status-badge badge-error">{label}</span>'
    return f'<span class="status-badge">{label}</span>'

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("SQLWhisper Text2SQL")
    st.markdown("*Transform natural language into SQL queries*")
with col2:
    if st.session_state.db_connected:
        st.markdown(status_badge("success", "Connected"), unsafe_allow_html=True)
    else:
        st.markdown(status_badge("error", "Disconnected"), unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Dashboard", "Database Setup", "SQL Playground", "Test Results"],
    label_visibility="collapsed"
)

# Sidebar settings
st.sidebar.markdown("---")
st.sidebar.subheader("Settings")
st.session_state.auto_execute = st.sidebar.checkbox(
    "Auto-execute generated SQL",
    value=st.session_state.auto_execute
)

# Sidebar connection info
st.sidebar.markdown("---")
st.sidebar.subheader("Connection Status")
if st.session_state.db_connected:
    st.sidebar.success("Database Connected")
    if st.session_state.current_schema:
        st.sidebar.metric("Available Tables", len(st.session_state.current_schema))
else:
    st.sidebar.warning("No Database Connected")

# Dashboard Page
if page == "Dashboard":
    st.header("Dashboard")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tests", len(st.session_state.test_results))
    
    with col2:
        successful_tests = sum(1 for t in st.session_state.test_results 
                              if t.get('result', {}).get('success') or t.get('generation_result', {}).get('valid'))
        st.metric("Successful", successful_tests)
    
    with col3:
        status = "Active" if st.session_state.db_connected else "Inactive"
        st.metric("Connection", status)
    
    with col4:
        avg_confidence = 0
        confidence_tests = [t.get('result', {}).get('confidence') or t.get('generation_result', {}).get('confidence') 
                           for t in st.session_state.test_results]
        confidence_tests = [c for c in confidence_tests if c]
        if confidence_tests:
            avg_confidence = sum(confidence_tests) / len(confidence_tests)
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    st.markdown("---")
    
    # Quick Start
    st.subheader("Quick Start")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Getting Started
        1. **Connect Database** - Upload SQLite or connect external DB
        2. **Ask Questions** - Use natural language queries
        3. **Review Results** - Check generated SQL and execution results
        """)
        
        if not st.session_state.db_connected:
            if st.button("Connect Database Now", use_container_width=True):
                st.info("Please go to the 'Database Setup' page to connect a database.")
    
    with col2:
        st.markdown("### Recent Activity")
        if st.session_state.test_results:
            recent_tests = st.session_state.test_results[-5:]
            for i, test in enumerate(reversed(recent_tests)):
                question = test.get('question', test.get('sql', 'N/A'))[:50]
                st.text(f"{len(st.session_state.test_results) - i}. {question}...")
        else:
            st.info("No recent activity")

# Database Setup Page
elif page == "Database Setup":
    st.header("Database Connection")
    
    tab1, tab2 = st.tabs(["Upload SQLite", "External Database"])
    
    with tab1:
        st.markdown("### Upload SQLite Database File")
        
        uploaded_file = st.file_uploader(
            "Choose a SQLite file",
            type=["db", "sqlite", "sqlite3"]
        )
        
        if uploaded_file is not None:
            files = {"file": (uploaded_file.name, uploaded_file, "application/octet-stream")}
            
            if st.button("Upload & Connect", type="primary", use_container_width=True):
                try:
                    with st.spinner("Processing..."):
                        response = requests.post(f"{API_URL}/upload-db", files=files)
                        
                        if response.status_code == 200:
                            res = response.json()
                            if "error" in res:
                                st.error(f"Upload failed: {res['error']}")
                            else:
                                st.success("Database connected successfully!")
                                st.session_state.current_schema = res.get("schema", {})
                                st.session_state.db_connected = True
                                
                                # Display schema
                                st.markdown("### Database Schema")
                                schema = res.get("schema", {})
                                if schema:
                                    cols = st.columns(2)
                                    for idx, (table_name, columns) in enumerate(schema.items()):
                                        with cols[idx % 2]:
                                            with st.expander(f"**{table_name}**"):
                                                if isinstance(columns, list):
                                                    st.markdown(f"*{len(columns)} columns*")
                                                    for col in columns:
                                                        st.markdown(f"• `{col}`")
                                                else:
                                                    st.json(columns)
                        else:
                            st.error(f"Upload failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Upload request failed: {e}")
    
    with tab2:
        st.markdown("### Connect to External Database")
        
        with st.form("external_db_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                db_type = st.selectbox("Database Type", ["postgresql", "mysql"])
                host = st.text_input("Host", "localhost")
                database = st.text_input("Database Name")
            
            with col2:
                port = st.number_input("Port", value=5432 if db_type == "postgresql" else 3306)
                user = st.text_input("Username")
                password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Connect", type="primary", use_container_width=True)
            
            if submitted:
                payload = {
                    "db_type": db_type,
                    "host": host,
                    "port": int(port),
                    "database": database,
                    "user": user,
                    "password": password
                }
                try:
                    with st.spinner("Connecting..."):
                        response = requests.post(f"{API_URL}/connect-db", json=payload)
                        
                        if response.status_code == 200:
                            res = response.json()
                            if "error" in res:
                                st.error(f"Connection failed: {res['error']}")
                            else:
                                st.success(f"Connected to {db_type} database!")
                                st.session_state.current_schema = res.get("schema", {})
                                st.session_state.db_connected = True
                        else:
                            st.error(f"Connection failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection request failed: {e}")

# SQL Playground Page
elif page == "SQL Playground":
    st.header("SQL Playground")
    
    if not st.session_state.db_connected:
        st.warning("Please connect to a database first in the 'Database Setup' page.")
    else:
        st.markdown("### Ask Your Question")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            question = st.text_input(
                "Enter your natural language question",
                placeholder="e.g., Show me all customers who made purchases last month",
                label_visibility="collapsed"
            )
        
        with col2:
            execute_btn = st.button("Generate & Execute", type="primary", use_container_width=True)
        
        # Execute query
        if execute_btn and question.strip():
            try:
                with st.spinner("Processing..."):
                    # Generate SQL
                    gen_response = requests.post(f"{API_URL}/generate-sql", json={"question": question})
                    
                    if gen_response.status_code == 200:
                        gen_result = gen_response.json()
                        
                        if "error" in gen_result:
                            st.error(f"SQL generation failed: {gen_result['error']}")
                        else:
                            generated_sql = gen_result.get("sql", "")
                            st.session_state.last_generated_sql = generated_sql
                            
                            # Display generated SQL
                            st.markdown("### Generated SQL")
                            st.code(generated_sql, language="sql")
                            
                            # Metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                valid = gen_result.get("valid")
                                st.metric("Valid", "Yes" if valid else "No")
                            with col2:
                                confidence = gen_result.get("confidence", 0)
                                st.metric("Confidence", f"{confidence:.1%}" if confidence else "N/A")
                            with col3:
                                is_safe = gen_result.get("is_safe")
                                st.metric("Safe", "Yes" if is_safe else "No")
                            
                            # Auto-execute if enabled and valid
                            if st.session_state.auto_execute and gen_result.get("valid") and generated_sql:
                                exec_response = requests.post(
                                    f"{API_URL}/execute-sql",
                                    json={"sql": generated_sql}
                                )
                                
                                if exec_response.status_code == 200:
                                    exec_result = exec_response.json()
                                    
                                    if "error" in exec_result:
                                        st.error(f"Execution failed: {exec_result['error']}")
                                    else:
                                        st.success("Query executed successfully")
                                        
                                        if exec_result.get("success"):
                                            if exec_result.get("query_type") == "SELECT":
                                                rows = exec_result.get("rows", [])
                                                columns = exec_result.get("columns", [])
                                                
                                                if rows:
                                                    df = pd.DataFrame(rows, columns=columns)
                                                    st.dataframe(df, use_container_width=True)
                                                    st.metric("Rows Returned", len(rows))
                                                    
                                                    # Generate and display summary
                                                    st.markdown("---")
                                                    st.markdown("### 📝 Natural Language Summary")
                                                    with st.spinner("Generating summary..."):
                                                        # Convert rows to list of dicts for summary API
                                                        results_dict = []
                                                        for row in rows:
                                                            row_dict = {}
                                                            for i, col in enumerate(columns):
                                                                row_dict[col] = row[i] if i < len(row) else None
                                                            results_dict.append(row_dict)
                                                        
                                                        # Call summary endpoint
                                                        summary_payload = {
                                                            "question": question,
                                                            "sql_query": generated_sql,
                                                            "results": results_dict
                                                        }
                                                        
                                                        summary_response = requests.post(
                                                            f"{API_URL}/generate-summary",
                                                            json=summary_payload
                                                        )
                                                        
                                                        if summary_response.status_code == 200:
                                                            summary_result = summary_response.json()
                                                            if summary_result.get("success"):
                                                                summary_text = summary_result.get("summary", "")
                                                                st.info(f"💬 {summary_text}")
                                                                
                                                                # Show summary metadata if available
                                                                if summary_result.get("confidence"):
                                                                    st.caption(f"Confidence: {summary_result.get('confidence', 0):.1%}")
                                                            else:
                                                                st.warning("Summary generation failed")
                                                        else:
                                                            st.warning("Could not generate summary")
                                                else:
                                                    st.info("Query executed successfully but returned no rows")
                                            else:
                                                st.info(f"Query type: {exec_result.get('query_type')}")
                                                st.metric("Affected Rows", exec_result.get("affected_rows", 0))
                                        
                                        # Store result
                                        st.session_state.test_results.append({
                                            "type": "auto_execute",
                                            "question": question,
                                            "generation_result": gen_result,
                                            "execution_result": exec_result,
                                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        })
                            else:
                                if not st.session_state.auto_execute:
                                    st.info("Auto-execution is disabled. Enable it in settings.")
                                elif not gen_result.get("valid"):
                                    st.warning("SQL is not valid. Cannot execute.")
                                
                                # Store generation result only
                                st.session_state.test_results.append({
                                    "type": "generate_only",
                                    "question": question,
                                    "generation_result": gen_result,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                    else:
                        st.error(f"Generation request failed: {gen_response.status_code}")
                        
            except Exception as e:
                st.error(f"Request error: {e}")
        
        # Custom SQL execution
        st.markdown("---")
        with st.expander("Advanced: Execute Custom SQL"):
            st.markdown("### Custom SQL Query")
            sql_input = st.text_area(
                "Enter your SQL query",
                height=150,
                placeholder="SELECT * FROM table_name LIMIT 10;",
                value=st.session_state.last_generated_sql if st.session_state.last_generated_sql else ""
            )
            
            if st.button("Execute Custom SQL", type="secondary", use_container_width=True):
                if not sql_input.strip():
                    st.warning("Please enter a SQL query first")
                else:
                    try:
                        with st.spinner("Executing..."):
                            response = requests.post(f"{API_URL}/execute-sql", json={"sql": sql_input})
                            
                            if response.status_code == 200:
                                res = response.json()
                                if "error" in res:
                                    st.error(f"Execution failed: {res['error']}")
                                else:
                                    st.success("Query executed successfully")
                                    
                                    if res.get("success"):
                                        if res.get("query_type") == "SELECT":
                                            rows = res.get("rows", [])
                                            columns = res.get("columns", [])
                                            
                                            if rows:
                                                df = pd.DataFrame(rows, columns=columns)
                                                st.dataframe(df, use_container_width=True)
                                                st.metric("Rows Returned", len(rows))
                                                
                                                # Generate and display summary
                                                st.markdown("---")
                                                st.markdown("### 📝 Natural Language Summary")
                                                with st.spinner("Generating summary..."):
                                                    # Convert rows to list of dicts for summary API
                                                    results_dict = []
                                                    for row in rows:
                                                        row_dict = {}
                                                        for i, col in enumerate(columns):
                                                            row_dict[col] = row[i] if i < len(row) else None
                                                        results_dict.append(row_dict)
                                                    
                                                    # Call summary endpoint (no question for custom SQL)
                                                    summary_payload = {
                                                        "question": f"Results from SQL query",
                                                        "sql_query": sql_input,
                                                        "results": results_dict
                                                    }
                                                    
                                                    summary_response = requests.post(
                                                        f"{API_URL}/generate-summary",
                                                        json=summary_payload
                                                    )
                                                    
                                                    if summary_response.status_code == 200:
                                                        summary_result = summary_response.json()
                                                        if summary_result.get("success"):
                                                            summary_text = summary_result.get("summary", "")
                                                            st.info(f"💬 {summary_text}")
                                                            
                                                            # Show summary metadata if available
                                                            if summary_result.get("confidence"):
                                                                st.caption(f"Confidence: {summary_result.get('confidence', 0):.1%}")
                                                        else:
                                                            st.warning("Summary generation failed")
                                                    else:
                                                        st.warning("Could not generate summary")
                                            else:
                                                st.info("Query executed successfully but returned no rows")
                                        else:
                                            st.info(f"Query type: {res.get('query_type')}")
                                            st.metric("Affected Rows", res.get("affected_rows", 0))
                                    
                                    # Store result
                                    st.session_state.test_results.append({
                                        "type": "custom_execute",
                                        "sql": sql_input,
                                        "result": res,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    })
                            else:
                                st.error(f"Request failed: {response.status_code}")
                    except Exception as e:
                        st.error(f"Request error: {e}")

# Test Results Page
elif page == "Test Results":
    st.header("Test Results History")
    
    if not st.session_state.test_results:
        st.info("No test results yet. Run some queries to see results here.")
    else:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Tests", len(st.session_state.test_results))
        
        with col2:
            successful_tests = sum(1 for t in st.session_state.test_results 
                                  if t.get('result', {}).get('success') or 
                                  t.get('generation_result', {}).get('valid'))
            st.metric("Successful", successful_tests)
        
        with col3:
            if st.session_state.test_results:
                latest_time = st.session_state.test_results[-1]['timestamp']
                st.metric("Latest Test", latest_time.split()[1][:5])
        
        st.markdown("---")
        
        # Display results
        for i, result in enumerate(reversed(st.session_state.test_results)):
            idx = len(st.session_state.test_results) - 1 - i
            
            with st.expander(f"Test #{len(st.session_state.test_results) - idx} - {result.get('timestamp', 'N/A')}"):
                # Test info
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Question:** {result.get('question', result.get('sql', 'N/A'))}")
                    st.markdown(f"**Type:** `{result.get('type', 'N/A')}`")
                
                with col2:
                    if result.get('generation_result', {}).get('valid'):
                        st.markdown(status_badge("success", "Valid"), unsafe_allow_html=True)
                    else:
                        st.markdown(status_badge("error", "Invalid"), unsafe_allow_html=True)
                
                # Generated SQL if available
                gen_result = result.get('generation_result', {})
                if gen_result:
                    st.markdown("#### Generated SQL")
                    generated_sql = gen_result.get("sql", "N/A")
                    st.code(generated_sql, language="sql")
                
                # Execution results if available
                exec_result = result.get('execution_result', {})
                if exec_result and exec_result.get('success'):
                    st.markdown("#### Execution Results")
                    if exec_result.get('query_type') == 'SELECT':
                        rows = exec_result.get('rows', [])
                        st.metric("Rows Returned", len(rows))
                    else:
                        st.metric("Affected Rows", exec_result.get('affected_rows', 0))

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6c757d; padding: 1rem;'>"
    "SQLWhisper Text2SQL Testing UI"
    "</div>",
    unsafe_allow_html=True
)