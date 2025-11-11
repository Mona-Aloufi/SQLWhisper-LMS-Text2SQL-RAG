import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid
from components.translation import t
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
from components.layout import apply_layout
# ============================================================
#  PATHS & CONSTANTS
# ============================================================
HISTORY_FILE = "streamlit_app/history.csv"

# ============================================================
#  PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | History", page_icon="🕓", layout="wide")

# ============================================================
#  GLOBAL LAYOUT (theme, header, sidebar, footer, language)
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # use global language selection
# ============================================================
#  HISTORY CONTENT
# ============================================================
st.markdown(f'<div class="section-title">{t("history_tab", lang)}</div>', unsafe_allow_html=True)

if os.path.exists(HISTORY_FILE):
    df = pd.read_csv(HISTORY_FILE)

    if not df.empty:
        # Translate content if Arabic selected
        if lang == "ar":
            df["success"] = df["success"].replace(t("success_labels", lang))
            df["valid_sql"] = df["valid_sql"].replace(t("valid_sql_labels", lang))
            df["confidence_label"] = df["confidence_label"].replace(t("confidence_labels", lang))
            df.rename(columns=t("history_columns", lang), inplace=True)
        else:
            df.rename(columns=t("history_columns", lang), inplace=True)

        AgGrid(df.sort_values(by=df.columns[0], ascending=False), height=500, theme="alpine")
    else:
        st.info(t("no_history_yet", lang))
else:
    st.info(t("no_query_history", lang))

render_footer()
