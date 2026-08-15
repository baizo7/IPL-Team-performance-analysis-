"""
Metrics Component
Renders key performance indicator metric tiles and match summary overview cards.
"""

import streamlit as st
import pandas as pd


def render_dashboard_metrics(df: pd.DataFrame, team1: str, team2: str) -> None:
    """Render top summary metrics columns."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Matches", f"{df['match_id'].nunique():,}")
    with col2:
        st.metric("⚾ Total Balls", f"{len(df):,}")
    with col3:
        t1_balls = len(df[df['batting_team'] == team1])
        st.metric(f"🏏 {team1}", f"{t1_balls:,} balls")
    with col4:
        t2_balls = len(df[df['batting_team'] == team2])
        st.metric(f"🏏 {team2}", f"{t2_balls:,} balls")
