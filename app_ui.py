# test_streamlit_db.py
import streamlit as st
import requests
import os

# Set your FastAPI backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="SQLWhisper Streamlit Client", layout="wide")
st.title("🔗 SQLWhisper Text2SQL Frontend")

# -----------------------------
# 1️⃣ Upload SQLite Database
# -----------------------------
st.header("SQLite Database Upload")
uploaded_file = st.file_uploader("Upload SQLite file (.db, .sqlite, .sqlite3)", type=["db", "sqlite", "sqlite3"])

if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file, "application/octet-stream")}
    try:
        response = requests.post(f"{API_URL}/upload-db", files=files)
        if response.status_code == 200:
            res = response.json()
            if "error" in res:
                st.error(f"Upload failed: {res['error']}")
            else:
                st.success("✅ Database uploaded successfully")
                st.json(res["schema"])
        else:
            st.error(f"Upload failed: {response.status_code}")
    except Exception as e:
        st.error(f"Upload request failed: {e}")

# -----------------------------
# 2️⃣ External Database Connection
# -----------------------------
st.header("External Database Connection")
with st.form("external_db_form"):
    db_type = st.selectbox("DB Type", ["postgresql", "mysql"])
    host = st.text_input("Host", "localhost")
    port = st.number_input("Port", 5432)
    database = st.text_input("Database Name")
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Connect")

    if submitted:
        payload = {
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        try:
            response = requests.post(f"{API_URL}/connect-db", json=payload)
            if response.status_code == 200:
                res = response.json()
                if "error" in res:
                    st.error(f"Connection failed: {res['error']}")
                else:
                    st.success(f"✅ Connected to {db_type}")
                    st.json(res["schema"])
            else:
                st.error(f"Connection failed: {response.status_code}")
        except Exception as e:
            st.error(f"Connection request failed: {e}")

# -----------------------------
# 3️⃣ Ask a Question (Generate SQL)
# -----------------------------
st.header("Ask a Question / Generate SQL")
question = st.text_input("Your Question")

if st.button("Generate SQL"):
    if not question.strip():
        st.warning("Please enter a question first")
    else:
        payload = {"question": question}
        try:
            response = requests.post(f"{API_URL}/generate-sql", json=payload)
            if response.status_code == 200:
                res = response.json()
                if "error" in res:
                    st.error(f"SQL generation failed: {res['error']}")
                else:
                    st.success("✅ SQL Generated")
                    st.code(res.get("sql", ""))
                    st.json({
                        "valid": res.get("valid"),
                        "confidence": res.get("confidence"),
                        "confidence_label": res.get("confidence_label")
                    })
            else:
                st.error(f"Request failed: {response.status_code}")
        except Exception as e:
            st.error(f"Request error: {e}")

# -----------------------------
# 4️⃣ Execute SQL
# -----------------------------
st.header("Execute Custom SQL")
sql_input = st.text_area("Enter SQL Query")

if st.button("Execute SQL"):
    if not sql_input.strip():
        st.warning("Please enter a SQL query first")
    else:
        payload = {"sql": sql_input}
        try:
            response = requests.post(f"{API_URL}/execute-sql", json=payload)
            if response.status_code == 200:
                res = response.json()
                if "error" in res:
                    st.error(f"Execution failed: {res['error']}")
                else:
                    st.success("✅ Query executed")
                    st.write(res)
            else:
                st.error(f"Request failed: {response.status_code}")
        except Exception as e:
            st.error(f"Request error: {e}")
