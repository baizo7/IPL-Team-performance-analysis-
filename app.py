import streamlit as st
import legacy_app

st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Run the legacy dashboard directly
legacy_app.render_legacy()
