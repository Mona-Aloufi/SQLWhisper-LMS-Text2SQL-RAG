# import streamlit as st
# import streamlit_authenticator as stauth

# # --- Generate hashed passwords once ---
# hashed_passwords = stauth.Hasher(['sqlwhisper123', 'guest123']).generate()

# # --- Static configuration ---
# config = {
#     'credentials': {
#         'usernames': {
#             'admin': {
#                 'email': 'admin@sqlwhisper.ai',
#                 'name': 'SQLWhisper',
#                 'password': hashed_passwords[0]
#             },
#             'guest': {
#                 'email': 'guest@sqlwhisper.ai',
#                 'name': 'Guest User',
#                 'password': hashed_passwords[1]
#             }
#         }
#     },
#     'cookie': {
#         'name': 'sqlwhisper_cookie',
#         'key': 'secret_key_sqlwhisper',
#         'expiry_days': 1
#     },
#     'preauthorized': {
#         'emails': ['admin@sqlwhisper.ai']
#     }
# }

# # --- Initialize authenticator ---
# authenticator = stauth.Authenticate(
#     config['credentials'],
#     config['cookie']['name'],
#     config['cookie']['key'],
#     config['cookie']['expiry_days'],
# )

# # --- Login function ---
# def login_page():
#     """Simple login form for SQLWhisper"""
#     st.markdown("<h2 style='color:#6a0dad;text-align:center;'>🔐 SQLWhisper Login</h2>", unsafe_allow_html=True)
#     name, auth_status, username = authenticator.login('Login', 'main')

#     if auth_status is False:
#         st.error('❌ Invalid credentials.')
#     elif auth_status is None:
#         st.warning('Please enter your credentials.')
#     elif auth_status:
#         st.session_state["auth_status"] = True
#         st.session_state["username"] = username
#         st.success(f"✅ Welcome back, {name}!")
#         return True

#     return False
