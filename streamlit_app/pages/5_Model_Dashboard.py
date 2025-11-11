import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from components.translation import t
from components.layout import apply_layout

# ============================================================
#  PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | Model Dashboard", layout="wide")

# ============================================================
#  GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang

# ============================================================
#  HEADER
# ============================================================
st.markdown(f'<div class="section-title">{t("model_dashboard_title", lang)}</div>', unsafe_allow_html=True)
st.caption(t("model_dashboard_subtitle", lang))

HISTORY_FILE = "streamlit_app/history.csv"

if not os.path.exists(HISTORY_FILE):
    st.warning(t("no_history_data", lang))
    st.stop()

try:
    df_hist = pd.read_csv(HISTORY_FILE)

    # ---------- Core Metrics ----------
    total_queries = len(df_hist)
    success_rate = (df_hist["success"].sum() / total_queries * 100) if total_queries else 0
    avg_conf = (
        np.mean([r for r in df_hist.get("confidence", []) if pd.notnull(r)])
        if "confidence" in df_hist.columns
        else None
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(t("total_queries_label", lang), total_queries)
    c2.metric(t("success_rate", lang), f"{success_rate:.1f}%")
    c3.metric(t("avg_confidence", lang), f"{avg_conf:.1f}%" if avg_conf else "N/A")

    # ---------- Trends ----------
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"], errors="coerce")
    df_hist = df_hist.sort_values("timestamp")

    if len(df_hist) > 1:
        # Success trend
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

        # Confidence trend
        if "confidence" in df_hist.columns and df_hist["confidence"].notna().any():
            fig_conf = px.line(
                df_hist,
                x="timestamp",
                y="confidence",
                title=t("confidence_trend", lang),
                template="plotly_white",
                markers=True,
                line_shape="spline"
            )
            fig_conf.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.info(t("confidence_unavailable", lang))
    else:
        st.info(t("no_query_yet_run", lang))

except Exception as e:
    st.error(f"{t('error_loading_dashboard', lang)}: {e}")

render_footer()
