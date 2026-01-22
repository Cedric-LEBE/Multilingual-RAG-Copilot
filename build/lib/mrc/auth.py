from __future__ import annotations

import hmac
import streamlit as st
from passlib.hash import argon2


def require_login() -> None:
    """
    Centered authentication page with a single unified card.

    Secrets required:
      - AUTH_USERNAME
      - AUTH_PASSWORD_HASH (Argon2)
    """

    username = st.secrets.get("AUTH_USERNAME", "")
    pw_hash = st.secrets.get("AUTH_PASSWORD_HASH", "")

    if not username or not pw_hash:
        st.error(
            "Authentication is not configured. "
            "Please set AUTH_USERNAME and AUTH_PASSWORD_HASH in Streamlit secrets."
        )
        st.stop()

    if st.session_state.get("authed", False):
        return

    # Hide Streamlit chrome + global styling
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none; }
        header[data-testid="stHeader"] { visibility: hidden; }
        footer { visibility: hidden; }

        /* Page background */
        .stApp {
            background-color: #f5f6f8;
        }

        /* Card styling (applied to Streamlit bordered container) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border-radius: 18px;
            border: 1px solid rgba(49,51,63,0.12);
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            padding: 2rem 2.2rem;
        }

        /* Ensure inputs fill card width */
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="input"],
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="base-input"],
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="form-control"] {
            width: 100%;
        }

        /* Header styles */
        .login-badge {
            display: inline-block;
            padding: .35rem .75rem;
            border-radius: 999px;
            font-size: .85rem;
            background: #eef0f3;
            border: 1px solid rgba(49,51,63,0.15);
            margin-bottom: 1rem;
        }

        .login-title {
            font-size: 1.9rem;
            font-weight: 800;
            margin: 0;
            line-height: 1.1;
        }

        .login-subtitle {
            margin-top: .5rem;
            color: rgba(49,51,63,0.70);
            font-size: .95rem;
            margin-bottom: 1.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Center the card using columns and fixed max width
    _, center, _ = st.columns([1, 1, 1])
    with center:
        st.markdown(
            "<div style='max-width: 620px; margin: 10vh auto 0 auto;'>",
            unsafe_allow_html=True,
        )

        # ONE single Streamlit container = ONE single card
        with st.container(border=True):
            st.markdown("<div class='login-badge'>🔐 Secure access</div>", unsafe_allow_html=True)
            st.markdown("<p class='login-title'>Log in</p>", unsafe_allow_html=True)
            st.markdown(
                "<div class='login-subtitle'>Enter your credentials to access the app.</div>",
                unsafe_allow_html=True,
            )

            with st.form("login_form", clear_on_submit=False):
                u = st.text_input("Username", key="auth_user")
                p = st.text_input("Password", type="password", key="auth_pass")
                submitted = st.form_submit_button("✅ Log in", use_container_width=True)

            if submitted:
                ok_user = hmac.compare_digest(u.strip(), username)
                ok_pass = argon2.verify(p, pw_hash) if p else False

                if ok_user and ok_pass:
                    st.session_state.authed = True
                    st.toast("Welcome!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()