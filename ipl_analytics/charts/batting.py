"""
Batting Analytics Chart Generators
Runs distribution pie charts, strike rate comparisons, and player matchup heatmaps.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from ipl_analytics.charts.base import get_plotly_layout_theme, get_team_color
from ipl_analytics.utils.helpers import _filter_by_bowler_type


def calculate_player_matchup(_df: pd.DataFrame, player: str, bowler_type: str, team: Optional[str] = None) -> pd.DataFrame:
    """Calculate player matchup statistics against specified bowler type."""
    filtered = _filter_by_bowler_type(_df, bowler_type)
    if team:
        filtered = filtered[filtered['batting_team'] == team]
    player_data = filtered[filtered['batter'] == player]
    
    if player_data.empty:
        return pd.DataFrame()
        
    stats = player_data.groupby('bowler').agg(
        runs=('runs_off_bat', 'sum'),
        balls=('ball', 'count'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    
    stats['sr'] = (stats['runs'] / stats['balls'] * 100).round(2)
    return stats.sort_values('runs', ascending=False)


def create_runs_distribution_chart(df: pd.DataFrame, team: str) -> go.Figure:
    """Create pie chart of team runs distribution (1s, 2s, 3s, 4s, 6s, Extras)."""
    t_df = df[df['batting_team'] == team]
    if t_df.empty:
        return go.Figure()
        
    ones = int((t_df['runs_off_bat'] == 1).sum()) * 1
    twos = int((t_df['runs_off_bat'] == 2).sum()) * 2
    threes = int((t_df['runs_off_bat'] == 3).sum()) * 3
    fours = int((t_df['runs_off_bat'] == 4).sum()) * 4
    sixes = int((t_df['runs_off_bat'] == 6).sum()) * 6
    extras = int(t_df['extras'].sum()) if 'extras' in t_df.columns else 0
    
    labels = ['Singles (1s)', 'Doubles (2s)', 'Triples (3s)', 'Boundaries (4s)', 'Sixes (6s)', 'Extras']
    values = [ones, twos, threes, fours, sixes, extras]
    
    fig = px.pie(
        names=labels,
        values=values,
        title=f"<b>{team} — Scoring Distribution</b>",
        color_discrete_sequence=['#38bdf8', '#818cf8', '#c084fc', '#4ade80', '#f43f5e', '#fbbf24'],
        hole=0.4
    )
    fig.update_layout(**get_plotly_layout_theme(f"{team} Scoring Distribution", height=400))
    return fig


def create_strike_rate_comparison(df: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Compare top 5 batters strike rate between two teams."""
    fig = go.Figure()
    
    for team, col in [(team1, get_team_color(team1)), (team2, get_team_color(team2))]:
        t_df = df[df['batting_team'] == team]
        if t_df.empty:
            continue
        stats = t_df.groupby('batter').agg(
            runs=('runs_off_bat', 'sum'),
            balls=('ball', 'count')
        ).reset_index()
        stats = stats[stats['balls'] >= 30]
        stats['sr'] = (stats['runs'] / stats['balls'] * 100).round(2)
        top5 = stats.sort_values('runs', ascending=False).head(5)
        
        fig.add_trace(go.Bar(
            x=top5['batter'],
            y=top5['sr'],
            name=team,
            marker_color=col,
            text=top5['sr'],
            textposition='auto'
        ))
        
    fig.update_layout(barmode='group', **get_plotly_layout_theme(f"Top Batters Strike Rate — {team1} vs {team2}", height=420))
    return fig


def create_player_matchup_heatmap(df: pd.DataFrame, team: str) -> go.Figure:
    """Create player matchup heatmap (Batter vs Bowler runs)."""
    t_df = df[df['batting_team'] == team]
    if t_df.empty:
        return go.Figure()
        
    pivot = t_df.pivot_table(index='batter', columns='bowler', values='runs_off_bat', aggfunc='sum', fill_value=0)
    top_batters = t_df.groupby('batter')['runs_off_bat'].sum().nlargest(8).index
    top_bowlers = t_df.groupby('bowler')['runs_off_bat'].sum().nlargest(8).index
    pivot_sub = pivot.loc[pivot.index.isin(top_batters), pivot.columns.isin(top_bowlers)]
    
    fig = px.imshow(
        pivot_sub,
        labels=dict(x="Bowler", y="Batter", color="Runs Conceded"),
        x=pivot_sub.columns,
        y=pivot_sub.index,
        color_continuous_scale='Viridis',
        title=f"<b>{team} — Batter vs Bowler Head-to-Head Heatmap</b>"
    )
    fig.update_layout(**get_plotly_layout_theme(f"{team} Matchup Heatmap", height=450))
    return fig
