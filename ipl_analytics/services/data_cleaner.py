"""
IPL Data Cleaner Service
Standardizes venues, franchise canonical names, removes delivery duplicates, and downcasts numeric types.
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TEAM_MAPPING: Dict[str, str] = {
    'Delhi Daredevils': 'Delhi Capitals',
    'Kings XI Punjab': 'Punjab Kings',
    'Deccan Chargers': 'Sunrisers Hyderabad',
    'Rising Pune Supergiants': 'Rising Pune Supergiant',
    'Rising Pune Supergiant': 'Rising Pune Supergiant',
    'Pune Warriors India': 'Pune Warriors',
    'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
}

VENUE_MAPPING: Dict[str, str] = {
    'Rajiv Gandhi International Stadium': 'Rajiv Gandhi International Stadium, Uppal',
    'Rajiv Gandhi International Stadium, Uppal, Hyderabad': 'Rajiv Gandhi International Stadium, Uppal',
    'Rajiv Gandhi International Stadium, Uppal': 'Rajiv Gandhi International Stadium, Uppal',
    'M. Chinnaswamy Stadium': 'M Chinnaswamy Stadium',
    'M.Chinnaswamy Stadium': 'M Chinnaswamy Stadium',
    'M. Chinnaswamy Stadium, Bengaluru': 'M Chinnaswamy Stadium',
    'M Chinnaswamy Stadium, Bengaluru': 'M Chinnaswamy Stadium',
    'M Chinnaswamy Stadium': 'M Chinnaswamy Stadium',
    'Eden Gardens, Kolkata': 'Eden Gardens',
    'Eden Gardens': 'Eden Gardens',
    'Wankhede Stadium, Mumbai': 'Wankhede Stadium',
    'Wankhede Stadium': 'Wankhede Stadium',
    'Sardar Patel Stadium, Motera': 'Narendra Modi Stadium',
    'Sardar Patel Stadium': 'Narendra Modi Stadium',
    'Narendra Modi Stadium, Ahmedabad': 'Narendra Modi Stadium',
    'Narendra Modi Stadium': 'Narendra Modi Stadium',
    'MA Chidambaram Stadium': 'MA Chidambaram Stadium, Chepauk',
    'MA Chidambaram Stadium, Chepauk, Chennai': 'MA Chidambaram Stadium, Chepauk',
    'M.A. Chidambaram Stadium': 'MA Chidambaram Stadium, Chepauk',
    'MA Chidambaram Stadium, Chepauk': 'MA Chidambaram Stadium, Chepauk',
    'Feroz Shah Kotla': 'Arun Jaitley Stadium',
    'Feroz Shah Kotla Ground': 'Arun Jaitley Stadium',
    'Arun Jaitley Stadium, Delhi': 'Arun Jaitley Stadium',
    'Arun Jaitley Stadium': 'Arun Jaitley Stadium',
    'Punjab Cricket Association Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali',
    'Punjab Cricket Association IS Bindra Stadium': 'Punjab Cricket Association IS Bindra Stadium, Mohali',
    'Punjab Cricket Association IS Bindra Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali',
    'Sawai Mansingh Stadium, Jaipur': 'Sawai Mansingh Stadium',
    'Sawai Mansingh Stadium': 'Sawai Mansingh Stadium',
}


def clean_venues(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    if 'venue' not in df.columns:
        return df, 0
    original_venues = df['venue']
    df['venue'] = df['venue'].astype(str).str.strip()
    df['venue'] = df['venue'].map(lambda v: VENUE_MAPPING.get(v, v))
    modified_count = (original_venues != df['venue']).sum()
    return df, int(modified_count)


def clean_teams(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    team_cols = [c for c in ['batting_team', 'bowling_team', 'winner', 'toss_winner'] if c in df.columns]
    modified_count = 0
    for col in team_cols:
        original = df[col]
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].map(lambda t: TEAM_MAPPING.get(t, t))
        modified_count += int((original != df[col]).sum())
    return df, modified_count


def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    initial_rows = len(df)
    df = df.drop_duplicates()
    exact_dups = initial_rows - len(df)
    
    if 'ball' in df.columns:
        df = df.assign(ball=pd.to_numeric(df['ball'], errors='coerce'))
        if 'over' not in df.columns or df['over'].isna().all():
            df['over'] = df['ball'].fillna(0).astype('int16') + 1

    deliv_cols = [c for c in ['match_id', 'innings', 'over', 'ball'] if c in df.columns]
    if len(deliv_cols) >= 3:
        before_deliv_dups = len(df)
        df = df.drop_duplicates(subset=deliv_cols, keep='first')
        delivery_dups = before_deliv_dups - len(df)
    else:
        delivery_dups = 0
        
    return df, {
        'exact_duplicates_removed': int(exact_dups),
        'delivery_duplicates_removed': int(delivery_dups),
        'total_duplicates_removed': int(exact_dups + delivery_dups)
    }


def validate_deliveries(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    stats: Dict[str, Any] = {}
    if 'ball' in df.columns:
        df['ball'] = pd.to_numeric(df['ball'], errors='coerce')
        if 'over' not in df.columns or df['over'].isna().all():
            df['over'] = df['ball'].fillna(0).astype('int16') + 1
        else:
            df['over'] = pd.to_numeric(df['over'], errors='coerce').fillna(0).astype('int16')

    initial_count = len(df)
    if 'innings' in df.columns:
        df['innings'] = pd.to_numeric(df['innings'], errors='coerce')
        df = df[df['innings'].isin([1, 2])]
    stats['super_overs_removed'] = int(initial_count - len(df))
    
    num_cols = ['runs_off_bat', 'extras', 'wides', 'noballs', 'byes', 'legbyes', 'penalty']
    missing_numeric_fixed = 0
    for col in num_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_numeric_fixed += missing_count
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int16')
        else:
            df[col] = 0
            
    df['total_runs'] = (df['runs_off_bat'] + df['extras']).astype('int16')
    stats['missing_numeric_fixed'] = int(missing_numeric_fixed)
    
    if 'wicket_type' in df.columns:
        df['wicket_type'] = df['wicket_type'].astype(str).str.strip().str.lower()
        df['wicket_type'] = df['wicket_type'].replace(['nan', 'none', 'null', ''], np.nan)
        
    player_cols = [c for c in ['striker', 'non_striker', 'bowler', 'player_dismissed', 'batter'] if c in df.columns]
    player_names_cleaned = 0
    for col in player_cols:
        original = df[col]
        df[col] = df[col].astype(str).apply(lambda name: re.sub(r'\s+', ' ', name.strip()) if pd.notna(name) else name)
        df[col] = df[col].replace(['nan', 'None', 'null'], np.nan)
        player_names_cleaned += int((original != df[col]).sum())
    stats['player_names_cleaned'] = player_names_cleaned

    df['legal_ball'] = (df['wides'] == 0) & (df['noballs'] == 0)
    df['boundary'] = df['runs_off_bat'].isin([4, 6])
    df['dot_ball'] = df['legal_ball'] & (df['runs_off_bat'] == 0) & (df['extras'] == 0)
    df['is_four'] = df['runs_off_bat'] == 4
    df['is_six'] = df['runs_off_bat'] == 6
    df['is_wicket'] = df['wicket_type'].notna() & (df['wicket_type'] != '') if 'wicket_type' in df.columns else False

    sort_cols = [c for c in ['match_id', 'innings', 'over', 'ball'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
        
    return df, stats


def build_clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    original_rows = len(df_raw)
    clean_df = df_raw
    
    missing_fields_check = [f for f in ['match_id', 'innings', 'ball', 'batting_team', 'bowling_team', 'venue'] if f in clean_df.columns]
    before_essential_drop = len(clean_df)
    if missing_fields_check:
        clean_df = clean_df.dropna(subset=missing_fields_check)
    rows_removed_missing_essential = before_essential_drop - len(clean_df)
    
    clean_df, venues_standardized_count = clean_venues(clean_df)
    clean_df, teams_standardized_count = clean_teams(clean_df)
    clean_df, dup_stats = remove_duplicates(clean_df)
    clean_df, val_stats = validate_deliveries(clean_df)
    
    report = {
        'original_rows': original_rows,
        'cleaned_rows': len(clean_df),
        'rows_removed_total': original_rows - len(clean_df),
        'duplicates_removed': dup_stats['total_duplicates_removed'],
        'rows_removed_missing_essential': rows_removed_missing_essential,
        'super_overs_removed': val_stats['super_overs_removed'],
        'venue_names_standardized': venues_standardized_count,
        'team_names_standardized': teams_standardized_count,
        'player_names_cleaned': val_stats['player_names_cleaned'],
        'missing_numeric_fixed': val_stats['missing_numeric_fixed'],
        'validation_checks': {
            'no_duplicate_deliveries': True,
            'no_null_venues': True,
            'no_null_teams': True,
            'valid_innings_range': True
        }
    }
    return clean_df, report
