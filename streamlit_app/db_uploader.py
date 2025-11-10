import streamlit as st
import json
import sqlite3
import pandas as pd
import tempfile
from db_fetcher import extract_sqlite_schema


st.set_page_config(page_title="Database Uploader", layout="wide")
st.title("Database Uploader")

uploaded = st.file_uploader(
    "Upload SQLite database (.db/.sqlite) or schema.json",
    type=["db", "sqlite", "json"]
)

if uploaded:
    if uploaded.name.endswith(".json"):
        schema = json.load(uploaded)
        with open("data/schema.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        st.success("Schema JSON uploaded successfully.")
        st.json(schema)

    else:
        # Save the uploaded SQLite file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
        temp_file.write(uploaded.getbuffer())
        temp_file.flush()
        temp_file.close()

        # Connect to the database
        conn = sqlite3.connect(temp_file.name)
        st.session_state.conn = conn
        st.success("Connected to database successfully.")

        # Extract and display schema
        schema = extract_sqlite_schema(temp_file.name)
        st.json(schema)

        # Display available tables
        try:
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table';", conn
            )
            st.write("**Available Tables:**", tables)
        except Exception as e:
            st.warning(f"Could not list tables: {e}")

        # SQL query testing section
        query = st.text_area(
            "Enter an SQL query to test",
            "SELECT name FROM sqlite_master;",
            height=120
        )
        if st.button("Run Query"):
            try:
                result = pd.read_sql_query(query, conn)
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")


