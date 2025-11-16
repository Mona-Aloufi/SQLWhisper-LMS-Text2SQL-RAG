import streamlit as st
import pandas as pd
import sqlite3
from components.translation import t
from components.layout import apply_layout
from components.footer import render_footer

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="SQLWhisper | Feedback Review",
    layout="wide"
)

# ============================================================
# GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
# PAGE TITLE
# ============================================================
st.markdown(
    f'<div class="section-title">{t("user_feedback_review", lang)}</div>',
    unsafe_allow_html=True
)

# ============================================================
# DB FILE
# ============================================================
DB_PATH = "data/my_database.sqlite"

# ============================================================
# SAFE TABLE CREATION (prevents your error)
# ============================================================
def init_feedback_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sql_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                generated_sql TEXT,
                verdict TEXT,
                comment TEXT,
                user_correction TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to initialize feedback table: {e}")

# Run initialization
init_feedback_table()

# ============================================================
# LOAD FEEDBACK DATA
# ============================================================
try:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM sql_feedback ORDER BY created_at DESC", conn)
    conn.close()

    if df.empty:
        st.info(t("no_feedback", lang))

    else:
        # Ensure all expected columns exist
        expected_cols = [
            "id", "question", "generated_sql", "verdict",
            "comment", "user_correction", "created_at"
        ]

        for col in expected_cols:
            if col not in df.columns:
                df[col] = None

        # Translate verdict labels
        if "verdict" in df.columns:
            df["verdict"] = df["verdict"].replace(t("verdict_labels", lang))

        # Rename columns safely
        col_map = t("feedback_columns", lang)
        rename_map = {c: col_map[c] for c in df.columns if c in col_map}
        df.rename(columns=rename_map, inplace=True)

        # Display
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"{t('error_loading_feedback', lang)}: {e}")

# ============================================================
# FOOTER
# ============================================================
render_footer()
