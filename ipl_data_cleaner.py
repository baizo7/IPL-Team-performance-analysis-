import pandas as pd
import numpy as np
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Canonical Team Mapping
TEAM_MAPPING = {
    'Delhi Daredevils': 'Delhi Capitals',
    'Kings XI Punjab': 'Punjab Kings',
    'Deccan Chargers': 'Sunrisers Hyderabad',
    'Rising Pune Supergiants': 'Rising Pune Supergiant',
    'Rising Pune Supergiant': 'Rising Pune Supergiant',
    'Pune Warriors India': 'Pune Warriors',
    'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
}

# Canonical Venue Mapping
VENUE_MAPPING = {
    # Rajiv Gandhi International Stadium
    'Rajiv Gandhi International Stadium': 'Rajiv Gandhi International Stadium, Uppal',
    'Rajiv Gandhi International Stadium, Uppal, Hyderabad': 'Rajiv Gandhi International Stadium, Uppal',
    'Rajiv Gandhi International Stadium, Uppal': 'Rajiv Gandhi International Stadium, Uppal',

    # M Chinnaswamy Stadium
    'M. Chinnaswamy Stadium': 'M Chinnaswamy Stadium',
    'M.Chinnaswamy Stadium': 'M Chinnaswamy Stadium',
    'M. Chinnaswamy Stadium, Bengaluru': 'M Chinnaswamy Stadium',
    'M Chinnaswamy Stadium, Bengaluru': 'M Chinnaswamy Stadium',
    'M Chinnaswamy Stadium': 'M Chinnaswamy Stadium',

    # Eden Gardens
    'Eden Gardens, Kolkata': 'Eden Gardens',
    'Eden Gardens': 'Eden Gardens',

    # Wankhede Stadium
    'Wankhede Stadium, Mumbai': 'Wankhede Stadium',
    'Wankhede Stadium': 'Wankhede Stadium',

    # Narendra Modi Stadium / Motera
    'Sardar Patel Stadium, Motera': 'Narendra Modi Stadium',
    'Sardar Patel Stadium': 'Narendra Modi Stadium',
    'Narendra Modi Stadium, Ahmedabad': 'Narendra Modi Stadium',
    'Narendra Modi Stadium': 'Narendra Modi Stadium',

    # MA Chidambaram Stadium
    'MA Chidambaram Stadium': 'MA Chidambaram Stadium, Chepauk',
    'MA Chidambaram Stadium, Chepauk, Chennai': 'MA Chidambaram Stadium, Chepauk',
    'M.A. Chidambaram Stadium': 'MA Chidambaram Stadium, Chepauk',
    'MA Chidambaram Stadium, Chepauk': 'MA Chidambaram Stadium, Chepauk',

    # Arun Jaitley Stadium / Feroz Shah Kotla
    'Feroz Shah Kotla': 'Arun Jaitley Stadium',
    'Feroz Shah Kotla Ground': 'Arun Jaitley Stadium',
    'Arun Jaitley Stadium, Delhi': 'Arun Jaitley Stadium',
    'Arun Jaitley Stadium': 'Arun Jaitley Stadium',

    # Punjab Cricket Association Stadium / Mohali
    'Punjab Cricket Association Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali',
    'Punjab Cricket Association IS Bindra Stadium': 'Punjab Cricket Association IS Bindra Stadium, Mohali',
    'Punjab Cricket Association IS Bindra Stadium, Mohali': 'Punjab Cricket Association IS Bindra Stadium, Mohali',

    # Sawai Mansingh Stadium
    'Sawai Mansingh Stadium, Jaipur': 'Sawai Mansingh Stadium',
    'Sawai Mansingh Stadium': 'Sawai Mansingh Stadium',

    # Maharashtra Cricket Association Stadium / Pune
    'Subrata Roy Sahara Stadium': 'Maharashtra Cricket Association Stadium',
    'Maharashtra Cricket Association Stadium, Pune': 'Maharashtra Cricket Association Stadium',
    'Maharashtra Cricket Association Stadium': 'Maharashtra Cricket Association Stadium',

    # Visakhapatnam
    'Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium': 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium',
    'Dr YS Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam': 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium',
    'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium': 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium',

    # UAE Venues
    'Dubai International Cricket Stadium, Dubai': 'Dubai International Cricket Stadium',
    'Dubai International Cricket Stadium': 'Dubai International Cricket Stadium',
    'Sharjah Cricket Stadium, Sharjah': 'Sharjah Cricket Stadium',
    'Sharjah Cricket Stadium': 'Sharjah Cricket Stadium',
    'Sheikh Zayed Stadium': 'Sheikh Zayed Stadium',
    'Zayed Cricket Stadium, Abu Dhabi': 'Sheikh Zayed Stadium',

    # Other Venues
    'Brabourne Stadium, Mumbai': 'Brabourne Stadium',
    'Brabourne Stadium': 'Brabourne Stadium',
    'Dr DY Patil Sports Academy, Mumbai': 'Dr DY Patil Sports Academy',
    'Dr DY Patil Sports Academy': 'Dr DY Patil Sports Academy',
    'Holkar Cricket Stadium, Indore': 'Holkar Cricket Stadium',
    'Holkar Cricket Stadium': 'Holkar Cricket Stadium',
    'BARSAPARA Cricket Stadium': 'Barsapara Cricket Stadium',
    'Barsapara Cricket Stadium, Guwahati': 'Barsapara Cricket Stadium',
    'Barsapara Cricket Stadium': 'Barsapara Cricket Stadium',
    'Himachal Pradesh Cricket Association Stadium, Dharamsala': 'Himachal Pradesh Cricket Association Stadium',
    'Himachal Pradesh Cricket Association Stadium': 'Himachal Pradesh Cricket Association Stadium',
    'Ekana Cricket Stadium': 'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium',
    'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow': 'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium',
    'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium': 'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium',
    'Green Park, Kanpur': 'Green Park',
    'Green Park': 'Green Park',
    'JSCA International Stadium Complex, Ranchi': 'JSCA International Stadium Complex',
    'JSCA International Stadium Complex': 'JSCA International Stadium Complex',
    'Shaheed Veer Narayan Singh International Stadium, Raipur': 'Shaheed Veer Narayan Singh International Stadium',
    'Shaheed Veer Narayan Singh International Stadium': 'Shaheed Veer Narayan Singh International Stadium',
    'Barabati Stadium, Cuttack': 'Barabati Stadium',
    'Barabati Stadium': 'Barabati Stadium',
    'Nehru Stadium, Kochi': 'Nehru Stadium',
    'Nehru Stadium': 'Nehru Stadium',
    'Vidarbha Cricket Association Stadium, Jamtha': 'Vidarbha Cricket Association Stadium, Jamtha',
    'Vidarbha Cricket Association Stadium': 'Vidarbha Cricket Association Stadium, Jamtha',
}


def clean_venues(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Standardize all venue names using canonical mappings.
    Returns modified DataFrame and count of modified venue names.
    """
    if 'venue' not in df.columns:
        return df, 0

    original_venues = df['venue']
    df['venue'] = df['venue'].astype(str).str.strip()
    df['venue'] = df['venue'].map(lambda v: VENUE_MAPPING.get(v, v))
    
    modified_count = (original_venues != df['venue']).sum()
    return df, int(modified_count)


def clean_teams(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Standardize franchise names across all team-related columns.
    Returns modified DataFrame and count of modified team names.
    """
    team_cols = [c for c in ['batting_team', 'bowling_team', 'winner', 'toss_winner'] if c in df.columns]
    
    modified_count = 0
    for col in team_cols:
        original = df[col]
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].map(lambda t: TEAM_MAPPING.get(t, t))
        modified_count += int((original != df[col]).sum())
        
    return df, modified_count


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Remove exact duplicate rows and delivery-level duplicates (match_id, innings, over, ball).
    """
    initial_rows = len(df)
    
    # 1. Exact row duplicates
    df = df.drop_duplicates()
    exact_dups = initial_rows - len(df)
    
    # 2. Duplicate deliveries (match_id + innings + over + ball or match_id + innings + ball)
    if 'ball' in df.columns:
        df['ball'] = pd.to_numeric(df['ball'], errors='coerce')
        if 'over' not in df.columns or df['over'].isna().all():
            df['over'] = df['ball'].fillna(0).astype('int16') + 1

    deliv_cols = [c for c in ['match_id', 'innings', 'over', 'ball'] if c in df.columns]
    if len(deliv_cols) >= 3:
        before_deliv_dups = len(df)
        df = df.drop_duplicates(subset=deliv_cols, keep='first')
        delivery_dups = before_deliv_dups - len(df)
    else:
        delivery_dups = 0
        
    stats = {
        'exact_duplicates_removed': int(exact_dups),
        'delivery_duplicates_removed': int(delivery_dups),
        'total_duplicates_removed': int(exact_dups + delivery_dups)
    }
    return df, stats


def validate_deliveries(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Validate numeric columns, dismissal types, player names, innings, and create helper columns.
    """
    stats = {}
    
    # 1. Normalize ball and calculate over
    if 'ball' in df.columns:
        df['ball'] = pd.to_numeric(df['ball'], errors='coerce')
        if 'over' not in df.columns or df['over'].isna().all():
            df['over'] = df['ball'].fillna(0).astype('int16') + 1
        else:
            df['over'] = pd.to_numeric(df['over'], errors='coerce').fillna(0).astype('int16')

    # 2. Remove Super Overs (keep innings 1 & 2)
    initial_count = len(df)
    if 'innings' in df.columns:
        df['innings'] = pd.to_numeric(df['innings'], errors='coerce')
        df = df[df['innings'].isin([1, 2])]
    super_overs_removed = initial_count - len(df)
    stats['super_overs_removed'] = int(super_overs_removed)
    
    # 3. Numeric Columns Validation & Imputation (Downcast to int16/int32 for RAM savings)
    num_cols = ['runs_off_bat', 'extras', 'wides', 'noballs', 'byes', 'legbyes', 'penalty']
    missing_numeric_fixed = 0
    for col in num_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_numeric_fixed += missing_count
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int16')
        else:
            df[col] = 0
            
    # Compute total_runs
    df['total_runs'] = (df['runs_off_bat'] + df['extras']).astype('int16')
    stats['missing_numeric_fixed'] = int(missing_numeric_fixed)
    
    # 4. Standardize Wicket/Dismissal Values
    if 'wicket_type' in df.columns:
        df['wicket_type'] = df['wicket_type'].astype(str).str.strip().str.lower()
        df['wicket_type'] = df['wicket_type'].replace(['nan', 'none', 'null', ''], np.nan)
        
    # 5. Standardize Player Names
    player_cols = [c for c in ['striker', 'non_striker', 'bowler', 'player_dismissed', 'batter'] if c in df.columns]
    player_names_cleaned = 0
    for col in player_cols:
        original = df[col]
        df[col] = df[col].astype(str).apply(lambda name: re.sub(r'\s+', ' ', name.strip()) if pd.notna(name) else name)
        df[col] = df[col].replace(['nan', 'None', 'null'], np.nan)
        player_names_cleaned += int((original != df[col]).sum())
    stats['player_names_cleaned'] = player_names_cleaned

    # 6. Validate Innings (A team can bat at most once per innings per match)
    if all(c in df.columns for c in ['match_id', 'innings', 'batting_team']):
        team_innings_counts = df.groupby(['match_id', 'innings', 'batting_team']).ngroups
        total_innings_combinations = df.groupby(['match_id', 'innings']).ngroups
        stats['valid_team_innings'] = bool(team_innings_counts == total_innings_combinations)
    else:
        stats['valid_team_innings'] = True

    # 7. Helper Columns (Booleans)
    df['legal_ball'] = (df['wides'] == 0) & (df['noballs'] == 0)
    df['boundary'] = df['runs_off_bat'].isin([4, 6])
    df['dot_ball'] = df['legal_ball'] & (df['runs_off_bat'] == 0) & (df['extras'] == 0)
    df['is_four'] = df['runs_off_bat'] == 4
    df['is_six'] = df['runs_off_bat'] == 6
    NON_BOWLER_DISMISSALS = ['run out', 'retired hurt', 'retired out', 'obstructing the field']
    df['is_wicket'] = df['wicket_type'].notna() & (df['wicket_type'] != '') if 'wicket_type' in df.columns else False
    df['is_bowler_wicket'] = df['is_wicket'] & (~df['wicket_type'].astype(str).str.lower().isin(NON_BOWLER_DISMISSALS))

    # 8. Sort Data Correctly
    sort_cols = [c for c in ['match_id', 'innings', 'over', 'ball'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
        
    return df, stats


def build_clean_dataset(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Main Data Pipeline function. 
    Cleans raw DataFrame efficiently and generates a Data Quality Report.
    """
    original_rows = len(df_raw)
    clean_df = df_raw
    
    # 1. Remove rows missing essential fields
    essential_fields = ['match_id', 'innings', 'over', 'ball', 'batting_team', 'bowling_team', 'venue']
    # Check fields present in raw data
    missing_fields_check = [f for f in ['match_id', 'innings', 'ball', 'batting_team', 'bowling_team', 'venue'] if f in clean_df.columns]
    
    before_essential_drop = len(clean_df)
    if missing_fields_check:
        clean_df = clean_df.dropna(subset=missing_fields_check)
    rows_removed_missing_essential = before_essential_drop - len(clean_df)
    
    # 2. Clean Venues
    clean_df, venues_standardized_count = clean_venues(clean_df)
    
    # 3. Clean Teams
    clean_df, teams_standardized_count = clean_teams(clean_df)
    
    # 4. Remove Duplicates (Row & Delivery)
    clean_df, dup_stats = remove_duplicates(clean_df)
    
    # 5. Validate Deliveries, Super Overs, Numeric & Helpers
    clean_df, val_stats = validate_deliveries(clean_df)
    
    cleaned_rows = len(clean_df)
    
    # 6. Perform Validation Checks
    deliv_cols = [c for c in ['match_id', 'innings', 'over', 'ball'] if c in clean_df.columns]
    validation_checks = {
        'no_duplicate_deliveries': bool(clean_df.duplicated(subset=deliv_cols).sum() == 0) if deliv_cols else True,
        'no_null_venues': bool(clean_df['venue'].isna().sum() == 0) if 'venue' in clean_df.columns else True,
        'no_null_teams': bool((clean_df['batting_team'].isna().sum() == 0) and (clean_df['bowling_team'].isna().sum() == 0)) if 'batting_team' in clean_df.columns else True,
        'valid_innings_range': bool(clean_df['innings'].isin([1, 2]).all()) if 'innings' in clean_df.columns else True,
        'valid_over_numbers': bool((clean_df['over'] >= 1).all()) if 'over' in clean_df.columns else True,
        'valid_team_innings': val_stats.get('valid_team_innings', True)
    }
    
    # 7. Generate Quality Report
    report = {
        'original_rows': original_rows,
        'cleaned_rows': cleaned_rows,
        'rows_removed_total': original_rows - cleaned_rows,
        'duplicates_removed': dup_stats['total_duplicates_removed'],
        'rows_removed_missing_essential': rows_removed_missing_essential,
        'super_overs_removed': val_stats['super_overs_removed'],
        'venue_names_standardized': venues_standardized_count,
        'team_names_standardized': teams_standardized_count,
        'player_names_cleaned': val_stats['player_names_cleaned'],
        'missing_numeric_fixed': val_stats['missing_numeric_fixed'],
        'validation_checks': validation_checks
    }
    
    return clean_df, report


def clean_hawkeye_mens_dataset(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean and standardize real Hawk-Eye tracking dataset (hawkeye_mens_ipl.csv).
    """
    original_rows = len(df_raw)
    clean_df = df_raw.copy()

    # 1. Drop missing essential keys
    clean_df = clean_df.dropna(subset=['matchId', 'batter', 'bowler'])
    missing_essential_drop = original_rows - len(clean_df)

    # 2. Drop duplicates
    initial_dups_check = len(clean_df)
    clean_df = clean_df.drop_duplicates()
    if 'matchId' in clean_df.columns and 'delivery' in clean_df.columns:
        clean_df = clean_df.drop_duplicates(subset=['matchId', 'delivery'], keep='first')
    duplicates_removed = initial_dups_check - len(clean_df)

    # 3. Standardize Player Names
    player_cols = ['batter', 'nonStriker', 'bowler']
    player_names_cleaned = 0
    for col in player_cols:
        if col in clean_df.columns:
            orig = clean_df[col].copy()
            clean_df[col] = clean_df[col].astype(str).apply(lambda n: re.sub(r'\s+', ' ', n.strip()) if pd.notna(n) else n)
            clean_df[col] = clean_df[col].replace(['nan', 'None', 'null'], np.nan)
            player_names_cleaned += int((orig != clean_df[col]).sum())

    # 4. Standardize Numeric Columns & Coordinates
    coord_cols = ['pitchX', 'pitchY', 'stumpsX', 'stumpsY', 'fieldX', 'fieldY', 'ballSpeed']
    for col in coord_cols:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].replace(['NA', 'na', -1, '-1', ''], np.nan)
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')

    run_cols = ['runs', 'batterRuns', 'bowlerRuns', 'extras']
    missing_numeric_fixed = 0
    for col in run_cols:
        if col in clean_df.columns:
            missing_numeric_fixed += clean_df[col].isna().sum()
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0)

    # 5. Standardize Dismissal Details
    if 'dismissalDetails' in clean_df.columns:
        clean_df['dismissalDetails'] = clean_df['dismissalDetails'].astype(str).str.strip().str.lower()
        clean_df['dismissalDetails'] = clean_df['dismissalDetails'].replace(['nan', 'none', 'null', ''], np.nan)

    # 6. Standardize Team Names
    clean_df, teams_standardized_count = clean_teams(clean_df)

    # 6. Validation Checks
    validation_checks = {
        'no_duplicate_deliveries': bool(clean_df.duplicated(subset=['matchId', 'delivery']).sum() == 0) if 'delivery' in clean_df.columns else True,
        'no_null_players': bool(clean_df['batter'].isna().sum() == 0 and clean_df['bowler'].isna().sum() == 0),
        'valid_coordinates': bool(clean_df['pitchX'].notna().sum() > 0)
    }

    report = {
        'dataset_name': 'Hawk-Eye Real IPL Dataset (hawkeye_mens_ipl.csv)',
        'original_rows': original_rows,
        'cleaned_rows': len(clean_df),
        'rows_removed_total': original_rows - len(clean_df),
        'duplicates_removed': int(duplicates_removed),
        'rows_removed_missing_essential': int(missing_essential_drop),
        'player_names_cleaned': int(player_names_cleaned),
        'missing_numeric_fixed': int(missing_numeric_fixed),
        'validation_checks': validation_checks
    }
    return clean_df, report


def clean_hawkeye_simulated_dataset(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean and standardize simulated Hawk-Eye dataset (hawkeye_simulated_2022_2026.csv).
    """
    original_rows = len(df_raw)
    clean_df = df_raw.copy()

    # 1. Essential columns check
    clean_df = clean_df.dropna(subset=['matchId', 'batter', 'bowler'])
    missing_essential_drop = original_rows - len(clean_df)

    # 2. Super Overs check (keep innings 1 & 2)
    initial_count = len(clean_df)
    if 'innings' in clean_df.columns:
        clean_df['innings'] = pd.to_numeric(clean_df['innings'], errors='coerce')
        clean_df = clean_df[clean_df['innings'].isin([1, 2])]
    super_overs_removed = initial_count - len(clean_df)

    # 3. Deduplication
    initial_dups_check = len(clean_df)
    clean_df = clean_df.drop_duplicates()
    if all(c in clean_df.columns for c in ['matchId', 'delivery']):
        clean_df = clean_df.drop_duplicates(subset=['matchId', 'delivery'], keep='first')
    duplicates_removed = initial_dups_check - len(clean_df)

    # 4. Standardize Player Names
    player_cols = ['batter', 'bowler']
    player_names_cleaned = 0
    for col in player_cols:
        if col in clean_df.columns:
            orig = clean_df[col].copy()
            clean_df[col] = clean_df[col].astype(str).apply(lambda n: re.sub(r'\s+', ' ', n.strip()) if pd.notna(n) else n)
            clean_df[col] = clean_df[col].replace(['nan', 'None', 'null'], np.nan)
            player_names_cleaned += int((orig != clean_df[col]).sum())

    # 5. Standardize Numeric Columns & Physics Features
    physics_cols = ['ballSpeed', 'pitchX', 'pitchY', 'stumpsX', 'stumpsY', 'fieldX', 'fieldY', 'swing', 'deviation', 'creaseZ', 'sixDistance']
    for col in physics_cols:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].replace(['NA', 'na', -1, '-1', ''], np.nan)
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')

    run_cols = ['runs', 'extras', 'wicket']
    missing_numeric_fixed = 0
    for col in run_cols:
        if col in clean_df.columns:
            missing_numeric_fixed += clean_df[col].isna().sum()
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0)

    # 6. Standardize Team Names
    clean_df, teams_standardized_count = clean_teams(clean_df)

    # 6. Validation Checks
    validation_checks = {
        'no_duplicate_deliveries': bool(clean_df.duplicated(subset=['matchId', 'delivery']).sum() == 0) if 'delivery' in clean_df.columns else True,
        'no_null_players': bool(clean_df['batter'].isna().sum() == 0 and clean_df['bowler'].isna().sum() == 0),
        'valid_innings_range': bool(clean_df['innings'].isin([1, 2]).all()) if 'innings' in clean_df.columns else True
    }

    report = {
        'dataset_name': 'Hawk-Eye Simulated Dataset (hawkeye_simulated_2022_2026.csv)',
        'original_rows': original_rows,
        'cleaned_rows': len(clean_df),
        'rows_removed_total': original_rows - len(clean_df),
        'duplicates_removed': int(duplicates_removed),
        'rows_removed_missing_essential': int(missing_essential_drop),
        'super_overs_removed': int(super_overs_removed),
        'player_names_cleaned': int(player_names_cleaned),
        'missing_numeric_fixed': int(missing_numeric_fixed),
        'validation_checks': validation_checks
    }
    return clean_df, report


def clean_all_project_datasets(project_dir: str = "."):
    """
    Run data cleaning pipeline across all project datasets:
    - all_ipl_matches.csv / parquet
    - hawkeye_mens_ipl.csv
    - hawkeye_simulated_2022_2026.csv
    Returns a dictionary of cleaned DataFrames and reports.
    """
    from pathlib import Path
    base_path = Path(project_dir)
    results = {}

    # 1. Main Match Dataset
    csv_match = base_path / 'all_ipl_matches.csv'
    if csv_match.exists():
        logging.info("Cleaning all_ipl_matches.csv...")
        raw_df = pd.read_csv(csv_match, low_memory=False)
        clean_df, report = build_clean_dataset(raw_df)
        results['match_dataset'] = (clean_df, report)

    # 2. Real Hawk-Eye Dataset
    hawk_mens = base_path / 'hawkeye_mens_ipl.csv'
    if hawk_mens.exists():
        logging.info("Cleaning hawkeye_mens_ipl.csv...")
        raw_df = pd.read_csv(hawk_mens, low_memory=False)
        clean_df, report = clean_hawkeye_mens_dataset(raw_df)
        results['hawkeye_mens'] = (clean_df, report)

    # 3. Simulated Hawk-Eye Dataset
    hawk_sim = base_path / 'hawkeye_simulated_2022_2026.csv'
    if hawk_sim.exists():
        logging.info("Cleaning hawkeye_simulated_2022_2026.csv...")
        raw_df = pd.read_csv(hawk_sim, low_memory=False)
        clean_df, report = clean_hawkeye_simulated_dataset(raw_df)
        results['hawkeye_simulated'] = (clean_df, report)

    return results


def generate_quality_report(df_raw: pd.DataFrame, clean_df: pd.DataFrame, report: dict) -> str:
    """
    Format Data Quality Report into a professional summary string.
    """
    ds_name = report.get('dataset_name', 'IPL BALL-BY-BALL MATCH DATASET')
    summary = f"""
================================================================================
                    {ds_name.upper()}
================================================================================
📊 DATASET SUMMARY:
   • Original Row Count             : {report['original_rows']:,}
   • Cleaned Row Count              : {report['cleaned_rows']:,}
   • Total Rows Excluded            : {report['rows_removed_total']:,} ({report['rows_removed_total'] / max(report['original_rows'], 1) * 100:.2f}%)

🧹 CLEANING & STANDARDIZATION METRICS:
   • Duplicates Removed             : {report.get('duplicates_removed', 0):,}
   • Missing Essential Rows Removed : {report.get('rows_removed_missing_essential', 0):,}
   • Super Over Deliveries Removed  : {report.get('super_overs_removed', 0):,}
   • Venue Names Standardized       : {report.get('venue_names_standardized', 0):,}
   • Team/Franchise Names Canonicalized: {report.get('team_names_standardized', 0):,}
   • Player Names Normalized        : {report.get('player_names_cleaned', 0):,}
   • Missing Numeric Values Imputed : {report.get('missing_numeric_fixed', 0):,}

✅ VALIDATION CHECKS STATUS:
"""
    for check_name, status in report['validation_checks'].items():
        icon = "PASS [✓]" if status else "FAIL [✗]"
        summary += f"   • {check_name.replace('_', ' ').title():<32}: {icon}\n"
        
    summary += "================================================================================\n"
    return summary

