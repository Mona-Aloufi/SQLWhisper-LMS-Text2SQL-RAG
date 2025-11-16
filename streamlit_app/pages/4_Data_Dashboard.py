import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
from components.translation import t
from components.layout import apply_layout
from graphviz import Digraph

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | Data Dashboard", layout="wide")

# ============================================================
# GLOBAL LAYOUT & LANGUAGE
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
# LOAD DATABASE (USER OR DEFAULT)
# ============================================================
# Support BOTH upload systems: Home Page & Connection Page
db_path = (
    st.session_state.get("db_path") or
    st.session_state.get("user_database")
)

if db_path:
    st.session_state.db_path = db_path  # normalize for later pages
else:
    st.warning(t("no_database_loaded", lang))
    st.stop()


if not db_path:
    st.warning(t("no_database_loaded", lang))
    st.stop()


@st.cache_data(show_spinner=False)
def load_tables(db_path):
    """Load table metadata and schema."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]

        stats, schema = [], []
        for tname in tables:
            # Count rows
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{tname}"')
                n = cur.fetchone()[0]
            except Exception:
                n = 0

            # RAW column names (fixed)
            stats.append({
                "table_name": tname,
                "rows_count": n
            })

            # Schema extraction
            try:
                cur.execute(f'PRAGMA table_info("{tname}")')
                for col in cur.fetchall():
                    schema.append({
                        "table_name": tname,
                        "column": col[1],
                        "type": col[2]
                    })
            except Exception as e:
                st.warning(f"Could not read schema for {tname}: {e}")

    return pd.DataFrame(stats), pd.DataFrame(schema), tables


def extract_relationships(db_path):
    """Parse foreign key relationships between tables."""
    relations = []
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            
            for tname in tables:
                cur.execute(f'PRAGMA foreign_key_list("{tname}")')
                fks = cur.fetchall()
                for fk in fks:
                    relations.append({
                        "from_table": tname,
                        "from_column": fk[3],
                        "to_table": fk[2],
                        "to_column": fk[4]
                    })
    except Exception as e:
        st.warning(f"Could not extract relationships: {e}")
    return relations


df_db_stats, df_schema, tables = load_tables(db_path)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"<h1 class='section-title'>{t('data_dashboard_title', lang)}</h1>", unsafe_allow_html=True)
st.caption(t("data_dashboard_subtitle", lang))

# ============================================================
# FILTER SECTION
# ============================================================
st.markdown("<h3 class='section-subtitle'>" + t("filter_section", lang) + "</h3>", unsafe_allow_html=True)

col1, col2 = st.columns([1.2, 2.5])

with col1:
    selection_mode = st.radio(
        t("table_selection_mode", lang),
        [t("single_table", lang), t("multiple_tables", lang)],
        horizontal=True
    )

with col2:
    if selection_mode == t("single_table", lang):
        selected_tables = [st.selectbox(
            t("choose_table", lang),
            ["All Tables"] + tables,
            index=0
        )]
    else:
        selected_tables = st.multiselect(
            t("choose_multiple_tables", lang),
            tables,
            default=tables
        )

if "All Tables" in selected_tables:
    selected_tables = tables

# ============================================================
# KPI SECTION
# ============================================================
filtered_stats = df_db_stats[df_db_stats["table_name"].isin(selected_tables)]

col1, col2, col3 = st.columns(3)
col1.metric(t("total_tables", lang), len(tables))
col2.metric(t("selected_tables", lang), len(selected_tables))
col3.metric(t("total_rows", lang), filtered_stats["rows_count"].sum())

# ============================================================
# MAIN TABS
# ============================================================
tab_chart, tab_schema, tab_preview, tab_erd = st.tabs([
    t("rows_chart_title", lang),
    t("schema_explorer", lang),
    t("data_preview", lang),
    t("erd_diagram", lang)
])

# ------------------- TAB 1: ROW COUNT CHART -------------------
with tab_chart:
    if not filtered_stats.empty:
        chart = px.bar(
            filtered_stats,
            x="table_name",
            y="rows_count",
            text="rows_count",
            color="table_name",
            template="plotly_white"
        )
        chart.update_traces(textposition="outside")
        chart.update_layout(showlegend=False)
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info(t("no_table_selected", lang))

# ------------------- TAB 2: SCHEMA -------------------
with tab_schema:
    filtered_schema = df_schema[df_schema["table_name"].isin(selected_tables)]
    st.dataframe(filtered_schema, use_container_width=True, height=500)

# ------------------- TAB 3: DATA PREVIEW -------------------
with tab_preview:
    try:
        with sqlite3.connect(db_path) as conn:
            preview_tabs = st.tabs(selected_tables)
            for i, tname in enumerate(selected_tables):
                with preview_tabs[i]:
                    safe = tname.replace('"', '""')
                    df = pd.read_sql_query(f'SELECT * FROM "{safe}" LIMIT 50', conn)
                    st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading data: {e}")

# ------------------- TAB 4: ERD DIAGRAM -------------------
with tab_erd:
    relationships = extract_relationships(db_path)
    dot = Digraph()

    for tname in tables:
        dot.node(tname)

    for rel in relationships:
        dot.edge(rel["from_table"], rel["to_table"], label=f'{rel["from_column"]} → {rel["to_column"]}')

    if relationships:
        st.graphviz_chart(dot)
    else:
        st.info(t("no_relationships_found", lang))

# ============================================================
# FOOTER
# ============================================================
render_footer()
