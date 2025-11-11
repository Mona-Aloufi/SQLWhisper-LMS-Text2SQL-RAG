import os
import streamlit as st

theme_path = os.path.join(os.path.dirname(__file__), "..", "style", "theme.css")


def render_footer():
        html = """
        <style>
          .footer { padding:16px; text-align:center; color:#6A0DAD; }
          .footer .logo { font-weight:700; font-size:1.05rem; }
          .footer .nav-links { margin-top:8px; }
          .footer .nav-links a { margin:0 8px; text-decoration:none; color:#555555; transition: color 0.12s ease-in-out; }
          .footer .social-icons { margin-top:8px; }
          .footer .social-icons a { margin:0 6px; color:#555555; text-decoration:none; transition: color 0.12s ease-in-out; }
          .footer a:hover { color:#000000 !important; }
          .footer .copyright { margin-top:8px; font-size:0.9rem; }
        </style>
        <div class="footer">
            <div class="copyright">
                © 2025 Made with 💜 by <span style='color:#8A2BE2;'>SQLWhisper Team</span>
            </div>
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)
