import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid
from components.translation import t
from components.layout import apply_layout
from components.footer import render_footer

# ============================================================
# PATHS & CONSTANTS
# ============================================================
HISTORY_FILE = "streamlit_app/history.csv"

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | History", layout="wide")

# ============================================================
# GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
# HEADER
# ============================================================
st.markdown(f'<div class="section-title">{t("history_tab", lang)}</div>', unsafe_allow_html=True)

# ============================================================
# LOAD HISTORY
# ============================================================
if os.path.exists(HISTORY_FILE):

    df = pd.read_csv(HISTORY_FILE)

    if df.empty:
        st.info(t("no_history_yet", lang))
        render_footer()
        st.stop()

    # ============================================================
    # ENSURE ALL EXPECTED COLUMNS EXIST
    # ============================================================
    expected_cols = [
        "timestamp", "question", "sql_query", "success", "valid_sql",
        "rows_returned", "error_message", "confidence", "confidence_label"
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # ============================================================
    # OPTIONAL TRANSLATION (when Arabic is selected)
    # ============================================================
    if lang == "ar":

        # Translate boolean/success statuses
        if "success" in df.columns:
            df["success"] = df["success"].replace(t("success_labels", lang))

        if "valid_sql" in df.columns:
            df["valid_sql"] = df["valid_sql"].replace(t("valid_sql_labels", lang))

        if "confidence_label" in df.columns:
            df["confidence_label"] = df["confidence_label"].replace(t("confidence_labels", lang))

        # Rename column headers
        df = df.rename(columns=t("history_columns", lang))

    else:
        df = df.rename(columns=t("history_columns", lang))

    # ============================================================
    # SORT BY TIMESTAMP
    # ============================================================
    if "timestamp" in df.columns:
        df = df.sort_values(by="timestamp", ascending=False)

    # ============================================================
    # DISPLAY TABLE
    # ============================================================
    AgGrid(
        df,
        height=540,
        theme="alpine"
    )

else:
    st.info(t("no_query_history", lang))

# ============================================================
# FOOTER
# ============================================================
render_footer()
