import streamlit as st
from PIL import Image
import os
from pathlib import Path
from components.translation import t
#Theme.css
theme_path = os.path.join(os.path.dirname(__file__), "..", "style", "theme.css")
if os.path.exists(theme_path):
    with open(theme_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("theme.css not found in streamlit_app/style/")

#header
def render_header(lang):
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    
    header_col1, header_col2 = st.columns([0.2, 0.8])
    with header_col1:
        try:
            logo = Image.open(logo_path)
            st.image(logo, width=80)
        except:
            st.write("LOGO")
    with header_col2:
        st.markdown(f'<h1 class="app-title">{t("app_title", lang)}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="app-subtitle">{t("app_subtitle", lang)}</p>', unsafe_allow_html=True)
