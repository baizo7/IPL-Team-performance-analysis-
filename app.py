import streamlit as st

st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

import ipl_analytics.app

if __name__ == "__main__":
    ipl_analytics.app.run_app()
