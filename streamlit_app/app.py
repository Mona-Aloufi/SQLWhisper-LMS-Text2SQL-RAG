# streamlit_app/app.py
import streamlit as st
import pandas as pd
import sqlite3
import datetime
import re
from st_aggrid import AgGrid, GridOptionsBuilder
from PIL import Image
import os


# ----------------------------
# Page configuration
st.set_page_config(page_title="SQLWhisper 💜", page_icon="💜", layout="centered")

# ----------------------------
# Subtle background
st.markdown(
    """
    <style>
    body {
        background-image: repeating-linear-gradient(
            45deg,
            #f8f8f8,
            #f8f8f8 10px,
            #ffffff 10px,
            #ffffff 20px
        );
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Title + optional logo
try:
    logo = Image.open("streamlit_app/logo.png")
    st.image(logo, width=100)
except Exception:
    pass

st.markdown(
    "<h1 style='text-align: center; color: #6a0dad;'>SQLWhisper 💜</h1>"
    "<h4 style='text-align: center; color: #5e5e5e;'>From Questions To Queries - instantly</h4>",
    unsafe_allow_html=True,
)

# ----------------------------
# Database config (use forward slashes so paths work on Windows too)
DB_FILE = "streamlit_app/my_database.sqlite"
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# ----------------------------
# History file
HISTORY_FILE = "streamlit_app/history.csv"

def log_question(question, sql_query, success, error_message=None):
    log_file = "query_log.csv"
    row = {
        "question": question,
        "sql_query": sql_query,
        "success": success,
        "error_message": error_message
    }

    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        # if columns mismatch, reset
        expected_cols = ["question", "sql_query", "success", "error_message"]
        if list(df.columns) != expected_cols:
            df = pd.DataFrame(columns=expected_cols)
    else:
        df = pd.DataFrame(columns=["question", "sql_query", "success", "error_message"])

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(log_file, index=False)


# ----------------------------
# SQL generation placeholder (replace with model call later)
def generate_sql(question):
    """Generate SQL from a natural language question (placeholder)."""
    demo_map = {
        "Show all students who scored above 90": "SELECT * FROM students WHERE score > 90;",
        "List courses taught by Professor": "SELECT * FROM courses WHERE professors = 'X';",
        "Get students enrolled in course Y": "SELECT * FROM enrollments WHERE courses = 'Y';",
    }
    return demo_map.get(question, f"SELECT * FROM students WHERE name LIKE '%{question}%'")

# ----------------------------
# Helper: find table names used in a simple SELECT query
def extract_tables_from_sql(sql):
    """
    Naive extraction of table names from SQL using regex for 'FROM <table>' and JOINs.
    Works for simple queries — good enough for validation and friendly error messages.
    """
    sql_clean = sql.lower()
    tables = re.findall(r'from\s+([`"]?)(\w+)\1', sql_clean)
    joins = re.findall(r'join\s+([`"]?)(\w+)\1', sql_clean)
    table_names = [t[1] for t in tables] + [j[1] for j in joins]
    return list(dict.fromkeys(table_names))  # unique order-preserving

def table_exists(table_name):
    """Check if a table exists in SQLite DB."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    return cur.fetchone() is not None

# ----------------------------
# Tabs
tab1, tab2, tab3 = st.tabs(["Ask", "History", "About"])

# Use session state to keep generated SQL between interactions
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False

# ----------------------------
# Tab 1: Ask
with tab1:
    st.markdown("<h2 style='color:#6a0dad'>Ask a Question</h2>", unsafe_allow_html=True)

    # Suggested queries (more professional label)
    suggested_queries = [
        "Show all students who scored above 90",
        "List courses taught by Professor X",
        "Get students enrolled in course Y",
    ]
    st.write("### Suggested Queries")
    cols = st.columns(len(suggested_queries))
    for i, q in enumerate(suggested_queries):
        if cols[i].button(q):
            # generate SQL and store it
            st.session_state.last_question = q
            st.session_state.generated_sql = generate_sql(q)
            st.session_state.last_result = None

    st.write("---")
    # User input
    user_question = st.text_input("Or type your own question here:", value=st.session_state.last_question or "")
    run_now = st.checkbox("Auto-run after SQL generation", value=st.session_state.auto_run)
    st.session_state.auto_run = run_now

    # Button to generate SQL using (future) model or placeholder
    if st.button("Generate SQL"):
        if not user_question.strip():
            st.warning("Please enter a question first.")
        else:
            st.session_state.last_question = user_question
            # Replace this with model call later
            generated = generate_sql(user_question)
            st.session_state.generated_sql = generated
            st.session_state.last_result = None
            st.success("SQL generated (preview below).")
            # If auto-run is enabled, execute immediately
            if st.session_state.auto_run:
                # fall through to execute block below by setting a flag
                st.session_state._run_after_gen = True
            else:
                st.session_state._run_after_gen = False

    # Show SQL preview if available
    if st.session_state.generated_sql:
        st.subheader("SQL Preview")
        st.code(st.session_state.generated_sql, language="sql")

        # Extract tables and validate before running
        tables = extract_tables_from_sql(st.session_state.generated_sql)
        if tables:
            missing = [t for t in tables if not table_exists(t)]
            if missing:
                st.warning(f"These table(s) do not exist in the database: {missing}. Check table names or choose a different query.")
        else:
            st.info("No table detected by the simple parser — query might be more complex. You can still try to run it.")

        # Execute button
        if st.button("▶ Run SQL"):
            try:
                cur.execute(st.session_state.generated_sql)
                rows = cur.fetchall()
                if rows:
                    df = pd.DataFrame(rows, columns=[d[0] for d in cur.description])
                    st.success("Query executed successfully — results below:")
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(filterable=True, sortable=True, resizable=True)
                    AgGrid(df, gridOptions=gb.build(), height=300, fit_columns_on_grid_load=True)
                    st.session_state.last_result = df
                    log_question(st.session_state.last_question, st.session_state.generated_sql, True, df)
                else:
                    st.info("Query executed but returned no rows.")
                    st.session_state.last_result = pd.DataFrame()
                    log_question(st.session_state.last_question, st.session_state.generated_sql, True, [])
            except sqlite3.OperationalError as op_err:
                # SQL syntax or execution error
                st.error(f"SQL execution error: {op_err}")
                st.info("Suggestions: check table and column names, verify SQL syntax, or adjust the query.")
                log_question(st.session_state.last_question, st.session_state.generated_sql, False, str(op_err))
            except Exception as e:
                st.error(f"Unexpected error while executing SQL: {e}")
                log_question(st.session_state.last_question, st.session_state.generated_sql, False, str(e))

        # Auto-run if requested after generation
        if st.session_state.get("_run_after_gen", False):
            st.session_state._run_after_gen = False
            try:
                cur.execute(st.session_state.generated_sql)
                rows = cur.fetchall()
                if rows:
                    df = pd.DataFrame(rows, columns=[d[0] for d in cur.description])
                    st.success("Auto-run executed — results below:")
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(filterable=True, sortable=True, resizable=True)
                    AgGrid(df, gridOptions=gb.build(), height=300, fit_columns_on_grid_load=True)
                    st.session_state.last_result = df
                    log_question(st.session_state.last_question, st.session_state.generated_sql, True, df)
                else:
                    st.info("Auto-run executed but returned no rows.")
                    st.session_state.last_result = pd.DataFrame()
                    log_question(st.session_state.last_question, st.session_state.generated_sql, True, [])
            except Exception as e:
                st.error(f"Auto-run error: {e}")
                log_question(st.session_state.last_question, st.session_state.generated_sql, False, str(e))

    # If there is a last result cached, show quick summary and download
    if st.session_state.last_result is not None:
        st.write("---")
        st.subheader("Last Result (cached)")
        if isinstance(st.session_state.last_result, pd.DataFrame) and not st.session_state.last_result.empty:
            gb2 = GridOptionsBuilder.from_dataframe(st.session_state.last_result)
            gb2.configure_default_column(filterable=True, sortable=True, resizable=True)
            AgGrid(st.session_state.last_result, gridOptions=gb2.build(), height=250)
            csv = st.session_state.last_result.to_csv(index=False).encode("utf-8")
            st.download_button("Download last result as CSV", csv, file_name="last_query_result.csv", mime="text/csv")
        elif isinstance(st.session_state.last_result, pd.DataFrame) and st.session_state.last_result.empty:
            st.info("Last query returned no rows.")
        else:
            st.info("No cached result to show.")

# ----------------------------
# Tab 2: History
with tab2:
    st.markdown("<h2 style='color:#5e5e5e'>🕒 History of Questions</h2>", unsafe_allow_html=True)
    try:
        df_hist = pd.read_csv(HISTORY_FILE)
        gb = GridOptionsBuilder.from_dataframe(df_hist)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        AgGrid(df_hist, gridOptions=gb.build(), height=350, fit_columns_on_grid_load=True)
        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download History as CSV", csv, file_name="sql_history.csv", mime="text/csv")
    except Exception:
        st.info("No history yet. Once you generate or run queries, history will appear here.")

# ----------------------------
# Tab 3: About
with tab3:
    st.markdown("<h2 style='color:#8a2be2'>ℹ️ About SQLWhisper</h2>", unsafe_allow_html=True)
    st.write(
        """
        SQLWhisper is a Text2SQL assistant demo.

        Workflow now:
        1) Generate SQL (preview) from the question (placeholder or model).
        2) Review SQL preview and optionally run it against the SQLite DB.
        3) Results are shown interactively and saved to history.

        When you connect a model later:
        - Replace `generate_sql()` with model inference.
        - The same flow will work: model generates SQL -> preview -> run.
        """
    )
