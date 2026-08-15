import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import io

def calculate_win_probability(
    target: int,
    current_runs: int,
    overs_bowled: float,
    wickets_lost: int,
    venue_avg_first_inns: float = 170.0
) -> Dict[str, Any]:
    """
    Calculate dynamic win probability percentage during an IPL chase.
    """
    balls_remaining = max(0, 120 - int(overs_bowled * 6))
    runs_needed = max(0, target - current_runs)
    wickets_remaining = max(0, 10 - wickets_lost)

    if runs_needed <= 0:
        return {"win_probability_batting": 100.0, "win_probability_bowling": 0.0, "required_run_rate": 0.0}
    if balls_remaining <= 0 or wickets_remaining <= 0:
        return {"win_probability_batting": 0.0, "win_probability_bowling": 100.0, "required_run_rate": 99.9}

    rrr = (runs_needed / balls_remaining) * 6
    curr_rr = (current_runs / max(1, (120 - balls_remaining))) * 6

    # Model baseline logistic function based on RRR, Wickets remaining, and overs left
    wkt_factor = (wickets_remaining / 10.0) ** 1.5
    rrr_penalty = np.exp((rrr - 8.5) / 2.5)
    
    prob = (wkt_factor / (1.0 + rrr_penalty)) * 100.0
    prob = float(np.clip(prob, 1.0, 99.0))

    return {
        "win_probability_batting": round(prob, 1),
        "win_probability_bowling": round(100.0 - prob, 1),
        "required_run_rate": round(rrr, 2),
        "current_run_rate": round(curr_rr, 2),
        "runs_needed": runs_needed,
        "balls_remaining": balls_remaining
    }

def analyze_toss_venue_impact(df: pd.DataFrame, venue: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze Toss Win % and Venue Pitch Bias (Batting 1st vs Fielding 1st win rates).
    """
    if df is None or df.empty:
        return {}

    filtered = df.copy()
    if venue and venue != "All Venues":
        filtered = filtered[filtered['venue'] == venue]

    if 'match_id' not in filtered.columns:
        return {}

    # Match level aggregation
    match_df = filtered.drop_duplicates(subset=['match_id']).copy()
    total_matches = len(match_df)
    if total_matches == 0:
        return {}

    # Toss impact if toss columns exist
    toss_wins = 0
    bat_first_wins = 0
    field_first_wins = 0

    if 'toss_winner' in match_df.columns and 'winner' in match_df.columns:
        toss_wins = (match_df['toss_winner'] == match_df['winner']).sum()
        
        if 'toss_decision' in match_df.columns:
            bat_first_wins = ((match_df['toss_decision'] == 'bat') & (match_df['toss_winner'] == match_df['winner'])).sum()
            field_first_wins = ((match_df['toss_decision'] == 'field') & (match_df['toss_winner'] == match_df['winner'])).sum()

    return {
        "total_matches": total_matches,
        "toss_win_win_pct": round((toss_wins / total_matches) * 100, 1) if total_matches > 0 else 0.0,
        "bat_first_win_pct": round((bat_first_wins / total_matches) * 100, 1) if total_matches > 0 else 0.0,
        "field_first_win_pct": round((field_first_wins / total_matches) * 100, 1) if total_matches > 0 else 0.0,
        "venue": venue or "All Venues"
    }

def calculate_player_impact_scores(df: pd.DataFrame, team: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Calculate IPL-style Player Impact Score based on phase-weighted contribution.
    """
    if df is None or df.empty:
        return []

    data = df.copy()
    if team:
        data = data[(data['batting_team'] == team) | (data['bowling_team'] == team)]

    # Batting contribution
    bat_df = data.groupby('striker').agg(
        runs=('runs_off_bat', 'sum'),
        balls=('ball', 'count'),
        fours=('runs_off_bat', lambda x: (x == 4).sum()),
        sixes=('runs_off_bat', lambda x: (x == 6).sum()),
        death_runs=('runs_off_bat', lambda x: x[data.loc[x.index, 'phase'] == 'Death'].sum() if 'phase' in data.columns else 0)
    ).reset_index().rename(columns={'striker': 'player'})

    bat_df['sr'] = (bat_df['runs'] / np.maximum(1, bat_df['balls'])) * 100
    bat_df['bat_impact'] = (
        (bat_df['runs'] * 1.0) +
        ((bat_df['sr'] - 130) * 0.4) +
        (bat_df['fours'] * 1.5) +
        (bat_df['sixes'] * 2.5) +
        (bat_df['death_runs'] * 0.5)
    )

    # Bowling contribution
    bwl_df = data.groupby('bowler').agg(
        balls=('ball', 'count'),
        runs_conceded=('runs_off_bat', 'sum'),
        wickets=('is_wicket', 'sum') if 'is_wicket' in data.columns else ('wicket', 'sum'),
        dots=('runs_off_bat', lambda x: (x == 0).sum())
    ).reset_index().rename(columns={'bowler': 'player'})

    bwl_df['econ'] = (bwl_df['runs_conceded'] / (np.maximum(1, bwl_df['balls']) / 6))
    bwl_df['bwl_impact'] = (
        (bwl_df['wickets'] * 25.0) +
        (bwl_df['dots'] * 1.5) +
        (np.maximum(0, 8.5 - bwl_df['econ']) * 4.0)
    )

    # Merge impacts
    impact_df = pd.merge(bat_df, bwl_df, on='player', how='outer', suffixes=('_bat', '_bwl')).fillna(0)
    impact_df['total_impact'] = (impact_df['bat_impact'] + impact_df['bwl_impact']).round(1)

    top_players = impact_df.sort_values('total_impact', ascending=False).head(15)
    return top_players.to_dict(orient='records')

def get_season_over_season_comparison(df: pd.DataFrame, team: str) -> List[Dict[str, Any]]:
    """
    Generate season-over-season performance progression for a team.
    """
    if df is None or df.empty or 'season' not in df.columns:
        return []

    team_data = df[df['batting_team'] == team].copy()
    if team_data.empty:
        return []

    season_stats = team_data.groupby('season').agg(
        total_runs=('runs_off_bat', 'sum'),
        total_balls=('ball', 'count'),
        sixes=('runs_off_bat', lambda x: (x == 6).sum()),
        fours=('runs_off_bat', lambda x: (x == 4).sum()),
        dots=('runs_off_bat', lambda x: (x == 0).sum())
    ).reset_index()

    season_stats['run_rate'] = ((season_stats['total_runs'] / season_stats['total_balls']) * 6).round(2)
    season_stats['boundary_pct'] = (((season_stats['sixes'] + season_stats['fours']) / season_stats['total_balls']) * 100).round(1)

    return season_stats.sort_values('season').to_dict(orient='records')

def export_to_csv(data: List[Dict[str, Any]]) -> str:
    """Export dataset dictionary list to CSV string."""
    df_export = pd.DataFrame(data)
    return df_export.to_csv(index=False)
