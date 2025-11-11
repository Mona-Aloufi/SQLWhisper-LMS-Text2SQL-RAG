import streamlit as st
from components.translation import t
import os

def render_sidebar(lang, get_database_info):
    """
    Render a clean, bilingual sidebar for SQLWhisper with logo, navigation, and upload.
    """

    # ============================================================
    # 🟣 APP LOGO & NAME
    # ============================================================
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")

    with st.sidebar:
        if os.path.exists(logo_path):
            col1, col2 = st.columns([0.2, 0.8])
            with col1:
                st.image(logo_path, width=40)
            with col2:
                st.markdown(
                    "<h2 style='color:#6A1B9A; font-weight:800; margin:0; padding-top:5px;'>SQLWhisper</h2>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<h2 style='color:#6A1B9A; font-weight:800; text-align:left;'>SQLWhisper</h2>",
                unsafe_allow_html=True,
            )

        st.caption(f"<p style='color:gray; margin-top:-8px;'>{t('app_subtitle', lang)}</p>", unsafe_allow_html=True)
        st.markdown("---")

    # ============================================================
    # 🌐 LANGUAGE TOGGLE
    # ============================================================
    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    current_lang = st.session_state.lang
    header_title = "Language" if current_lang == "en" else "اللغة"
    toggle_label = "Ar" if current_lang == "en" else "En"

    st.sidebar.markdown(
        f"<h3 style='color:#6A1B9A; font-weight:700;'>{header_title}</h3>",
        unsafe_allow_html=True
    )

    toggle_state = st.sidebar.toggle(
        toggle_label,
        value=(current_lang == "ar"),
        key="lang_toggle_sidebar",
    )

    st.session_state.lang = "ar" if toggle_state else "en"
    lang = st.session_state.lang

    if lang == "ar":
        st.markdown("<style>html {direction: rtl; text-align: right;}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>html {direction: ltr; text-align: left;}</style>", unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # ============================================================
    # 📂 NAVIGATION LINKS
    # ============================================================
    st.sidebar.page_link("streamlitapp.py", label=t("app_title", lang))
    st.sidebar.page_link("pages/1_Query.py", label=t("query_tab", lang))
    st.sidebar.page_link("pages/2_History.py", label=t("history_tab", lang))
    st.sidebar.page_link("pages/3_Feedback_Review.py", label=t("feedback_tab", lang))
    st.sidebar.page_link("pages/4_Data_Dashboard.py", label=t("data_dashboard_title", lang))
    st.sidebar.page_link("pages/5_Model_Dashboard.py", label=t("model_dashboard_title", lang))
    st.sidebar.page_link("pages/6_About.py", label=t("about_tab", lang))
    st.sidebar.page_link("pages/7_Chatbot.py", label=t("chatbot_title", lang))
    st.sidebar.markdown("---")

    # # ============================================================
    # # 🧩 DATABASE INFORMATION
    # # ============================================================
    # st.sidebar.markdown(f"### {t('database_info', lang)}")
    # if get_database_info:
    #     try:
    #         db_info = get_database_info()
    #         if db_info:
    #             st.sidebar.success(t("db_connected", lang))
    #             if "tables" in db_info and db_info["tables"]:
    #                 st.sidebar.caption(f"**Tables:** {', '.join(db_info['tables'])}")
    #         else:
    #             st.sidebar.warning(t("db_failed", lang))
    #     except Exception:
    #         st.sidebar.error(t("db_failed", lang))

    # # ============================================================
    # # 🗃️ LOAD SCHEMA / DATA UPLOAD
    # # ============================================================
    # st.sidebar.markdown(f"### {t('load_schema', lang)}")

    # uploaded_db = st.sidebar.file_uploader(
    #     t("upload_prompt", lang),
    #     type=["sqlite", "db", "csv"],
    #     key="sidebar_uploader",
    #     label_visibility="collapsed"
    # )

    # if uploaded_db:
    #     upload_path = os.path.join("data", uploaded_db.name)
    #     os.makedirs("data", exist_ok=True)
    #     with open(upload_path, "wb") as f:
    #         f.write(uploaded_db.getbuffer())

    #     st.session_state["user_database"] = upload_path
    #     st.sidebar.success(f"{uploaded_db.name} {t('uploaded_success', lang)}")

    #     # ✅ Redirect to Data Dashboard
    #     st.switch_page("pages/4_Data_Dashboard.py")
