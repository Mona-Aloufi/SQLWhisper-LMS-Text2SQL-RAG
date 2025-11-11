import streamlit as st
from components.translation import t
from components.layout import apply_layout

# ============================================================
#  PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="SQLWhisper | About", page_icon="ℹ️", layout="wide")

# ============================================================
#  GLOBAL LAYOUT (theme, header, sidebar, footer, language)
# ============================================================
render_footer = apply_layout()
lang = st.session_state.lang  # use global language selection

# ============================================================
#  ABOUT CONTENT
# ============================================================
st.markdown(f'<div class="section-title">{t("about_sqlwhisper", lang)}</div>', unsafe_allow_html=True)
st.markdown(t("about_rich_html", lang), unsafe_allow_html=True)

# ============================================================
#  FOOTER
# ============================================================
render_footer()
