import streamlit as st
import os
import requests
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

def apply_layout(lang="en"):
    """Apply shared layout, theme, header, sidebar, footer, and language selection."""

    # ============================================================
    # PAGE CONFIG
    # ============================================================
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    st.set_page_config(
        page_title="SQLWhisper",
        page_icon=logo_path,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ============================================================
    # HIDE STREAMLIT DEFAULT MULTI-PAGE SIDEBAR
    # ============================================================
    st.markdown("""
        <style>
        /* Hide Streamlit's built-in page selector in the sidebar */
        [data-testid="stSidebarNav"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # THEME
    # ============================================================
    theme_path = os.path.join(os.path.dirname(__file__), "..", "style", "theme.css")
    if os.path.exists(theme_path):
        with open(theme_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("theme.css not found in streamlit_app/style/")
    # ============================================================
    # HELPER: GET DATABASE INFO
    # ============================================================
    def get_database_info():
        API_BASE_URL = "http://127.0.0.1:8000"
        try:
            res = requests.get(f"{API_BASE_URL}/db-info", timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            return None

    # ============================================================
    # SHARED LAYOUT COMPONENTS
    # ============================================================
    render_header(lang)
    render_sidebar(lang, get_database_info)

    # ============================================================
    # RETURN FOOTER FUNCTION
    # ============================================================
    return render_footer
