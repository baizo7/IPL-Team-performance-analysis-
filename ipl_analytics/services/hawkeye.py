"""
Hawk-Eye Telemetry Processor Service
Singleton resource manager for spatial delivery coordinates and tracking telemetry.
"""

import streamlit as st
from hawkeye_processor import HawkeyeProcessor


@st.cache_resource(show_spinner="Initializing Hawk-Eye Tracking Telemetry Engine...")
def get_hawkeye_processor() -> HawkeyeProcessor:
    """Instantiate and load Hawk-Eye tracking processor instance."""
    hp = HawkeyeProcessor()
    hp.load()
    return hp
