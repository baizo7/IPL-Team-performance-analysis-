import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_DIR = Path(__file__).parent

IPL_TEAM_COLORS = {
    'Chennai Super Kings': '#F9CD05',
    'Mumbai Indians': '#004BA0',
    'Royal Challengers Bangalore': '#EC1C24',
    'Royal Challengers Bengaluru': '#EC1C24',
    'Kolkata Knight Riders': '#2E0854',
    'Delhi Capitals': '#00008B',
    'Delhi Daredevils': '#00008B',
    'Punjab Kings': '#ED1B24',
    'Kings XI Punjab': '#ED1B24',
    'Rajasthan Royals': '#EA1A85',
    'Sunrisers Hyderabad': '#FF822A',
    'Deccan Chargers': '#00416A',
    'Lucknow Super Giants': '#005087',
    'Gujarat Titans': '#1B2133',
    'Pune Warriors': '#2F9BE3',
    'Rising Pune Supergiant': '#D11D9B',
    'Rising Pune Supergiants': '#D11D9B',
    'Kochi Tuskers Kerala': '#E5A812',
    'Gujarat Lions': '#E04F16',
}


@st.cache_resource(show_spinner="Loading IPL data...")
def load_data():
    path = BASE_DIR / 'all_ipl_matches.parquet'
    csv_path = BASE_DIR / 'all_ipl_matches.csv'

    if path.exists():
        try:
            df = pd.read_parquet(path)
            logging.info(f'Loaded {len(df)} rows from {path.name}')
            return clean_data(df)
        except Exception as e:
            logging.warning(f'Parquet load failed: {e}')

    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, low_memory=False)
            logging.info(f'Loaded {len(df)} rows from {csv_path.name}')
            return clean_data(df)
        except Exception as e:
            logging.warning(f'CSV load failed: {e}')

    # Fall back to building from raw CSVs
    data_dir = BASE_DIR / 'ipl_data'
    if data_dir.exists():
        all_files = sorted(data_dir.glob('[0-9]*.csv'))
        info_files = {f.stem for f in data_dir.glob('*_info.csv')}
        match_files = [f for f in all_files if f.stem not in info_files]

        if match_files:
            dfs = []
            for f in match_files:
                try:
                    df_chunk = pd.read_csv(f, on_bad_lines='skip', encoding='utf-8')
                    if not df_chunk.empty:
                        dfs.append(df_chunk)
                except Exception as e:
                    logging.warning(f'Skipping {f.name}: {e}')

            if dfs:
                df = pd.concat(dfs, axis=0, ignore_index=True)
                logging.info(f'Built dataset from {len(match_files)} files ({len(df)} rows)')
                return clean_data(df)

    st.warning('No real IPL data found. Using sample data for demonstration.')
    return create_sample_data()


def create_sample_data():
    teams = ['Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore',
             'Kolkata Knight Riders', 'Delhi Capitals']
    n_records = 2500
    bowlers = ['B Kumar', 'J Bumrah', 'R Ashwin', 'Y Chahal', 'K Rabada',
               'A Zampa', 'R Jadeja', 'S Narine', 'P Cummins', 'T Boult']
    df = pd.DataFrame({
        'match_id': np.repeat(range(1, 26), 100),
        'batting_team': np.random.choice(teams, n_records),
        'bowling_team': np.random.choice(teams, n_records),
        'ball': np.tile(np.arange(0.1, 20.1, 0.1), n_records // 200 + 1)[:n_records],
        'runs_off_bat': np.random.choice([0, 1, 2, 3, 4, 6], n_records, p=[0.55, 0.15, 0.05, 0.02, 0.15, 0.08]),
        'extras': np.random.choice([0, 0, 0, 1], n_records, p=[0.9, 0.05, 0.03, 0.02]),
        'is_wicket': np.random.choice([0, 1], n_records, p=[0.96, 0.04]),
        'batter': np.random.choice(['V Kohli', 'R Sharma', 'S Dhawan', 'D Warner', 'K Williamson'], n_records),
        'bowler': np.random.choice(bowlers, n_records),
        'bowler_type': np.random.choice(['Right-Arm Fast', 'Right-Arm Seam', 'Right-Arm Leg Spin',
                                         'Left-Arm Orthodox', 'Right-Arm Off Spin'], n_records),
        'season': np.random.choice(['2020', '2021', '2022', '2023', '2024'], n_records),
    })
    df['total_runs'] = df['runs_off_bat'] + df['extras']
    df['over'] = df['ball'].astype(int) + 1
    df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21],
                          labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)'])
    return df


from ipl_data_cleaner import build_clean_dataset, generate_quality_report

def clean_data(df):
    clean_df, report = build_clean_dataset(df)

    # Column mappings fallback for legacy views
    if 'batter' not in clean_df.columns and 'striker' in clean_df.columns:
        clean_df['batter'] = clean_df['striker']

    clean_df['phase'] = pd.cut(clean_df['over'], bins=[0, 6, 15, 21],
                                labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)'])

    # bowler_type from pre-joined data or build it
    if 'bowler_type' not in clean_df.columns or clean_df['bowler_type'].isna().all():
        if 'bowler' in clean_df.columns:
            clean_df['bowler_type'] = clean_df['bowler'].apply(_guess_bowler_type)
        else:
            clean_df['bowler_type'] = 'Unknown'

    # Convert string columns to category for 10x fast Pandas filtering & 80% RAM savings
    cat_cols = ['batting_team', 'bowling_team', 'phase', 'venue', 'season', 'bowler_type']
    for col in cat_cols:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].astype('category')

    logging.info(generate_quality_report(df, clean_df, report))
    return clean_df


_BOWLER_STYLES_CACHE = None

def _guess_bowler_type(bowler_name):
    global _BOWLER_STYLES_CACHE
    if pd.isna(bowler_name):
        return 'Unknown'
    name = str(bowler_name).strip()

    if _BOWLER_STYLES_CACHE is None:
        json_file = BASE_DIR / 'hawkeye_bowler_styles.json'
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _BOWLER_STYLES_CACHE = data.get('manual', {})
            except Exception:
                _BOWLER_STYLES_CACHE = {}
        else:
            _BOWLER_STYLES_CACHE = {}

    if name in _BOWLER_STYLES_CACHE:
        return _BOWLER_STYLES_CACHE[name]

    lower_name = name.lower()
    for k, v in _BOWLER_STYLES_CACHE.items():
        if k.lower() == lower_name:
            return v

    left_arm_pacers = ['boult', 'arshdeep', 'natarajan', 'mustafizur', 'curran', 'starc',
                       'khaleel', 'sakariya', 'mukesh choudhary', 'dayal', 'mohsin khan']
    left_arm_wrist = ['kuldeep yadav', 'noor ahmad', 'tabraiz shamsi']
    left_arm_orthodox = ['jadeja', 'axar', 'krunal', 'shahbaz', 'santner', 'sai kishore']
    right_arm_leg = ['rashid', 'chahal', 'bishnoi', 'hasaranga', 'zampa', 'varun',
                     'mishra', 'warne', 'kumble', 'chawla']
    right_arm_off = ['ashwin', 'narine', 'chakravarthy', 'theekshana', 'livingstone',
                     'potter', 'parnes', 'washington sundar', 'moeen', 'harbhajan']

    if any(p in lower_name for p in left_arm_pacers):
        return 'Left-Arm Pace'
    if any(p in lower_name for p in left_arm_wrist):
        return 'Left-Arm Wrist Spin'
    if any(p in lower_name for p in left_arm_orthodox):
        return 'Left-Arm Orthodox'
    if any(p in lower_name for p in right_arm_leg):
        return 'Right-Arm Leg Spin'
    if any(p in lower_name for p in right_arm_off):
        return 'Right-Arm Off Spin'
    return 'Right-Arm Pace'
