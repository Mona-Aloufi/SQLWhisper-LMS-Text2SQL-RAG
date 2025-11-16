import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from components.translation import t
from components.layout import apply_layout

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | Model Dashboard", layout="wide")

# ============================================================
# GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
# PAGE TITLE
# ============================================================
st.markdown(f'<div class="section-title">{t("model_dashboard_title", lang)}</div>', unsafe_allow_html=True)
st.caption(t("model_dashboard_subtitle", lang))

HISTORY_FILE = "streamlit_app/history.csv"

if not os.path.exists(HISTORY_FILE):
    st.warning(t("no_history_data", lang))
    st.stop()

try:
    df_hist = pd.read_csv(HISTORY_FILE)

    if df_hist.empty:
        st.info(t("no_history_data", lang))
        st.stop()

    # ============================================================
    # SAFE COLUMN CREATION (avoid KeyErrors)
    # ============================================================
    for col in ["success", "confidence", "timestamp"]:
        if col not in df_hist.columns:
            df_hist[col] = None

    # Convert success to numeric safely
    df_hist["success"] = df_hist["success"].apply(lambda x: 1 if str(x).strip().lower() == "true" else 0)

    # Convert confidence to numeric safely
    df_hist["confidence"] = pd.to_numeric(df_hist["confidence"], errors="coerce")

    # ============================================================
    # METRICS
    # ============================================================
    total_queries = len(df_hist)
    success_rate = (df_hist["success"].mean() * 100) if total_queries > 0 else 0

    valid_conf = df_hist["confidence"].dropna()
    avg_conf = valid_conf.mean() if not valid_conf.empty else None

    c1, c2, c3 = st.columns(3)
    c1.metric(t("total_queries_label", lang), total_queries)
    c2.metric(t("success_rate", lang), f"{success_rate:.1f}%")
    c3.metric(
        t("avg_confidence", lang),
        f"{avg_conf:.1f}%" if avg_conf is not None else "N/A"
    )

    # ============================================================
    # TIMESTAMP HANDLING
    # ============================================================
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"], errors="coerce")
    df_hist = df_hist.sort_values("timestamp")

    if df_hist["timestamp"].notna().sum() < 2:
        st.info(t("no_query_yet_run", lang))
        render_footer()
        st.stop()

    # ============================================================
    # SUCCESS TREND
    # ============================================================
    fig_q = px.line(
        df_hist,
        x="timestamp",
        y="success",
        markers=True,
        title=t("query_trend", lang),
        template="plotly_white"
    )
    fig_q.update_yaxes(title=t("execution_success_label", lang))
    st.plotly_chart(fig_q, use_container_width=True)

    # ============================================================
    # CONFIDENCE TREND
    # ============================================================
    if "confidence" in df_hist.columns and df_hist["confidence"].notna().any():
        fig_conf = px.line(
            df_hist,
            x="timestamp",
            y="confidence",
            markers=True,
            line_shape="spline",
            title=t("confidence_trend", lang),
            template="plotly_white"
        )
        fig_conf.update_yaxes(range=[0, 100])
        st.plotly_chart(fig_conf, use_container_width=True)
    else:
        st.info(t("confidence_unavailable", lang))

except Exception as e:
    st.error(f"{t('error_loading_dashboard', lang)}: {e}")

render_footer()
