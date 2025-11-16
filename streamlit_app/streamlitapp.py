import streamlit as st
import os
from components.translation import t
from components.layout import apply_layout

# ============================================================
#  PAGE CONFIG
# ============================================================
st.set_page_config(page_title="SQLWhisper - Home", layout="wide")

# ============================================================
#  GLOBAL LAYOUT
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # language from session

# ============================================================
#  PAGE STYLE
# ============================================================
st.markdown("""
<style>
.main-container {
    padding: 2.5rem 3rem;
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 18px;
    box-shadow: 0 6px 20px rgba(106, 13, 173, 0.08);
    margin-top: 2rem;
}
.welcome-box {
    background: #fde7f3;
    border-left: 5px solid #d63384;
    border-radius: 12px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 10px rgba(214, 51, 132, 0.1);
}
.welcome-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #d63384;
    margin-bottom: 0.8rem;
    line-height: 1.2;
}
.welcome-sub {
    font-size: 1.1rem;
    color: #6a1b9a;
    margin-bottom: 0;
}
.feature-box {
    padding: 0.8rem 1.2rem;
    border-radius: 12px;
    background: #f3e5f5;
    color: #4A148C;
    font-weight: 600;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 8px rgba(106, 13, 173, 0.05);
    font-size: 0.9rem;
}
.feature-box strong { color: #6A1B9A; }
section.main > div:first-child { background: transparent !important; box-shadow: none !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  MAIN CONTENT
# ============================================================
st.markdown(f"""
<div class="welcome-box" style="margin-top:0;">
    <div class="welcome-title">{t("welcome_title", lang)}</div>
    <div class="welcome-sub">{t("welcome_sub", lang)}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="feature-box">{t("feature_secure", lang)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="feature-box">{t("feature_ai", lang)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="feature-box">{t("feature_insights", lang)}</div>', unsafe_allow_html=True)

# ============================================================
#  FOOTER
# ============================================================
render_footer()
