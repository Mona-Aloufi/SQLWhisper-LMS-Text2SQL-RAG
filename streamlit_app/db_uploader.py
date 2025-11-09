import streamlit as st
import json
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
        with open(f"data/{uploaded.name}", "wb") as f:
            f.write(uploaded.read())
        schema = extract_sqlite_schema(f"data/{uploaded.name}")
        st.success("Schema extracted and saved to data/schema.json.")
        st.json(schema)

