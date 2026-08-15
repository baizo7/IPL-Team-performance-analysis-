"""
Phase Analysis Chart Generators
Phase efficiency matrix, worm curves, pace vs spin breakdown, and innings split.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from ipl_analytics.charts.base import get_plotly_layout_theme, get_team_color
from ipl_analytics.utils.helpers import _filter_by_bowler_type


def calculate_run_rate_by_phase(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Calculate run rate per phase for specified team."""
    team_data = df[df['batting_team'] == team]
    phase_stats = team_data.groupby('phase', observed=False).agg({
        'total_runs': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()
    phase_stats['run_rate'] = (phase_stats['total_runs'] / phase_stats['ball']) * 6
    phase_stats['wickets'] = phase_stats['is_wicket']
    phase_stats['avg_runs_per_ball'] = phase_stats['total_runs'] / phase_stats['ball']
    return phase_stats


def calculate_comprehensive_phase_stats(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """Calculate comprehensive phase statistics including Run Rate, Dot %, Boundary %, Wickets, and Efficiency Index."""
    team_data = df[df['batting_team'] == team].copy()
    phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
    
    results = []
    for p in phases:
        p_df = team_data[team_data['phase'] == p]
        total_balls = len(p_df)
        if total_balls == 0:
            results.append({
                'phase': p, 'runs': 0, 'balls': 0, 'wickets': 0,
                'run_rate': 0.0, 'balls_per_wicket': 0.0,
                'dot_pct': 0.0, 'boundary_pct': 0.0, 'efficiency_index': 0.0
            })
            continue
        
        runs = int(p_df['total_runs'].sum()) if 'total_runs' in p_df.columns else int(p_df['runs_off_bat'].sum())
        wickets = int(p_df['is_wicket'].sum())
        dots = int((p_df['runs_off_bat'] == 0).sum())
        boundaries = int(((p_df['runs_off_bat'] == 4) | (p_df['runs_off_bat'] == 6)).sum())
        
        rr = round((runs / total_balls) * 6, 2)
        bpw = round(total_balls / wickets, 1) if wickets > 0 else float(total_balls)
        dot_pct = round((dots / total_balls) * 100, 1)
        boundary_pct = round((boundaries / total_balls) * 100, 1)
        eff_index = round((rr * boundary_pct) / (dot_pct + 1.0), 2)
        
        results.append({
            'phase': p,
            'runs': runs,
            'balls': total_balls,
            'wickets': wickets,
            'run_rate': rr,
            'balls_per_wicket': bpw,
            'dot_pct': dot_pct,
            'boundary_pct': boundary_pct,
            'efficiency_index': eff_index
        })
        
    return pd.DataFrame(results)


def create_phase_efficiency_matrix_chart(df: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Create side-by-side Phase Efficiency Matrix scatter plot."""
    s1 = calculate_comprehensive_phase_stats(df, team1)
    s2 = calculate_comprehensive_phase_stats(df, team2)
    s1['team'] = team1
    s2['team'] = team2
    combined = pd.concat([s1, s2], ignore_index=True)
    
    fig = px.scatter(
        combined,
        x='dot_pct',
        y='run_rate',
        size='efficiency_index',
        color='team',
        symbol='phase',
        hover_name='phase',
        hover_data=['boundary_pct', 'wickets', 'balls_per_wicket'],
        color_discrete_map={team1: get_team_color(team1), team2: get_team_color(team2)},
        labels={'dot_pct': 'Dot Ball % (Lower is Better)', 'run_rate': 'Run Rate (RPO)', 'efficiency_index': 'Efficiency Index'},
        title=f"<b>Phase Efficiency Matrix — {team1} vs {team2}</b>"
    )
    fig.update_layout(**get_plotly_layout_theme(f"Phase Efficiency Matrix — {team1} vs {team2}", height=450))
    return fig


def create_phase_overlay_worm_chart(df: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Create cumulative run rate worm curves across 20 overs."""
    fig = go.Figure()
    
    for team, col in [(team1, get_team_color(team1)), (team2, get_team_color(team2))]:
        t_df = df[df['batting_team'] == team]
        if t_df.empty:
            continue
        over_runs = t_df.groupby('over')['total_runs'].sum().reset_index()
        over_runs['cum_runs'] = over_runs['total_runs'].cumsum()
        over_runs['cum_rr'] = (over_runs['cum_runs'] / over_runs['over']).round(2)
        
        fig.add_trace(go.Scatter(
            x=over_runs['over'],
            y=over_runs['cum_rr'],
            mode='lines+markers',
            name=team,
            line=dict(color=col, width=3),
            marker=dict(size=6)
        ))
        
    fig.update_layout(**get_plotly_layout_theme(f"Cumulative Run Rate Worm — {team1} vs {team2}", height=420))
    return fig


def create_phase_pace_vs_spin_chart(df: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Create Pace vs Spin comparison bar chart across match phases."""
    fig = go.Figure()
    for team, col in [(team1, get_team_color(team1)), (team2, get_team_color(team2))]:
        t_df = df[df['batting_team'] == team]
        if t_df.empty or 'bowler_type' not in t_df.columns:
            continue
        t_df = _filter_by_bowler_type(t_df, 'Pace')
        pace_stats = t_df.groupby('phase', observed=False)['total_runs'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=pace_stats['phase'],
            y=pace_stats['total_runs'],
            name=f"{team} vs Pace",
            marker_color=col
        ))
    fig.update_layout(barmode='group', **get_plotly_layout_theme(f"Pace vs Spin Phase Breakdown — {team1} vs {team2}", height=420))
    return fig


def create_phase_innings_split_chart(df: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Create 1st Innings vs 2nd Innings run rate split chart."""
    fig = go.Figure()
    for team, col in [(team1, get_team_color(team1)), (team2, get_team_color(team2))]:
        t_df = df[df['batting_team'] == team]
        if t_df.empty:
            continue
        inns_stats = t_df.groupby('innings')['total_runs'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=[f"Innings {i}" for i in inns_stats['innings']],
            y=inns_stats['total_runs'],
            name=team,
            marker_color=col
        ))
    fig.update_layout(barmode='group', **get_plotly_layout_theme(f"Innings Split — {team1} vs {team2}", height=420))
    return fig
