import streamlit as st
import sqlite3
import tempfile
import os
import json

st.set_page_config(page_title="Database Fetcher", layout="wide")
st.title("Database Fetcher (Upload schema.json or DB file)")

def extract_sqlite_schema(path):

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    schema = {"tables": []}

    for t in tables:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = []
        pks = []
        for cid, name, ctype, notnull, dflt, pk in cur.fetchall():
            cols.append({
                "name": name,
                "type": ctype,
                "nullable": notnull == 0,
                "default": dflt
            })
            if pk:
                pks.append(name)

        cur.execute(f"PRAGMA foreign_key_list('{t}')")
        fks = [
            {
                "column": fk[3],
                "referred_table": fk[2],
                "referred_columns": [fk[4]]
            }
            for fk in cur.fetchall()
        ]

        schema["tables"].append({
            "name": t,
            "columns": cols,
            "primary_key": pks,
            "foreign_keys": fks
        })

    conn.close()
    return schema


tab1, tab2 = st.tabs(["Upload DB", "Upload Schema JSON"])

with tab1:
    db_file = st.file_uploader("Upload SQLite file (.db or .sqlite)", type=["db", "sqlite"])
    if db_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
            tmp.write(db_file.read())
            tmp_path = tmp.name

        schema = extract_schema_from_sqlite(tmp_path)
        os.remove(tmp_path)
        st.success("Schema extracted successfully")
        st.json(schema)
        st.download_button(
            "Download schema.json",
            json.dumps(schema, indent=2).encode("utf-8"),
            "schema.json",
            "application/json"
        )

with tab2:
    schema_file = st.file_uploader("Upload schema.json", type=["json"])
    if schema_file:
        schema = json.load(schema_file)
        st.success("Schema loaded successfully")
        st.json(schema)
