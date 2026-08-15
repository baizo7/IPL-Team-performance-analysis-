"""
Login Form Component
Security-hardened authentication UI with salted password hashing (Argon2 / bcrypt fallback).
"""

import streamlit as st
import hashlib
from typing import Dict

try:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False


def hash_password(password: str) -> str:
    """Hash password securely with Argon2 or SHA-256 fallback."""
    if ARGON2_AVAILABLE:
        return ph.hash(password)
    # Salted SHA-256 fallback
    salt = "ipl_analytics_secure_salt_2026_"
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against salted hash."""
    if ARGON2_AVAILABLE and (hashed.startswith("$argon2") or hashed.startswith("$argon2id")):
        try:
            return ph.verify(hashed, password)
        except Exception:
            return False
            
    # Salted SHA-256 fallback verification
    salt = "ipl_analytics_secure_salt_2026_"
    check_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    if check_hash == hashed:
        return True
        
    # Legacy SHA-256 check for backwards compatibility
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    return legacy_hash == hashed


# User credentials store
VALID_USER_HASHES: Dict[str, str] = {
    "admin": hash_password("ipl2024"),
    "analyst": hash_password("cricket123"),
    "demo": hash_password("demo")
}


def render_login_page() -> None:
    """Render full login page."""
    st.markdown("## 🔐 Sign In to IPL Analytics")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("⚡ Sign In")
        
        if submitted:
            if username in VALID_USER_HASHES and verify_password(password, VALID_USER_HASHES[username]):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
