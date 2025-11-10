import streamlit as st
import sqlite3
import os
import pandas as pd

st.set_page_config(page_title="Database Uploader", layout="wide")
st.title("Database Uploader & SQL Tester")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

ACCESS_KEY = "SDAIA2025"
key_input = st.text_input("Enter access key:", type="password")

if key_input == ACCESS_KEY:
    st.success("Access granted")

    uploaded = st.file_uploader("Upload SQLite database (.db / .sqlite)", type=["db", "sqlite"])
    if uploaded:
        save_path = os.path.join(DATA_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"File saved to: {save_path}")

    db_files = [f for f in os.listdir(DATA_DIR) if f.endswith((".db", ".sqlite"))]
    if db_files:
        selected_db = st.selectbox("Select a database:", db_files)
        db_path = os.path.join(DATA_DIR, selected_db)

        query = st.text_area("SQL query:", "SELECT name FROM sqlite_master WHERE type='table';", height=100)
        if st.button("Run Query"):
            try:
                conn = sqlite3.connect(db_path)
                df = pd.read_sql_query(query, conn)
                st.dataframe(df, use_container_width=True)
                conn.close()
            except Exception as e:
                st.error(f"SQL Error: {e}")
    else:
        st.info("No databases found in /data.")
else:
    st.warning("Enter a valid access key to enable uploader.")



