"""
Sidebar Component
Renders team, venue, phase, bowler type, and AI Copilot sidebar controls.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_sidebar_filters(df: pd.DataFrame) -> Dict[str, Any]:
    """Render sidebar controls and return selected filter options dictionary."""
    st.sidebar.markdown("## 🏏 IPL Dashboard Controls")
    
    # Get Teams
    teams = sorted(list(df['batting_team'].dropna().unique())) if 'batting_team' in df.columns else []
    default_t1 = 'Chennai Super Kings' if 'Chennai Super Kings' in teams else (teams[0] if teams else 'Team 1')
    default_t2 = 'Delhi Capitals' if 'Delhi Capitals' in teams else (teams[1] if len(teams) > 1 else 'Team 2')
    
    team1 = st.sidebar.selectbox("Select Team 1", options=teams, index=teams.index(default_t1) if default_t1 in teams else 0)
    team2 = st.sidebar.selectbox("Select Team 2", options=teams, index=teams.index(default_t2) if default_t2 in teams else 0)
    
    # Phases
    phases = ['All Phases', 'Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
    selected_phase = st.sidebar.selectbox("Match Phase Filter", options=phases, index=0)
    
    # Bowler Type
    bowler_types = ['All Types', 'Pace / Fast', 'Spin', 'Right-Arm Fast', 'Left-Arm Fast', 'Right-Arm Spin', 'Left-Arm Spin']
    selected_bowler_type = st.sidebar.selectbox("Bowler Type Filter", options=bowler_types, index=0)
    
    # Venue
    venues = ['All Venues'] + sorted(list(df['venue'].dropna().unique())) if 'venue' in df.columns else ['All Venues']
    selected_venue = st.sidebar.selectbox("Venue Filter", options=venues, index=0)
    
    return {
        'team1': team1,
        'team2': team2,
        'selected_phase': selected_phase,
        'selected_bowler_type': selected_bowler_type,
        'selected_venue': selected_venue
    }
