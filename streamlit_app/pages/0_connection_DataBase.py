import streamlit as st
import requests
from components.translation import t, text_labels
from components.layout import apply_layout
from components.footer import render_footer
import streamlit as st

# ============================================================
# GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.get("lang", "en")

API_BASE_URL = "http://127.0.0.1:8000"

# ============================================================
# SAFE INITIALIZATION OF SESSION STATE KEYS
# ============================================================
defaults = {
    "db_path": None,
    "db_type": None,
    "db_connected": False,
    "db_credentials": None,
    "current_schema": {},
    "file_id": None
}

for key, val in defaults.items():
    st.session_state.setdefault(key, val)

# ============================================================
# HELPERS
# ============================================================
def tr(key: str) -> str:
    """Safe translation lookup with English fallback."""
    return text_labels.get(lang, text_labels["en"]).get(key, key)

# ============================================================
# PAGE HEADER
# ============================================================
st.header(tr("database_connection_title"))

# ============================================================
# TABS
# ============================================================
tab1, tab2 = st.tabs([
    tr("upload_sqlite_tab"),
    tr("external_db_tab")
])

# ============================================================
# TAB 1 — SQLITE UPLOAD
# ============================================================
with tab1:
    st.markdown("### " + tr("upload_sqlite_title"))

    uploaded_file = st.file_uploader(
        tr("choose_sqlite_file"),
        type=["db", "sqlite", "sqlite3"]
    )

    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file, "application/octet-stream")}

        if st.button(tr("upload_connect_btn"), type="primary", use_container_width=True):

            try:
                with st.spinner(tr("processing")):
                    response = requests.post(f"{API_BASE_URL}/upload-db", files=files)

                if response.status_code == 200:
                    res = response.json()

                    if "error" in res:
                        st.error(f"{tr('upload_failed')}: {res['error']}")
                    else:
                        st.success(tr("db_connected_success"))

                        # Save session state for teammate’s UI logic
                        st.session_state.db_type = "sqlite"
                        st.session_state.file_id = res.get("file_id")  # IMPORTANT
                        st.session_state.db_path = res.get("db_path") 
                        st.session_state.db_connected = True
                        st.session_state.current_schema = res.get("schema", {})

                        # Redirect to Data Dashboard
                        st.info(tr("redirecting_dashboard"))
                        st.switch_page("pages/4_Data_Dashboard.py")

                else:
                    st.error(f"Upload failed: {response.status_code}")

            except Exception as e:
                st.error(f"Upload request failed: {e}")

# ============================================================
# TAB 2 — EXTERNAL DB CONNECTION
# ============================================================
with tab2:
    st.markdown("### " + tr("connect_external_title"))

    with st.form("external_db_form"):
        col1, col2 = st.columns(2)

        with col1:
            db_type = st.selectbox(tr("db_type_label"), ["postgresql", "mysql"])
            host = st.text_input(tr("host_label"), "localhost")
            database = st.text_input(tr("dbname_label"))

        with col2:
            port = st.number_input(
                tr("port_label"),
                value=5432 if db_type == "postgresql" else 3306
            )
            user = st.text_input(tr("username_label"))
            password = st.text_input(tr("password_label"), type="password")

        submitted = st.form_submit_button(
            tr("connect_btn"),
            type="primary",
            use_container_width=True
        )

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
                with st.spinner(tr("connecting")):
                    response = requests.post(f"{API_BASE_URL}/connect-db", json=payload)

                if response.status_code == 200:
                    res = response.json()

                    if "error" in res:
                        st.error(f"{tr('connection_failed')}: {res['error']}")
                    else:
                        st.success(tr("db_connected_success"))

                        # Save session state
                        st.session_state.db_type = db_type
                        st.session_state.db_credentials = payload
                        st.session_state.db_connected = True
                        st.session_state.current_schema = res.get("schema", {})
                        st.session_state.file_id = res.get("file_id")
                        st.session_state.db_path = res.get("db_path")

                        # Redirect to Data Dashboard
                        st.info(tr("redirecting_dashboard"))
                        st.switch_page("pages/4_Data_Dashboard.py")

                else:
                    st.error(f"Connection failed: {response.status_code}")

            except Exception as e:
                st.error(f"Connection request failed: {e}")

# ============================================================
# FOOTER
# ============================================================
render_footer()
