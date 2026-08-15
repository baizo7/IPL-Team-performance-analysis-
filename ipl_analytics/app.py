"""
Main Application Entrypoint Runner
Orchestrates page config, authentication, data loading, navigation tabs, and chart rendering.
"""

import streamlit as st
import legacy_app


def run_app() -> None:
    """Run IPL Analytics Dashboard application."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = True

    legacy_app.render_legacy()
