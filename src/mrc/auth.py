from __future__ import annotations

import hmac

import streamlit as st
from passlib.hash import argon2

def require_login() -> None:
    """Very simple demo authentication.

    Uses secrets:
      AUTH_USERNAME
      AUTH_PASSWORD_HASH  (bcrypt)

    Suitable for a class/demo app (not enterprise SSO).
    """
    username = st.secrets.get("AUTH_USERNAME", "")
    pw_hash = st.secrets.get("AUTH_PASSWORD_HASH", "")

    if not username or not pw_hash:
        st.warning("Auth is not configured (AUTH_USERNAME / AUTH_PASSWORD_HASH).")
        return

    if st.session_state.get("authed"):
        return

    with st.sidebar:
        st.subheader("🔐 Sign in")
        u = st.text_input("Username", key="auth_user")
        p = st.text_input("Password", type="password", key="auth_pass")
        if st.button("Login", use_container_width=True):
            ok_user = hmac.compare_digest(u.strip(), username)
            ok_pass = argon2.verify(p, pw_hash) if p else False
            if ok_user and ok_pass:
                st.session_state.authed = True
                st.success("Logged in.")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    st.stop()
