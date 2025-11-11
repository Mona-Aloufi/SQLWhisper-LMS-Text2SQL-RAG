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
db_path = st.session_state.get("user_database", "data/my_database.sqlite")

if not os.path.exists(db_path):
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
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{tname}"')
                n = cur.fetchone()[0]
            except Exception:
                n = "?"
            stats.append({t("table_name", lang): tname, t("rows_count", lang): n})

            try:
                cur.execute(f'PRAGMA table_info("{tname}")')
                for col in cur.fetchall():
                    schema.append({
                        t("table_name", lang): tname,
                        "Column": col[1],
                        "Type": col[2]
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
# FILTER SECTION (IN MAIN PAGE)
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
            default=tables[:3] if len(tables) >= 3 else tables
        )

# Handle “All Tables”
if "All Tables" in selected_tables:
    selected_tables = tables

st.divider()

# ============================================================
# KPI SECTION
# ============================================================
total_tables = len(tables)
selected_count = len(selected_tables)
filtered_stats = df_db_stats[df_db_stats[t("table_name", lang)].isin(selected_tables)]

col1, col2, col3 = st.columns(3)
col1.metric(t("total_tables", lang), total_tables)
col2.metric(t("selected_tables", lang), selected_count)
col3.metric(
    t("total_rows", lang),
    int(filtered_stats[t("rows_count", lang)].replace("?", 0).astype(int).sum())
)

# ============================================================
# MAIN DASHBOARD TABS
# ============================================================
tab_chart, tab_schema, tab_preview,tab_erd  = st.tabs([
    t("rows_chart_title", lang),
    t("schema_explorer", lang),
    t("data_preview", lang),
    t("erd_diagram",lang),
])

# ---------- TAB 1: CHART ----------
with tab_chart:
    if not filtered_stats.empty:
        chart = px.bar(
            filtered_stats,
            x=t("table_name", lang),
            y=t("rows_count", lang),
            color=t("table_name", lang),
            text=t("rows_count", lang),
            template="plotly_white"
        )
        chart.update_traces(textposition="outside")
        chart.update_layout(
            xaxis_title=t("table_name", lang),
            yaxis_title=t("rows_count", lang),
            showlegend=False,
            margin=dict(t=20, b=40, l=20, r=20)
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info(t("no_table_selected", lang))

# ---------- TAB 2: SCHEMA ----------
with tab_schema:
    with st.expander(t("show_schema_details", lang), expanded=True):
        filtered_schema = df_schema[df_schema[t("table_name", lang)].isin(selected_tables)]
        st.dataframe(filtered_schema, use_container_width=True, height=500)

# ---------- TAB 3: DATA PREVIEW ----------
with tab_preview:
    if selected_tables:
        preview_tabs = st.tabs(selected_tables)
        try:
            with sqlite3.connect(db_path) as conn:
                for i, tname in enumerate(selected_tables):
                    with preview_tabs[i]:
                        try:
                            safe_tname = tname.replace('"', '""')
                            df_data = pd.read_sql_query(f'SELECT * FROM "{safe_tname}" LIMIT 50', conn)
                            if not df_data.empty:
                                st.dataframe(df_data, width='stretch', height=350)

                                st.download_button(
                                    label=f"⬇️ {tname} CSV",
                                    data=df_data.to_csv(index=False),
                                    file_name=f"{tname}_data.csv",
                                    mime="text/csv",
                                    width='stretch'
                                )
                            else:
                                st.info(f"No data to preview or download for {tname}.")
                        except Exception as e:
                            st.warning(f"{t('error_loading_data', lang)}: {e}")
        except Exception as e:
            st.error(f"{t('error_loading_data', lang)}: {e}")
    else:
        st.info(t("no_table_selected", lang))

# ---------- TAB 4: ERD DIAGRAM ----------
with tab_erd:
    st.markdown(f"### Database Relationships Diagram")

    relationships = extract_relationships(db_path)
    dot = Digraph()

    # Create nodes for each table
    for tname in tables:
        dot.node(tname, tname, shape="box", style="filled", color="#E1BEE7", fillcolor="#F3E5F5")

    # Create edges for each foreign key
    for rel in relationships:
        dot.edge(rel["from_table"], rel["to_table"],
                 label=f'{rel["from_column"]} → {rel["to_column"]}',
                 color="#6A1B9A")

    if relationships:
        st.graphviz_chart(dot)
    else:
        st.info("No foreign key relationships detected in this database.")

# ============================================================
# CUSTOM CSS — POLISH & THEME VARIABLES
# ============================================================
st.markdown("""
<style>
:root {
    --purple: #6A1B9A;
    --light-purple: #F3E5F5;
    --font: "Segoe UI", "Roboto", sans-serif;
}
html, body, [class*="css"] {
    font-family: var(--font);
}
.section-title {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--purple);
    margin-bottom: 0.5rem;
}
.section-subtitle {
    font-size: 1.2rem;
    font-weight: 600;
    color: #4A148C;
}
div[data-testid="stMetricValue"] {
    color: var(--purple);
}
[data-testid="stMetricLabel"] {
    color: #666;
}
# #MainMenu, footer, header {visibility: hidden;}
# [data-testid="stSidebar"] {background-color: var(--light-purple);}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
render_footer()
