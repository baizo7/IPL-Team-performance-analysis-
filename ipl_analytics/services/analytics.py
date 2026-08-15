import pandas as pd
import numpy as np
from functools import lru_cache

from ipl_analytics.utils.theme import PHASE_ORDER
from ipl_analytics.utils.helpers import filter_by_bowler_type, filter_team_data


@lru_cache(maxsize=128)
def calculate_run_rate_by_phase(df_tuple, team: str) -> pd.DataFrame:
    """Calculate run rate by phase for a team."""
    df = pd.DataFrame(df_tuple)
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


@lru_cache(maxsize=128)
def calculate_comprehensive_phase_stats(df_tuple, team: str) -> pd.DataFrame:
    """Calculate comprehensive phase statistics."""
    df = pd.DataFrame(df_tuple)
    team_data = df[df['batting_team'] == team].copy()
    
    results = []
    for p in PHASE_ORDER:
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
            'phase': p, 'runs': runs, 'balls': total_balls, 'wickets': wickets,
            'run_rate': rr, 'balls_per_wicket': bpw, 'dot_pct': dot_pct,
            'boundary_pct': boundary_pct, 'efficiency_index': eff_index
        })
    
    return pd.DataFrame(results)


@lru_cache(maxsize=128)
def calculate_player_matchup(df_tuple, player: str, bowler_type: str, team: str | None = None) -> dict | None:
    """Calculate player vs bowler type matchup stats."""
    df = pd.DataFrame(df_tuple)
    filtered = filter_by_bowler_type(df, bowler_type)
    if team:
        filtered = filtered[filtered['batting_team'] == team]
    player_data = filtered[filtered['batter'] == player]
    if len(player_data) == 0:
        return None
    
    balls = len(player_data)
    runs = int(player_data['runs_off_bat'].sum())
    dismissals = int(player_data['is_wicket'].sum())
    
    return {
        'balls_faced': int(balls),
        'runs_scored': runs,
        'dismissals': dismissals,
        'strike_rate': float((runs / balls) * 100 if balls > 0 else 0),
        'dismissal_rate': float((dismissals / balls) * 100 if balls > 0 else 0),
        'average': float(runs / dismissals if dismissals > 0 else runs)
    }


def get_top_batters(df: pd.DataFrame, team: str, n: int = 5) -> pd.DataFrame:
    """Get top batters for a team."""
    team_data = df[df['batting_team'] == team]
    stats = team_data.groupby('batter').agg({
        'runs_off_bat': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()
    stats = stats[stats['ball'] >= 30].sort_values('runs_off_bat', ascending=False).head(n)
    return stats