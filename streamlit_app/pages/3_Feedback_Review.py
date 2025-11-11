import streamlit as st
import pandas as pd
import sqlite3
from components.translation import t
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer
from components.layout import apply_layout
# ============================================================
#  PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | Feedback", page_icon="💬", layout="wide")

# ============================================================
#  GLOBAL LAYOUT (theme, header, sidebar, footer, language)
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # use global language selection
# ============================================================
#  FEEDBACK CONTENT
# ============================================================
st.markdown(f'<div class="section-title">{t("user_feedback_review", lang)}</div>', unsafe_allow_html=True)

try:
    conn = sqlite3.connect("data/my_database.sqlite")
    df = pd.read_sql("SELECT * FROM sql_feedback ORDER BY created_at DESC", conn)
    conn.close()

    if not df.empty:
        df["verdict"] = df["verdict"].replace(t("verdict_labels", lang))
        df.rename(columns=t("feedback_columns", lang), inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info(t("no_feedback", lang))
except Exception as e:
    st.error(f"{t('error_loading_feedback', lang)}: {e}")

render_footer()
