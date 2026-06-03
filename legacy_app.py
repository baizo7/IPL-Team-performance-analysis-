import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import uuid
import hashlib
import altair as alt
import streamlit.components.v1 as components
import tempfile

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
    'Gujarat Lions': '#E04F16'
}

@st.cache_data
def load_data():
    """Load and clean IPL data"""
    path = "ipl_data"
    csv_file = "all_ipl_matches.csv"
    
    # Check if processed file exists
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, low_memory=False)
    else:
        # Logic to load from folder or create sample
        if not os.path.exists(path):
            return create_sample_data()
            
        else:
            all_files = glob.glob(os.path.join(path, "*.csv"))
            if not all_files:
                return create_sample_data()
                
            df_list = []
            for filename in all_files:
                try:
                    df = pd.read_csv(filename, index_col=None, header=0, on_bad_lines='skip', encoding='utf-8')
                    if not df.empty:
                        df_list.append(df)
                except:
                    continue
            final_df = pd.concat(df_list, axis=0, ignore_index=True)
            df = final_df

    return clean_data(df)

def create_sample_data():
    # Fallback sample data generator
    teams = ['Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore', 'Kolkata Knight Riders']
    n_records = 1000
    df = pd.DataFrame({
        'match_id': np.repeat(range(1, 11), 100),
        'batting_team': np.random.choice(teams, n_records),
        'bowling_team': np.random.choice(teams, n_records),
        'ball': np.tile(np.arange(0.1, 20.1, 0.1), n_records // 200 + 1)[:n_records],
        'runs_off_bat': np.random.choice([0, 1, 4, 6], n_records),
        'extras': 0,
        'wicket_type': np.random.choice([None, 'caught'], n_records, p=[0.95, 0.05]),
        'batter': 'Sample Batter',
        'bowler': 'Sample Bowler'
    })
    return clean_data(df)

def clean_data(df):
    df = df.copy()
    
    # Column mapping
    column_mappings = {
        'runs_off_bat': ['runs_off_bat', 'batsman_runs', 'runs_scored'],
        'extras': ['extras', 'extra_runs'],
        'wicket_type': ['wicket_type', 'dismissal_kind', 'wicket_kind'],
        'batter': ['batter', 'batsman', 'striker'],
        'bowler': ['bowler', 'bowler_name'],
        'ball': ['ball', 'over_ball'],
        'batting_team': ['batting_team', 'team'],
        'bowling_team': ['bowling_team', 'opponent']
    }
    
    for standard_name, variations in column_mappings.items():
        for var in variations:
            if var in df.columns and standard_name not in df.columns:
                df.rename(columns={var: standard_name}, inplace=True)
                break
                
    # Basic columns
    if 'ball' in df.columns:
        df['ball'] = pd.to_numeric(df['ball'], errors='coerce').fillna(0)
        df['over'] = df['ball'].astype(int) + 1
    elif 'over' in df.columns:
        df['over'] = pd.to_numeric(df['over'], errors='coerce').fillna(1).astype(int)
    else:
        df['over'] = 1
        
    # Runs
    if 'runs_off_bat' in df.columns and 'extras' in df.columns:
        df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
        df['extras'] = pd.to_numeric(df['extras'], errors='coerce').fillna(0)
        df['total_runs'] = df['runs_off_bat'] + df['extras']
    elif 'runs_off_bat' in df.columns:
        df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
        df['total_runs'] = df['runs_off_bat']
    else:
        df['total_runs'] = 0
        
    # Phase
    df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21], labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)'])
    
    # Wickets
    if 'wicket_type' in df.columns:
        df['is_wicket'] = df['wicket_type'].notna().astype(int)
    else:
        df['is_wicket'] = 0
        
    # Bowler types
    if 'bowler' in df.columns:
        def get_bowler_type(bowler_name):
            if pd.isna(bowler_name): return 'Unknown'
            name = str(bowler_name).lower()
            
            left_arm_pacers = ['boult', 'arshdeep', 'natarajan', 'mustafizur', 'curran', 'starc']
            left_arm_wrist = ['kuldeep yadav', 'noor ahmad', 'tabraiz shamsi']
            left_arm_orthodox = ['jadeja', 'axar', 'krunal', 'shahbaz', 'santner']
            right_arm_leg = ['rashid', 'chahal', 'bishnoi', 'hasaranga', 'zampa']
            right_arm_off = ['ashwin', 'narine', 'chakravarthy', 'theekshana', 'livingstone']
            
            if any(p in name for p in left_arm_pacers):
                return 'Left-Arm Pace'
            elif any(p in name for p in left_arm_wrist):
                return 'Left-Arm Wrist Spin'
            elif any(p in name for p in left_arm_orthodox):
                return 'Left-Arm Orthodox'
            elif any(p in name for p in right_arm_leg):
                return 'Right-Arm Leg Spin'
            elif any(p in name for p in right_arm_off):
                return 'Right-Arm Off Spin'
            else:
                return 'Right-Arm Pace'

        df['bowler_type'] = df['bowler'].apply(get_bowler_type)
    else:
        df['bowler_type'] = 'Unknown'
        
    # Fill NaNs
    for col in ['batting_team', 'bowling_team', 'batter', 'bowler']:
        if col in df.columns: df[col] = df[col].fillna('Unknown')
        
    return df


def render_legacy():
    if not st.session_state.get("authenticated", False):
        st.switch_page("pages/1_Login.py")
        st.stop()
        
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    /* === Base === */
    .main .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:100%}
    .stApp{font-family:'Inter',sans-serif;background:#030712}
    /* === Static Grid bg (Animation removed for performance) === */
    .stApp::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(102,126,234,.05)1px,transparent 1px),linear-gradient(90deg,rgba(102,126,234,.05)1px,transparent 1px);background-size:50px 50px;pointer-events:none;z-index:0}
    /* === Headers === */
    h1{font-family:'Orbitron',monospace!important;background:linear-gradient(135deg,#667eea 0%,#f093fb 50%,#f5576c 100%)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important;font-weight:900!important;letter-spacing:1px!important;font-size:2rem!important}
    h2{color:#e2e8f0;font-weight:700;border-bottom:1px solid rgba(102,126,234,.3);padding-bottom:.5rem;margin-top:1.5rem}
    h3{color:#cbd5e1;font-weight:600}
    /* === Metric Cards (glassmorphism) === */
    [data-testid="stMetric"]{background:rgba(15,23,42,.75)!important;backdrop-filter:blur(16px)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:16px!important;padding:1.2rem!important;box-shadow:0 4px 24px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.05)!important;transition:all .3s ease!important}
    [data-testid="stMetric"]:hover{border-color:rgba(102,126,234,.45)!important;box-shadow:0 8px 32px rgba(102,126,234,.15)!important;transform:translateY(-2px)!important}
    [data-testid="stMetricValue"]{font-family:'Orbitron',monospace!important;font-size:1.9rem!important;font-weight:800!important;background:linear-gradient(135deg,#667eea,#f093fb)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important}
    [data-testid="stMetricLabel"]{font-weight:600!important;text-transform:uppercase!important;letter-spacing:.8px!important;font-size:.72rem!important;color:rgba(148,163,184,.8)!important}
    /* === Column cards === */
    [data-testid="column"]{border-radius:16px;padding:1.2rem;background:rgba(15,23,42,.6);backdrop-filter:blur(12px);border:1px solid rgba(102,126,234,.12);box-shadow:0 4px 20px rgba(0,0,0,.2);transition:all .3s ease}
    [data-testid="column"]:hover{border-color:rgba(102,126,234,.3);box-shadow:0 8px 32px rgba(102,126,234,.1)}
    /* === Buttons === */
    .stButton>button{border-radius:10px!important;font-weight:600!important;background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;border:none!important;padding:.6rem 1.5rem!important;transition:all .3s cubic-bezier(.4,0,.2,1)!important;box-shadow:0 4px 15px rgba(102,126,234,.3)!important}
    .stButton>button:hover{transform:translateY(-3px)!important;box-shadow:0 8px 25px rgba(102,126,234,.5)!important}
    /* === Tabs (futuristic pill style) === */
    .stTabs [data-baseweb="tab-list"]{gap:4px;background:rgba(15,23,42,.8);padding:5px;border-radius:14px;border:1px solid rgba(102,126,234,.15);backdrop-filter:blur(12px)}
    .stTabs [data-baseweb="tab"]{border-radius:10px;padding:10px 22px;font-weight:600;transition:all .3s ease;color:rgba(148,163,184,.75)!important;font-size:.85rem}
    .stTabs [data-baseweb="tab"]:hover{background:rgba(102,126,234,.12)!important;color:#c4b5fd!important}
    .stTabs [data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,rgba(102,126,234,.3),rgba(118,75,162,.3))!important;color:#c4b5fd!important;box-shadow:0 0 12px rgba(102,126,234,.2)!important}
    /* === Sidebar === */
    section[data-testid="stSidebar"]{background:rgba(15,23,42,.95)!important;border-right:1px solid rgba(102,126,234,.18)!important;backdrop-filter:blur(20px)!important}
    section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#e2e8f0;border:none;font-family:'Inter',sans-serif!important}
    .stSidebar [data-testid="stSelectbox"]>div>div{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important}
    /* === Inputs === */
    .stSelectbox>div>div,.stMultiSelect>div>div{border-radius:10px!important}
    .stTextInput>div>div>input{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important;color:#f1f5f9!important}
    /* === DataFrames === */
    .stDataFrame{border-radius:12px;overflow:hidden;border:1px solid rgba(102,126,234,.15)!important}
    /* === Alert boxes === */
    .stAlert{border-radius:12px;backdrop-filter:blur(8px)}
    /* === Dividers === */
    hr{margin:2.5rem 0;border:none;height:1px;background:linear-gradient(90deg,transparent,rgba(102,126,234,.4),transparent)}
    /* === Spinner === */
    .stSpinner>div{border-color:rgba(102,126,234,.8) transparent transparent!important}
    /* === Scrollbar === */
    ::-webkit-scrollbar{width:6px;height:6px}
    ::-webkit-scrollbar-track{background:rgba(15,23,42,.5)}
    ::-webkit-scrollbar-thumb{background:rgba(102,126,234,.4);border-radius:3px}
    ::-webkit-scrollbar-thumb:hover{background:rgba(102,126,234,.7)}
    /* === Fade-in animation === */
    @keyframes fadeInUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
    .element-container{animation:fadeInUp .35s ease-out}
    /* === Top nav bar === */
    .top-nav{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;background:rgba(15,23,42,.9);backdrop-filter:blur(20px);border-bottom:1px solid rgba(102,126,234,.2);margin-bottom:20px;border-radius:0 0 16px 16px;position:sticky;top:0;z-index:999}
    .nav-brand{font-family:'Orbitron',monospace;font-size:18px;font-weight:900;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:2px}
    .nav-user{font-size:13px;color:rgba(148,163,184,.8);background:rgba(102,126,234,.12);border:1px solid rgba(102,126,234,.2);padding:6px 14px;border-radius:20px;font-weight:600}
    .nav-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;margin-right:6px;box-shadow:0 0 8px #22c55e;animation:blink 2s ease-in-out infinite}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
    /* === Section title badge === */
    .section-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(102,126,234,.12);border:1px solid rgba(102,126,234,.25);border-radius:8px;padding:6px 14px;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#818cf8;margin-bottom:12px}
    html{scroll-behavior:smooth}
    </style>
    """, unsafe_allow_html=True)
    
    
    
    # -----------------------------------------------------------------------------
    # 1. Data Loading and Cleaning
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------------------
    # 2. Analysis Functions
    # -----------------------------------------------------------------------------
    
    def calculate_run_rate_by_phase(df, team):
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
    
    def calculate_player_matchup(df, player, bowler_type):
        player_data = df[(df['batter'] == player) & (df['bowler_type'] == bowler_type)]
        if len(player_data) == 0: return None
        
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
    
    def get_top_batters(df, team, n=5):
        team_data = df[df['batting_team'] == team]
        stats = team_data.groupby('batter').agg({
            'runs_off_bat': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        stats = stats[stats['ball'] >= 30].sort_values('runs_off_bat', ascending=False).head(n)
        return stats
    
    def generate_pitch_map_data(df, team=None, bowler_type=None, phase=None):
        """Generate pitch map data with ball positions — vectorized for performance"""
        filtered_df = df.copy()
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if bowler_type and bowler_type != 'All Types':
            filtered_df = filtered_df[filtered_df['bowler_type'] == bowler_type]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        if len(filtered_df) == 0:
            return []
        if len(filtered_df) > 500:
            filtered_df = filtered_df.sample(500, random_state=42)
        
        n = len(filtered_df)
        rng = np.random.RandomState(42)
        
        runs = pd.to_numeric(filtered_df['runs_off_bat'], errors='coerce').fillna(0).astype(int).values
        wickets = filtered_df['is_wicket'].values.astype(int)
        batters = filtered_df['batter'].astype(str).values
        bowlers = filtered_df['bowler'].astype(str).values
        
        # Vectorized position generation
        x = np.zeros(n, dtype=float)
        y = np.zeros(n, dtype=float)
        colors = np.empty(n, dtype=object)
        sizes = np.zeros(n, dtype=int)
        
        is_w = wickets == 1
        is_six = (~is_w) & (runs >= 6)
        is_four = (~is_w) & (~is_six) & (runs == 4)
        is_running = (~is_w) & (~is_six) & (~is_four) & np.isin(runs, [1, 2, 3])
        is_dot = ~(is_w | is_six | is_four | is_running)
        
        # Wickets
        m = is_w.sum()
        if m: x[is_w] = rng.normal(0.3, 0.4, m); y[is_w] = rng.normal(8, 2, m); colors[is_w] = 'red'; sizes[is_w] = 12
        # Sixes
        m = is_six.sum()
        if m:
            choice = rng.choice([0, 1], m)
            y[is_six] = np.where(choice == 0, rng.normal(4, 2, m), rng.normal(18, 2, m))
            x[is_six] = rng.normal(0, 0.6, m); colors[is_six] = 'purple'; sizes[is_six] = 14
        # Fours
        m = is_four.sum()
        if m: x[is_four] = rng.normal(0, 0.7, m); y[is_four] = rng.normal(10, 4, m); colors[is_four] = 'green'; sizes[is_four] = 10
        # Running (1-3)
        m = is_running.sum()
        if m: x[is_running] = rng.normal(0, 0.5, m); y[is_running] = rng.normal(9, 3, m); colors[is_running] = 'blue'; sizes[is_running] = 6
        # Dots
        m = is_dot.sum()
        if m: x[is_dot] = rng.normal(0.2, 0.4, m); y[is_dot] = rng.normal(8, 2.5, m); colors[is_dot] = 'gray'; sizes[is_dot] = 4
        
        x = np.clip(x, -1.2, 1.2)
        y = np.clip(y, 0, 22)
        
        return [{'x': float(x[i]), 'y': float(y[i]), 'runs': int(runs[i]), 'wicket': int(wickets[i]),
                 'color': colors[i], 'size': int(sizes[i]), 'batter': batters[i], 'bowler': bowlers[i]} for i in range(n)]
    
    def generate_pitch_map_data_complete(df, team=None, bowler_type=None, phase=None):
        """Generate complete pitch map data with ball positions"""
        import numpy as np
        
        # Filter data
        filtered_df = df.copy()
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if bowler_type and bowler_type != 'All Types':
            filtered_df = filtered_df[filtered_df['bowler_type'] == bowler_type]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        # Sample data if too large (for performance — multi-panel renders 4 canvases)
        if len(filtered_df) > 200:
            filtered_df = filtered_df.sample(200, random_state=42)
        
        # Generate synthetic pitch positions
        np.random.seed(42)
        
        pitch_data = []
        for idx, row in filtered_df.iterrows():
            # Simulate pitch position based on outcome
            # X: -1 to 1 (left to right from bowler's perspective)
            # Y: 0 to 22 (pitch length in yards, 0 = bowler end, 22 = batter end)
            
            runs = row.get('runs_off_bat', 0)
            is_wicket = row.get('is_wicket', 0)
            
            # Good length balls (Y: 6-10 yards)
            # Short balls (Y: 0-6 yards)  
            # Full balls (Y: 10-16 yards)
            # Very full/yorkers (Y: 16-22 yards)
            
            if is_wicket:
                # Wicket balls tend to be good length, on or around off stump
                y = np.random.normal(8, 2)
                x = np.random.normal(0.3, 0.4)  # Around off stump
                color = 'red'
                size = 6
            elif runs >= 6:
                # Sixes - often short or very full
                y = np.random.choice([np.random.normal(4, 2), np.random.normal(18, 2)])
                x = np.random.normal(0, 0.6)
                color = 'purple'
                size = 7
            elif runs == 4:
                # Fours - various lengths
                y = np.random.normal(10, 4)
                x = np.random.normal(0, 0.7)
                color = 'green'
                size = 5
            elif runs in [1, 2, 3]:
                # Singles/doubles - good length
                y = np.random.normal(9, 3)
                x = np.random.normal(0, 0.5)
                color = 'blue'
                size = 3
            else:
                # Dot balls - good line and length
                y = np.random.normal(8, 2.5)
                x = np.random.normal(0.2, 0.4)
                color = 'gray'
                size = 2
            
            # Clamp values to pitch boundaries
            x = max(-1.2, min(1.2, x))
            y = max(0, min(22, y))
            
            pitch_data.append({
                'x': float(x),
                'y': float(y),
                'runs': int(runs),
                'wicket': int(is_wicket),
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return pitch_data
    
    def generate_wagon_wheel_data(df, team=None, batter=None, phase=None):
        """Generate accurate wagon wheel (shot direction) data based on ball position"""
        import numpy as np
        
        filtered_df = df.copy()
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if batter:
            filtered_df = filtered_df[filtered_df['batter'] == batter]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        filtered_df = filtered_df[filtered_df['runs_off_bat'] > 0]
        
        if len(filtered_df) > 300:
            filtered_df = filtered_df.sample(300, random_state=42)
        
        np.random.seed(42)
        wagon_data = []
        
        for idx, row in filtered_df.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            
            # Determine shot zone based on runs and add realistic variation
            if runs == 6:
                # Sixes - long distances (65-95m), wider angle distribution
                angle = float(np.random.choice([
                    np.random.uniform(-90, -45),   # Square leg/Fine leg
                    np.random.uniform(-45, 0),     # Mid-wicket
                    np.random.uniform(0, 45),      # Long-on/Straight
                    np.random.uniform(45, 90),     # Long-off/Extra cover
                    np.random.uniform(90, 135),    # Cover/Point
                    np.random.uniform(135, 180),   # Third man/Backward point
                ]))
                distance = float(np.random.uniform(65, 95))
                color = 'red'
                size = 14
                
            elif runs == 4:
                # Fours - medium-long distances (50-70m), all around ground
                angle = float(np.random.choice([
                    np.random.uniform(-135, -90),  # Fine leg
                    np.random.uniform(-90, -45),   # Square leg
                    np.random.uniform(-45, 0),     # Mid-wicket
                    np.random.uniform(0, 30),      # Straight/Mid-on
                    np.random.uniform(30, 60),     # Long-off
                    np.random.uniform(60, 120),    # Extra cover/Cover
                    np.random.uniform(120, 180),   # Point/Third man
                ]))
                distance = float(np.random.uniform(50, 70))
                color = 'red'  # Boundaries in red
                size = 11
                
            elif runs == 3:
                # Threes - medium distances (40-55m), good running
                angle = float(np.random.uniform(-120, 150))
                distance = float(np.random.uniform(40, 55))
                color = 'blue'
                size = 8
                
            elif runs == 2:
                # Twos - medium distances (30-50m)
                angle = float(np.random.uniform(-135, 135))
                distance = float(np.random.uniform(30, 50))
                color = 'orange'
                size = 7
                
            else:  # runs == 1
                # Singles - shorter distances (20-40m), all around
                angle = float(np.random.uniform(-180, 180))
                distance = float(np.random.uniform(20, 40))
                color = 'green'
                size = 6
            
            # Convert polar to cartesian coordinates
            rad = np.radians(angle)
            x = float(distance * np.sin(rad))  # Changed to sin for proper mapping
            y = float(distance * np.cos(rad))  # Changed to cos for proper mapping
            
            wagon_data.append({
                'x': x,
                'y': y,
                'angle': angle,
                'distance': distance,
                'runs': runs,
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return wagon_data
    
    def generate_stumps_view_data(df, team=None, phase=None):
        """Generate stumps view (behind bowler) data"""
        import numpy as np
        
        filtered_df = df.copy()
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        if len(filtered_df) > 400:
            filtered_df = filtered_df.sample(400, random_state=42)
        
        np.random.seed(42)
        stumps_data = []
        
        for idx, row in filtered_df.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            is_wicket = int(row.get('is_wicket', 0))
            
            if is_wicket:
                x = float(np.random.normal(0, 0.5))
                y = float(np.random.normal(1.5, 0.4))
                color = 'red'
                size = 6
            elif runs >= 6:
                x = float(np.random.normal(0, 0.7))
                y = float(np.random.choice([np.random.normal(2.2, 0.3), np.random.normal(0.8, 0.3)]))
                color = 'purple'
                size = 7
            elif runs == 4:
                x = float(np.random.normal(0, 0.9))
                y = float(np.random.normal(1.5, 0.5))
                color = 'green'
                size = 5
            elif runs in [1, 2, 3]:
                x = float(np.random.normal(0, 0.6))
                y = float(np.random.normal(1.5, 0.4))
                color = 'blue'
                size = 3
            else:
                x = float(np.random.normal(0, 0.4))
                y = float(np.random.normal(1.5, 0.3))
                color = 'gray'
                size = 2
            
            x = max(-2.5, min(2.5, x))
            y = max(0.2, min(2.8, y))
            
            stumps_data.append({
                'x': x,
                'y': y,
                'runs': runs,
                'wicket': is_wicket,
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return stumps_data
    
    def get_player_statistics(df, team, phase=None):
        """Get comprehensive player statistics"""
        team_data = df[df['batting_team'] == team].copy()
        
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        batter_stats = team_data.groupby('batter').agg({
            'runs_off_bat': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        
        batter_stats = batter_stats[batter_stats['ball'] >= 30]
        batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(2)
        batter_stats['average'] = (batter_stats['runs_off_bat'] / batter_stats['is_wicket'].replace(0, 1)).round(2)
        
        fours_sixes = team_data[team_data['runs_off_bat'].isin([4, 6])].groupby(['batter', 'runs_off_bat']).size().unstack(fill_value=0)
        if 4 in fours_sixes.columns:
            batter_stats = batter_stats.merge(fours_sixes[[4]].rename(columns={4: 'fours'}), left_on='batter', right_index=True, how='left')
        else:
            batter_stats['fours'] = 0
        if 6 in fours_sixes.columns:
            batter_stats = batter_stats.merge(fours_sixes[[6]].rename(columns={6: 'sixes'}), left_on='batter', right_index=True, how='left')
        else:
            batter_stats['sixes'] = 0
        
        batter_stats['fours'] = batter_stats['fours'].fillna(0).astype(int)
        batter_stats['sixes'] = batter_stats['sixes'].fillna(0).astype(int)
        
        # Calculate highest score per player (per innings)
        innings_scores = team_data.groupby(['batter', 'match_id'])['runs_off_bat'].sum().reset_index()
        highest_scores = innings_scores.groupby('batter')['runs_off_bat'].max().reset_index()
        highest_scores.columns = ['batter', 'highest_score']
        batter_stats = batter_stats.merge(highest_scores, on='batter', how='left')
        batter_stats['highest_score'] = batter_stats['highest_score'].fillna(0).astype(int)
        
        batter_stats = batter_stats.sort_values('runs_off_bat', ascending=False).head(10)
        
        return batter_stats
    
    # -----------------------------------------------------------------------------
    # Altair Statistical Visualizations
    # -----------------------------------------------------------------------------
    
    def create_runs_distribution_chart(df, team, phase=None):
        """Create comprehensive runs distribution analysis from scratch using Plotly"""
        import plotly.graph_objects as go
        
        # Filter data for batting team
        team_data = df[df['batting_team'] == team].copy()
        
        # Apply phase filter if specified
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        # Check if we have data
        if len(team_data) == 0:
            return None
        
        # Calculate runs distribution statistics
        runs_counts = team_data['runs_off_bat'].value_counts().reset_index()
        runs_counts.columns = ['runs', 'count']
        runs_counts = runs_counts.sort_values('runs')
        
        # Calculate percentages
        total_balls = len(team_data)
        runs_counts['percentage'] = ((runs_counts['count'] / total_balls) * 100).round(1)
        
        # Add cumulative percentage
        runs_counts['cumulative_pct'] = runs_counts['percentage'].cumsum().round(1)
        
        team_color = IPL_TEAM_COLORS.get(team, '#3b82f6')
        hex_c = team_color.lstrip('#')
        if len(hex_c) == 6:
            r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
        else:
            r, g, b = 59, 130, 246
            
        color_map = {
            0: f"rgba({r},{g},{b},0.15)",  # dots
            1: f"rgba({r},{g},{b},0.35)",  # singles
            2: f"rgba({r},{g},{b},0.55)",  # twos
            3: f"rgba({r},{g},{b},0.70)",  # threes
            4: f"rgba({r},{g},{b},0.85)",  # fours
            6: f"rgba({r},{g},{b},1.0)",   # sixes
        }
        
        label_map = {
            0: 'Dot Balls', 1: 'Singles', 2: 'Twos', 
            3: 'Threes', 4: 'Fours', 6: 'Sixes'
        }
        
        runs_counts['color'] = runs_counts['runs'].map(lambda x: color_map.get(x, '#fbbf24'))
        runs_counts['label'] = runs_counts['runs'].map(lambda x: label_map.get(x, f'{int(x)} Runs'))
        
        # Calculate summary statistics
        total_runs = int(team_data['runs_off_bat'].sum())
        avg_runs_per_ball = round(total_runs / total_balls, 2) if total_balls > 0 else 0
        dots = int(len(team_data[team_data['runs_off_bat'] == 0]))
        boundaries = int(len(team_data[(team_data['runs_off_bat'] == 4) | (team_data['runs_off_bat'] == 6)]))
        dot_pct = round((dots / total_balls) * 100, 1) if total_balls > 0 else 0
        boundary_pct = round((boundaries / total_balls) * 100, 1) if total_balls > 0 else 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=runs_counts['label'],
            y=runs_counts['count'],
            text=[f"<b>{count}</b><br><span style='font-size:11px;color:#cbd5e1'>{pct}%</span>" for count, pct in zip(runs_counts['count'], runs_counts['percentage'])],
            textposition='auto',
            marker=dict(
                color=runs_counts['color'],
                line=dict(color='rgba(255,255,255,0.3)', width=1.5),
            ),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata}%<extra></extra>",
            customdata=runs_counts['percentage']
        ))
        
        fig.update_layout(
            title=dict(
                text=f"<b>{team}</b><br><span style='font-size:13px;color:#94a3b8'>Total Runs: {total_runs} | Total Balls: {total_balls} | Avg: {avg_runs_per_ball}</span><br><span style='font-size:13px;color:#94a3b8'>Dots: {dot_pct}% | Boundaries: {boundary_pct}%</span>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                showgrid=False,
                title="",
                tickfont=dict(size=12, color='#e2e8f0', weight='bold')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title="Number of Balls",
                tickfont=dict(size=11, color='#94a3b8')
            ),
            margin=dict(t=90, b=40, l=50, r=20),
            showlegend=False,
            height=400,
            hoverlabel=dict(
                bgcolor="rgba(15, 23, 42, 0.9)",
                font_size=13,
                font_family="Segoe UI"
            )
        )
        
        chart = fig
        
        return chart
    
    def create_strike_rate_comparison(df, phase=None):
        """Create strike rate comparison chart for top batters across teams using Plotly"""
        import plotly.graph_objects as go
        if phase:
            data = df[df['phase'] == phase].copy()
        else:
            data = df.copy()
        
        batter_stats = data.groupby(['batter', 'batting_team']).agg({
            'runs_off_bat': 'sum',
            'ball': 'count'
        }).reset_index()
        
        batter_stats = batter_stats[batter_stats['ball'] >= 50]
        batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(2)
        batter_stats = batter_stats.sort_values('strike_rate', ascending=True).tail(15) # Ascending for horizontal bar
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=batter_stats['strike_rate'],
            y=batter_stats['batter'],
            orientation='h',
            text=[f"<b>{sr}</b>" for sr in batter_stats['strike_rate']],
            textposition='auto',
            marker=dict(
                color=[IPL_TEAM_COLORS.get(t, '#3b82f6') for t in batter_stats['batting_team']],
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            hovertemplate="<b>%{y}</b><br>Team: %{customdata[0]}<br>Strike Rate: %{x}<br>Runs: %{customdata[1]}<br>Balls: %{customdata[2]}<extra></extra>",
            customdata=batter_stats[['batting_team', 'runs_off_bat', 'ball']]
        ))
        
        fig.update_layout(
            title=dict(
                text="<b>Top 15 Batters by Strike Rate (min 50 balls)</b>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Strike Rate",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            yaxis=dict(
                title="",
                showgrid=False,
                tickfont=dict(size=12, color='#e2e8f0', weight='bold')
            ),
            margin=dict(t=70, b=40, l=120, r=40),
            showlegend=False,
            height=500,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        return fig
    
    def create_boundary_percentage_chart(df, teams, phase=None):
        """Create comprehensive boundary and dot ball analysis using Plotly"""
        import plotly.graph_objects as go
        import pandas as pd
        results = []
        
        for team in teams:
            team_data = df[df['batting_team'] == team].copy()
            if phase:
                team_data = team_data[team_data['phase'] == phase]
            
            total_balls = len(team_data)
            if total_balls == 0:
                continue
            
            fours = len(team_data[team_data['runs_off_bat'] == 4])
            sixes = len(team_data[team_data['runs_off_bat'] == 6])
            dots = len(team_data[team_data['runs_off_bat'] == 0])
            singles = len(team_data[team_data['runs_off_bat'] == 1])
            twos = len(team_data[team_data['runs_off_bat'] == 2])
            
            results.append({'team': team, 'category': 'Fours (4s)', 'percentage': round((fours/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Sixes (6s)', 'percentage': round((sixes/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Dot Balls', 'percentage': round((dots/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Singles (1s)', 'percentage': round((singles/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Twos (2s)', 'percentage': round((twos/total_balls)*100, 1)})
        
        if len(results) == 0:
            return None
            
        chart_df = pd.DataFrame(results)
        fig = go.Figure()
        
        categories = ['Dot Balls', 'Singles (1s)', 'Twos (2s)', 'Fours (4s)', 'Sixes (6s)']
        colors = [IPL_TEAM_COLORS.get(teams[0], '#3b82f6'), IPL_TEAM_COLORS.get(teams[1], '#f43f5e')] if len(teams) > 1 else ['#3b82f6', '#f43f5e']
        
        for idx, team in enumerate(teams):
            team_df = chart_df[chart_df['team'] == team]
            if len(team_df) == 0: continue
            
            team_df = team_df.set_index('category').reindex(categories).reset_index()
            
            fig.add_trace(go.Bar(
                name=team,
                x=team_df['category'],
                y=team_df['percentage'],
                text=[f"<b>{pct}%</b>" for pct in team_df['percentage']],
                textposition='auto',
                marker=dict(
                    color=colors[idx % len(colors)],
                    line=dict(color='rgba(255,255,255,0.2)', width=1)
                ),
                hovertemplate="<b>%{x}</b><br>Team: " + team + "<br>Percentage: %{y}%<extra></extra>"
            ))
            
        fig.update_layout(
            barmode='group',
            title=dict(
                text="<b>Boundary & Dot Ball Analysis - Team Comparison</b>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="",
                showgrid=False,
                tickfont=dict(size=12, color='#e2e8f0', weight='bold')
            ),
            yaxis=dict(
                title="Percentage of Balls (%)",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=100, b=40, l=50, r=20),
            height=400,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        return fig
    
    def create_runs_over_progression(df, team, phase=None):
        """Create runs progression over overs using Plotly"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        team_data = df[df['batting_team'] == team].copy()
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        over_runs = team_data.groupby('over')['runs_off_bat'].sum().reset_index()
        over_runs['cumulative_runs'] = over_runs['runs_off_bat'].cumsum()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        team_color = IPL_TEAM_COLORS.get(team, '#60a5fa')
        
        # Convert hex to rgba for transparent fill
        if team_color.startswith('#'):
            r, g, b = int(team_color[1:3], 16), int(team_color[3:5], 16), int(team_color[5:7], 16)
            team_color_rgba = f"rgba({r}, {g}, {b}, 0.5)"
        else:
            team_color_rgba = 'rgba(96, 165, 250, 0.5)'
            
        fig.add_trace(
            go.Bar(
                x=over_runs['over'],
                y=over_runs['runs_off_bat'],
                name="Runs per Over",
                marker_color=team_color_rgba,
                marker_line_color=team_color,
                marker_line_width=1.5,
                opacity=0.8
            ),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(
                x=over_runs['over'],
                y=over_runs['cumulative_runs'],
                name="Cumulative Runs",
                mode='lines+markers',
                line=dict(color=team_color, width=3),
                marker=dict(size=8, color=team_color, line=dict(color='white', width=1)),
            ),
            secondary_y=True,
        )
        
        fig.update_layout(
            title=dict(
                text=f"<b>{team} - Runs Progression Over Overs</b>",
                font=dict(size=16, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Over",
                showgrid=False,
                tickmode='linear',
                tick0=0, dtick=1,
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=80, b=40, l=40, r=40),
            height=400,
            hovermode="x unified",
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        
        fig.update_yaxes(title_text="Runs per Over", showgrid=False, secondary_y=False, tickfont=dict(color='#94a3b8'))
        fig.update_yaxes(title_text="Cumulative Runs", showgrid=True, gridcolor='rgba(255,255,255,0.05)', secondary_y=True, tickfont=dict(color='#60a5fa'))
        
        return fig
    
    def create_wicket_timeline(df, bowling_team, phase=None):
        """Create wicket fall timeline/distribution using Plotly"""
        import plotly.graph_objects as go
        
        team_data = df[df['bowling_team'] == bowling_team].copy()
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        wickets = team_data[team_data['is_wicket'] == 1].copy()
        if wickets.empty:
            return None
            
        # Group by over and wicket type
        wicket_counts = wickets.groupby(['over', 'wicket_type']).size().reset_index(name='count')
        
        fig = go.Figure()
        
        # Define a consistent color palette for wicket types
        colors = {
            'caught': '#3b82f6',
            'bowled': '#ef4444',
            'lbw': '#eab308',
            'run out': '#f97316',
            'stumped': '#8b5cf6',
            'caught and bowled': '#10b981',
            'hit wicket': '#ec4899',
            'retired hurt': '#64748b'
        }
        
        for w_type in wicket_counts['wicket_type'].unique():
            w_data = wicket_counts[wicket_counts['wicket_type'] == w_type]
            fig.add_trace(go.Bar(
                x=w_data['over'],
                y=w_data['count'],
                name=w_type,
                marker_color=colors.get(w_type, '#94a3b8'),
                hovertemplate="Over: %{x}<br>Type: " + str(w_type) + "<br>Wickets: %{y}<extra></extra>"
            ))
            
        fig.update_layout(
            barmode='stack',
            title=dict(
                text=f"<b>{bowling_team} - Fall of Wickets Distribution</b>",
                font=dict(size=16, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Over",
                showgrid=False,
                tickmode='linear',
                tick0=0, dtick=1,
                tickfont=dict(size=11, color='#94a3b8')
            ),
            yaxis=dict(
                title="Number of Wickets",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8'),
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=60, b=80, l=40, r=20),
            height=430,
            hovermode="x unified"
        )
        return fig

    def create_bowler_economy_chart(df, team, phase=None):
        """Create comprehensive bowler economy rate analysis from scratch"""
        # Filter data for bowling team
        team_data = df[df['bowling_team'] == team].copy()
        
        # Apply phase filter if specified
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        # Check if we have data
        if len(team_data) == 0:
            return None
        
        # Calculate comprehensive bowling statistics per bowler
        bowler_stats = team_data.groupby('bowler').agg({
            'runs_off_bat': 'sum',
            'extras': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        
        # Calculate additional metrics using direct filtering
        bowler_list = []
        for bowler in bowler_stats['bowler'].unique():
            bowler_balls = team_data[team_data['bowler'] == bowler]
            
            # Count dots (no runs and no extras)
            dots = len(bowler_balls[(bowler_balls['runs_off_bat'] == 0) & (bowler_balls['extras'] == 0)])
            
            # Count boundaries (4s and 6s)
            boundaries = len(bowler_balls[(bowler_balls['runs_off_bat'] == 4) | (bowler_balls['runs_off_bat'] == 6)])
            
            # Count sixes specifically
            sixes = len(bowler_balls[bowler_balls['runs_off_bat'] == 6])
            
            # Count fours specifically
            fours = len(bowler_balls[bowler_balls['runs_off_bat'] == 4])
            
            bowler_list.append({
                'bowler': bowler,
                'dots': dots,
                'boundaries': boundaries,
                'sixes': sixes,
                'fours': fours
            })
        
        # Merge additional statistics
        additional_stats = pd.DataFrame(bowler_list)
        bowler_stats = bowler_stats.merge(additional_stats, on='bowler', how='left')
        
        # Filter bowlers with minimum 24 balls (4 overs)
        bowler_stats = bowler_stats[bowler_stats['ball'] >= 24].copy()
        
        if len(bowler_stats) == 0:
            return None
        
        # Calculate derived metrics
        bowler_stats['overs'] = (bowler_stats['ball'] / 6).round(1)
        bowler_stats['total_runs'] = bowler_stats['runs_off_bat'] + bowler_stats['extras']
        bowler_stats['economy'] = (bowler_stats['total_runs'] / bowler_stats['overs']).round(2)
        
        # Calculate strike rate (balls per wicket)
        bowler_stats['strike_rate'] = bowler_stats.apply(
            lambda x: round(x['ball'] / x['is_wicket'], 1) if x['is_wicket'] > 0 else 999.0, axis=1
        )
        
        # Calculate bowling average (runs per wicket)
        bowler_stats['average'] = bowler_stats.apply(
            lambda x: round(x['total_runs'] / x['is_wicket'], 2) if x['is_wicket'] > 0 else 999.0, axis=1
        )
        
        # Calculate percentages
        bowler_stats['dot_percentage'] = ((bowler_stats['dots'] / bowler_stats['ball']) * 100).round(1)
        bowler_stats['boundary_percentage'] = ((bowler_stats['boundaries'] / bowler_stats['ball']) * 100).round(1)
        
        # Sort by economy rate and select top 12 bowlers
        bowler_stats = bowler_stats.sort_values('economy').head(12)
        
        # Prepare custom label for wickets
        bowler_stats['wicket_text'] = bowler_stats.apply(lambda x: f"🎯 {int(x['is_wicket'])} W | {int(x['dots'])} Dots", axis=1)

        # Create the base chart
        base = alt.Chart(bowler_stats).encode(
            y=alt.Y('bowler:N', 
                    sort=alt.EncodingSortField(field='economy', order='ascending'),
                    title='Bowler',
                    axis=alt.Axis(labelLimit=200, labelFontSize=12, labelColor='#e2e8f0', titleColor='#e2e8f0', grid=False, domainColor='rgba(255,255,255,0.1)'))
        )
        
        # Create horizontal bars with team color
        team_color = IPL_TEAM_COLORS.get(team, '#3b82f6')
        
        bars = base.mark_bar(
            cornerRadiusBottomRight=8,
            cornerRadiusTopRight=8,
            size=28,
            opacity=0.9,
            color=team_color
        ).encode(
            x=alt.X('economy:Q', 
                    title='Economy Rate (Runs per Over)', 
                    axis=alt.Axis(labelColor='#94a3b8', titleColor='#e2e8f0', gridColor='rgba(255,255,255,0.05)', domainColor='rgba(255,255,255,0.1)'),
                    scale=alt.Scale(domain=[0, max(15, bowler_stats['economy'].max() + 1)])),
            tooltip=[
                alt.Tooltip('bowler:N', title='🏏 Bowler'),
                alt.Tooltip('economy:Q', title='💰 Economy', format='.2f'),
                alt.Tooltip('is_wicket:Q', title='🎯 Wickets'),
                alt.Tooltip('average:Q', title='📊 Average', format='.2f'),
                alt.Tooltip('strike_rate:Q', title='⚡ Strike Rate', format='.1f'),
                alt.Tooltip('overs:Q', title='⏱️ Overs', format='.1f'),
                alt.Tooltip('total_runs:Q', title='🏃 Runs Conceded'),
                alt.Tooltip('dot_percentage:Q', title='⚫ Dot %', format='.1f'),
                alt.Tooltip('boundary_percentage:Q', title='🔴 Boundary %', format='.1f'),
                alt.Tooltip('fours:Q', title='4️⃣ Fours'),
                alt.Tooltip('sixes:Q', title='6️⃣ Sixes')
            ]
        )
        
        # Add text labels showing economy rate on bars
        text_labels = base.mark_text(
            align='left',
            baseline='middle',
            dx=5,
            fontSize=13,
            fontWeight='bold',
            color='#f8fafc' # Light color for dark theme
        ).encode(
            x=alt.X('economy:Q'),
            text=alt.Text('economy:Q', format='.2f')
        )
        
        # Add wickets and dots count as secondary text
        wicket_labels = base.mark_text(
            align='left',
            baseline='middle',
            dx=45,
            fontSize=11,
            color='#94a3b8',
            fontWeight=500
        ).encode(
            x=alt.X('economy:Q'),
            text=alt.Text('wicket_text:N')
        )
        
        # Combine all layers
        chart = (bars + text_labels + wicket_labels).properties(
            height=max(300, len(bowler_stats) * 45), # Dynamic height based on bowlers
            title={
                'text': [f'{team} - Bowler Economy Analysis'],
                'subtitle': [
                    'Ranked by economy rate (minimum 4 overs)',
                    'Lower economy = Better performance'
                ],
                'fontSize': 18,
                'fontWeight': 'bold',
                'color': '#f8fafc',
                'subtitleFontSize': 12,
                'subtitleColor': '#94a3b8',
                'anchor': 'start',
                'offset': 20,
                'font': 'Segoe UI'
            }
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=13,
            titleFontWeight=600,
            labelFont='Segoe UI',
            titleFont='Segoe UI'
        ).configure_view(
            strokeWidth=0,
            fill='transparent'
        ).configure_legend(
            titleFontSize=12,
            labelFontSize=11,
            symbolType='circle',
            titleFont='Segoe UI',
            labelFont='Segoe UI'
        ).interactive()
        
        return chart
    
    # -----------------------------------------------------------------------------
    # Interactive Plotly 3D Cricket Ball Animation
    # -----------------------------------------------------------------------------
    
    def create_3d_animated_trajectory():
        import plotly.graph_objects as go
        import numpy as np

        # Pitch dimensions
        pitch_y = np.linspace(0, 20, 2)
        pitch_x = np.linspace(-1.5, 1.5, 2)
        Y, X = np.meshgrid(pitch_y, pitch_x)
        Z = np.zeros_like(X)

        # Base figure with the pitch surface
        fig = go.Figure(data=[
            go.Surface(x=X, y=Y, z=Z, colorscale=[[0, '#654321'], [1, '#654321']], showscale=False, opacity=0.9, name='Pitch', hoverinfo='skip')
        ])
        
        # Add pitch creases (Popping and Bowling creases)
        crease_lines = []
        for y_c in [0, 1.22, 18.78, 20]:
            crease_lines.append(go.Scatter3d(
                x=[-1.5, 1.5], y=[y_c, y_c], z=[0.01, 0.01],
                mode='lines', line=dict(color='white', width=3), showlegend=False, hoverinfo='skip'
            ))
        
        for crease in crease_lines:
            fig.add_trace(crease)

        # Add stumps (Bowler end at y=0, Batter end at y=20)
        for y_pos in [0, 20]:
            for x in [-0.11, 0, 0.11]:
                fig.add_trace(go.Scatter3d(
                    x=[x, x], y=[y_pos, y_pos], z=[0, 0.71],
                    mode='lines', line=dict(color='white', width=4), showlegend=False, hoverinfo='skip'
                ))
            # Bails
            fig.add_trace(go.Scatter3d(
                x=[-0.11, 0.11], y=[y_pos, y_pos], z=[0.71, 0.71],
                mode='lines', line=dict(color='white', width=4), showlegend=False, hoverinfo='skip'
            ))

        # Define ball trajectories
        frames_data = []
        num_frames = 50
        
        # 1. Inswinging Yorker (Red)
        t = np.linspace(0, 1, num_frames)
        y1 = np.linspace(0, 20, num_frames)
        x1 = np.where(t < 0.5, -0.3 * t, -0.15 + 0.15*(t-0.5)/0.5) # Swings in to middle stump
        z1 = 2.2 - 2.2 * t  # Release height 2.2m, hits base of stumps

        # 2. Bouncer (Yellow)
        t_bounce2 = 0.55
        y2 = np.linspace(0, 20, num_frames)
        x2 = np.linspace(-0.2, 0.2, num_frames)
        z2 = np.where(t < t_bounce2, 2.2 - 2.2*(t/t_bounce2), 0.0 + 1.8*((t-t_bounce2)/(1-t_bounce2)))
        
        # 3. Good Length Outswinger (Orange)
        t_bounce3 = 0.8
        y3 = np.linspace(0, 20, num_frames)
        x3 = np.where(t < t_bounce3, 0.15 * (t/t_bounce3), 0.15 + 0.35*((t-t_bounce3)/(1-t_bounce3)))
        z3 = np.where(t < t_bounce3, 2.1 - 2.1*(t/t_bounce3), 0.0 + 0.7*((t-t_bounce3)/(1-t_bounce3)))

        # Add Pitch Marks (Impact points)
        fig.add_trace(go.Scatter3d(x=[0], y=[20 * 0.55], z=[0.02], mode='markers', marker=dict(size=8, color='#eab308', symbol='diamond', opacity=0.7), name='Bouncer Pitch'))
        fig.add_trace(go.Scatter3d(x=[0.15], y=[20 * 0.8], z=[0.02], mode='markers', marker=dict(size=8, color='#f97316', symbol='diamond', opacity=0.7), name='Outswinger Pitch'))

        # Calculate offset for ball traces
        ball_idx = len(fig.data) 
        
        # Add initial balls
        fig.add_trace(go.Scatter3d(x=[x1[0]], y=[y1[0]], z=[z1[0]], mode='markers', marker=dict(size=6, color='#ef4444'), name='Inswinging Yorker'))
        fig.add_trace(go.Scatter3d(x=[x2[0]], y=[y2[0]], z=[z2[0]], mode='markers', marker=dict(size=6, color='#eab308'), name='Bouncer'))
        fig.add_trace(go.Scatter3d(x=[x3[0]], y=[y3[0]], z=[z3[0]], mode='markers', marker=dict(size=6, color='#f97316'), name='Good Length Outswinger'))

        # Build Frames
        frames = []
        for k in range(num_frames):
            frame_data = [
                go.Scatter3d(x=x1[:k+1], y=y1[:k+1], z=z1[:k+1], mode='lines+markers', line=dict(color='#ef4444', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#ef4444')),
                go.Scatter3d(x=x2[:k+1], y=y2[:k+1], z=z2[:k+1], mode='lines+markers', line=dict(color='#eab308', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#eab308')),
                go.Scatter3d(x=x3[:k+1], y=y3[:k+1], z=z3[:k+1], mode='lines+markers', line=dict(color='#f97316', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#f97316')),
            ]
            frames.append(go.Frame(data=frame_data, traces=[ball_idx, ball_idx+1, ball_idx+2], name=str(k)))
        
        fig.frames = frames

        # Setup animation controls and clean layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(title='', range=[-2, 2], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                yaxis=dict(title='', range=[-1, 21], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                zaxis=dict(title='', range=[0, 3], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                aspectmode='manual',
                aspectratio=dict(x=1, y=3.5, z=0.5), # Slightly more elongated
                camera=dict(
                    eye=dict(x=-1.5, y=-2.0, z=0.6), # Isometric view for better depth perception!
                    center=dict(x=0, y=0, z=0)
                )
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="▶ Play Animation", method="animate", args=[None, dict(frame=dict(duration=40, redraw=True), fromcurrent=True, mode="immediate", transition=dict(duration=0))]),
                    dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
                ],
                x=0.5, y=-0.1, xanchor="center", yanchor="top", direction="left",
                bgcolor="#1e293b", font=dict(color="#f8fafc")
            )],
            margin=dict(l=0, r=0, b=0, t=0),
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0.8, y=0.9, bgcolor='rgba(15,23,42,0.8)', font=dict(color='#f8fafc'))
        )
        
        return fig
    
    # -----------------------------------------------------------------------------
    # 3. Three.js 3D Visualization Helper
    # -----------------------------------------------------------------------------
    
    def render_threejs_chart(data, chart_type, title, width=600, height=400):
        import hashlib
        div_id = f"chart_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        data_json = json.dumps(data)
        
        if chart_type == 'grouped_bar_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(15, 15, 15);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            renderer.setClearColor(0xf5f5f5, 1);
            
            const container = document.getElementById('{div_id}');
            container.style.position = 'relative';
            container.appendChild(renderer.domElement);
            
            // Basic Tooltip div
            const tooltip = document.createElement('div');
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = '#ffffff';
            tooltip.style.color = '#000000';
            tooltip.style.padding = '8px';
            tooltip.style.borderRadius = '3px';
            tooltip.style.pointerEvents = 'none';
            tooltip.style.display = 'none';
            tooltip.style.fontFamily = 'Arial, sans-serif';
            tooltip.style.fontSize = '13px';
            tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            tooltip.style.border = '1px solid #cccccc';
            tooltip.style.zIndex = '1000';
            container.appendChild(tooltip);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            scene.add(directionalLight);
            
            let maxValue = 0;
            data.forEach(cat => {{
                cat.values.forEach(val => {{
                    if (val.value > maxValue) maxValue = val.value;
                }});
            }});
            
            const barWidth = 1.5;
            const barDepth = 1.5;
            const spacing = 5;
            const groupSpacing = 2;
            const colors = [0xFDB913, 0x004BA0]; // Original basic colors
            
            const bars = [];
            
            data.forEach((category, catIndex) => {{
                category.values.forEach((val, teamIndex) => {{
                    const height = (val.value / maxValue) * 10;
                    const geometry = new THREE.BoxGeometry(barWidth, height, barDepth);
                    const material = new THREE.MeshPhongMaterial({{ 
                        color: colors[teamIndex], 
                        shininess: 100
                    }});
                    const bar = new THREE.Mesh(geometry, material);
                    
                    const xPos = catIndex * spacing - (data.length * spacing / 2);
                    const zPos = teamIndex * groupSpacing - 1;
                    bar.position.set(xPos, height/2, zPos);
                    
                    bar.userData = {{
                        team: val.label,
                        phase: category.category,
                        value: val.value.toFixed(2),
                        originalColor: colors[teamIndex]
                    }};
                    
                    scene.add(bar);
                    bars.push(bar);
                }});
            }});
            
            const gridHelper = new THREE.GridHelper(30, 30, 0x888888, 0xdddddd);
            scene.add(gridHelper);
            
            // Interactivity and Optimization
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let hoveredBar = null;
            let needsUpdate = true;
            
            controls.addEventListener('change', () => {{ needsUpdate = true; }});
            
            container.addEventListener('mousemove', (event) => {{
                const rect = renderer.domElement.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                
                raycaster.setFromCamera(mouse, camera);
                const intersects = raycaster.intersectObjects(bars);
                
                if (intersects.length > 0) {{
                    const object = intersects[0].object;
                    
                    if (hoveredBar !== object) {{
                        if (hoveredBar) hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                        hoveredBar = object;
                        hoveredBar.material.color.offsetHSL(0, 0, 0.2); // Lighten on hover
                        needsUpdate = true;
                    }}
                    
                    const data = object.userData;
                    tooltip.innerHTML = `<strong>${{data.phase}}</strong><br/>${{data.team}}: <strong>${{data.value}}</strong>`;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (event.clientX - rect.left + 15) + 'px';
                    tooltip.style.top = (event.clientY - rect.top + 15) + 'px';
                    container.style.cursor = 'pointer';
                }} else {{
                    if (hoveredBar) {{
                        hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                        hoveredBar = null;
                        needsUpdate = true;
                    }}
                    tooltip.style.display = 'none';
                    container.style.cursor = 'default';
                }}
            }});
            
            container.addEventListener('mouseleave', () => {{
                if (hoveredBar) {{
                    hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                    hoveredBar = null;
                    needsUpdate = true;
                }}
                tooltip.style.display = 'none';
                container.style.cursor = 'default';
            }});
            
            function animate() {{
                requestAnimationFrame(animate);
                controls.update(); // requires update for damping
                
                // Always render while damping is active, but we can't easily detect when damping stops.
                // For a small scene, simple requestAnimationFrame is OK if we're not allocating objects.
                renderer.render(scene, camera);
            }}
            animate();
            """
        
        elif chart_type == 'bar_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(10, 10, 15);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            scene.add(directionalLight);
            
            const maxValue = Math.max(...data.map(d => d.value));
            const barWidth = 1.5;
            const spacing = 3;
            
            data.forEach((item, index) => {{
                const height = (item.value / maxValue) * 10;
                const hue = (index / data.length) * 0.7;
                
                const geometry = new THREE.BoxGeometry(barWidth, height, barWidth);
                const material = new THREE.MeshPhongMaterial({{ 
                    color: new THREE.Color().setHSL(hue, 0.7, 0.5),
                    shininess: 100
                }});
                const bar = new THREE.Mesh(geometry, material);
                
                bar.position.set((index - data.length/2) * spacing, height/2, 0);
                bar.userData = {{
                    player: item.label,
                    strikeRate: item.value.toFixed(2),
                    balls: item.balls || 0,
                    runs: item.runs || 0,
                    dismissals: item.dismissals || 0
                }};
                
                scene.add(bar);
            }});
            
            const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xdddddd);
            scene.add(gridHelper);
            
            controls.enableDamping = false;
            controls.addEventListener('change', () => renderer.render(scene, camera));
            renderer.render(scene, camera);
            """
        
        elif chart_type == 'pie_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(0, 8, 12);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(5, 10, 5);
            scene.add(directionalLight);
            
            const total = data.reduce((sum, item) => sum + item.value, 0);
            let currentAngle = 0;
            const innerRadius = 2;
            const outerRadius = 5;
            const depth = 1;
            
            data.forEach((item, index) => {{
                const angle = (item.value / total) * Math.PI * 2;
                const hue = (index / data.length);
                
                const shape = new THREE.Shape();
                const startAngle = currentAngle;
                const endAngle = currentAngle + angle;
                
                shape.moveTo(outerRadius * Math.cos(startAngle), outerRadius * Math.sin(startAngle));
                shape.absarc(0, 0, outerRadius, startAngle, endAngle, false);
                shape.lineTo(innerRadius * Math.cos(endAngle), innerRadius * Math.sin(endAngle));
                shape.absarc(0, 0, innerRadius, endAngle, startAngle, true);
                
                const geometry = new THREE.ExtrudeGeometry(shape, {{
                    depth: depth,
                    bevelEnabled: true,
                    bevelThickness: 0.1,
                    bevelSize: 0.1,
                    bevelSegments: 2
                }});
                
                const material = new THREE.MeshPhongMaterial({{ 
                    color: new THREE.Color().setHSL(hue, 0.8, 0.6),
                    shininess: 100
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.z = -depth/2;
                mesh.userData = {{
                    label: item.label,
                    value: item.value,
                    percentage: ((item.value / total) * 100).toFixed(1)
                }};
                
                scene.add(mesh);
                currentAngle = endAngle;
            }});
            
            controls.enableDamping = false;
            controls.addEventListener('change', () => renderer.render(scene, camera));
            renderer.render(scene, camera);
            """
        else:
            script = ""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; font-family: sans-serif; }}
                #title {{ text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
                #{div_id} {{ border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
            </style>
        </head>
        <body>
            <div id="title">{title}</div>
            <div id="{div_id}"></div>
            <script>
                const data = {data_json};
                {script}
            </script>
        </body>
        </html>
        """
        return html
    
    def render_pitch_map(data, title, width=800, height=600):
        """Render advanced 3D pitch map with realistic cricket pitch background"""
        div_id = f"pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        data_json = json.dumps(data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ margin: 0; padding: 15px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .pitch-container-{div_id} {{ 
                    position: relative;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                }}
                .pitch-title-{div_id} {{ 
                    text-align: center; 
                    font-size: 20px; 
                    font-weight: bold; 
                    margin-bottom: 15px;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }}
                .pitch-legend-{div_id} {{ 
                    position: absolute; 
                    top: 70px; 
                    right: 25px; 
                    background: rgba(255,255,255,0.98); 
                    padding: 15px; 
                    border-radius: 10px; 
                    font-size: 12px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
                    z-index: 10;
                    border: 2px solid #1e3c72;
                }}
                .legend-item-{div_id} {{ 
                    display: flex; 
                    align-items: center; 
                    margin: 6px 0; 
                    font-weight: 500;
                }}
                .legend-color-{div_id} {{ 
                    width: 16px; 
                    height: 16px; 
                    border-radius: 50%; 
                    margin-right: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .controls-{div_id} {{
                    position: absolute;
                    top: 70px;
                    left: 25px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    z-index: 10;
                }}
                .view-btn-{div_id} {{
                    background: rgba(255, 255, 255, 0.95);
                    border: 2px solid #1e3c72;
                    padding: 10px 18px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 13px;
                    transition: all 0.3s ease;
                    color: #1e3c72;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }}
                .view-btn-{div_id}:hover {{
                    background: #1e3c72;
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 16px rgba(30, 60, 114, 0.4);
                }}
                #{div_id} {{ 
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                }}
            </style>
        </head>
        <body>
            <div class="pitch-container-{div_id}">
                <div class="pitch-title-{div_id}">{title}</div>
                <div class="controls-{div_id}">
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('top')">📍 Top View</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('bowler')">🎯 Bowler End</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('batter')">🏏 Batter End</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('side')">👁️ Side View</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('reset')">🔄 Reset</button>
                </div>
                <div class="pitch-legend-{div_id}">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #1e3c72; font-size: 14px;">Ball Outcomes</div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #808080;"></div><span>Dot Ball (0)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #2196f3;"></div><span>Singles (1-3)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #00ff00;"></div><span>Four (4)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #9c27b0;"></div><span>Six (6)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #ff0000;"></div><span>Wicket (W)</span></div>
                </div>
                <div id="{div_id}"></div>
            </div>
            <script>
            (function() {{
                const pitchData = {data_json};
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x87ceeb);
                scene.fog = new THREE.Fog(0x87ceeb, 50, 100);
                
                const camera = new THREE.PerspectiveCamera(50, {width}/{height}, 0.1, 1000);
                camera.position.set(0, 30, 35);
                camera.lookAt(0, 0, 11);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize({width}, {height});
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.shadowMap.enabled = false;
                // renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.0;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.08;
                controls.minDistance = 15;
                controls.maxDistance = 80;
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.target.set(0, 0, 11);
                
                // Enhanced lighting system
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambientLight);
                
                const mainLight = new THREE.DirectionalLight(0xffffff, 0.9);
                mainLight.position.set(15, 35, 20);
                mainLight.castShadow = true;
                mainLight.shadow.mapSize.width = 4096;
                mainLight.shadow.mapSize.height = 4096;
                mainLight.shadow.camera.near = 0.5;
                mainLight.shadow.camera.far = 100;
                mainLight.shadow.camera.left = -30;
                mainLight.shadow.camera.right = 30;
                mainLight.shadow.camera.top = 30;
                mainLight.shadow.camera.bottom = -30;
                scene.add(mainLight);
                
                const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
                fillLight.position.set(-15, 20, 10);
                scene.add(fillLight);
                
                const backLight = new THREE.DirectionalLight(0xffffff, 0.2);
                backLight.position.set(0, 15, -20);
                scene.add(backLight);
                
                // Cricket Stadium - Circular outfield
                const stadiumRadius = 70;
                
                // Stadium bowl/ground
                const stadiumGeometry = new THREE.CircleGeometry(stadiumRadius, 64);
                const stadiumMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x1a5c1a,
                    roughness: 0.85,
                    metalness: 0.1
                }});
                const stadium = new THREE.Mesh(stadiumGeometry, stadiumMaterial);
                stadium.rotation.x = -Math.PI / 2;
                stadium.position.set(0, -0.05, 11);
                stadium.receiveShadow = true;
                scene.add(stadium);
                
                // Add stadium grass texture pattern
                const stadiumTexture = document.createElement('canvas');
                stadiumTexture.width = 1024;
                stadiumTexture.height = 1024;
                const stadiumCtx = stadiumTexture.getContext('2d');
                
                // Base green
                stadiumCtx.fillStyle = '#1a5c1a';
                stadiumCtx.fillRect(0, 0, 1024, 1024);
                
                // Grass blades
                for (let i = 0; i < 500; i++) {{
                    const shade = Math.random() * 30 - 15;
                    stadiumCtx.fillStyle = `rgb(${{26 + shade}},${{92 + shade * 1.5}},${{26 + shade}})`;
                    stadiumCtx.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2);
                }}
                
                // Mowing pattern - stripes
                stadiumCtx.globalAlpha = 0.15;
                for (let i = 0; i < 20; i++) {{
                    if (i % 2 === 0) {{
                        stadiumCtx.fillStyle = '#0d4a0d';
                    }} else {{
                        stadiumCtx.fillStyle = '#236b23';
                    }}
                    const stripeWidth = 1024 / 20;
                    stadiumCtx.fillRect(i * stripeWidth, 0, stripeWidth, 1024);
                }}
                stadiumCtx.globalAlpha = 1.0;
                
                const texture = new THREE.CanvasTexture(stadiumTexture);
                texture.wrapS = THREE.RepeatWrapping;
                texture.wrapT = THREE.RepeatWrapping;
                texture.repeat.set(4, 4);
                stadium.material.map = texture;
                stadium.material.needsUpdate = true;
                
                // Inner circle (30-yard circle)
                const innerCircleGeometry = new THREE.RingGeometry(27, 27.3, 64);
                const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.9,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.1
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.set(0, 0, 11);
                innerCircle.receiveShadow = true;
                scene.add(innerCircle);
                
                // Boundary rope
                const boundaryGeometry = new THREE.RingGeometry(stadiumRadius - 0.5, stadiumRadius, 64);
                const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
                boundary.rotation.x = -Math.PI / 2;
                boundary.position.set(0, 0.02, 11);
                scene.add(boundary);
                
                // Stadium boundary markers (advertising boards simulation)
                const markerCount = 32;
                for (let i = 0; i < markerCount; i++) {{
                    const angle = (i / markerCount) * Math.PI * 2;
                    const radius = stadiumRadius - 2;
                    const x = Math.cos(angle) * radius;
                    const z = Math.sin(angle) * radius + 11;
                    
                    const markerGeometry = new THREE.BoxGeometry(3, 1.5, 0.2);
                    const hue = (i / markerCount) * 360;
                    const markerMaterial = new THREE.MeshStandardMaterial({{ 
                        color: new THREE.Color(`hsl(${{hue}}, 70%, 50%)`),
                        roughness: 0.5,
                        metalness: 0.3,
                        emissive: new THREE.Color(`hsl(${{hue}}, 70%, 30%)`),
                        emissiveIntensity: 0.3
                    }});
                    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                    marker.position.set(x, 0.75, z);
                    marker.lookAt(0, 0.75, 11);
                    marker.castShadow = false;
                    scene.add(marker);
                }}
                
                // Floodlight towers (4 corners)
                const floodlightPositions = [
                    {{ x: 50, z: -30 }},
                    {{ x: -50, z: -30 }},
                    {{ x: 50, z: 52 }},
                    {{ x: -50, z: 52 }}
                ];
                
                floodlightPositions.forEach(pos => {{
                    // Tower pole
                    const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 8);
                    const poleMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0x808080,
                        roughness: 0.6,
                        metalness: 0.7
                    }});
                    const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                    pole.position.set(pos.x, 20, pos.z);
                    pole.castShadow = false;
                    scene.add(pole);
                    
                    // Light fixture on top
                    const lightGeometry = new THREE.BoxGeometry(3, 2, 1);
                    const lightMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0xffff00,
                        roughness: 0.3,
                        metalness: 0.5,
                        emissive: 0xffff88,
                        emissiveIntensity: 0.8
                    }});
                    const lightFixture = new THREE.Mesh(lightGeometry, lightMaterial);
                    lightFixture.position.set(pos.x, 41, pos.z);
                    lightFixture.lookAt(0, 0, 11);
                    scene.add(lightFixture);
                }});
                
                // Cricket pitch - tan/brown color with texture (centered in stadium)
                const pitchGeometry = new THREE.PlaneGeometry(2.6, 22.5);
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base color - light brown
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Add dirt texture
                for (let i = 0; i < 8000; i++) {{
                    const shade = Math.random() * 40 - 20;
                    pitchCtx.fillStyle = `rgb(${{201 + shade}},${{168 + shade}},${{117 + shade}})`;
                    pitchCtx.fillRect(Math.random() * 256, Math.random() * 2048, 3, 3);
                }}
                
                // Worn areas (darker patches)
                pitchCtx.fillStyle = 'rgba(160, 130, 80, 0.3)';
                for (let i = 0; i < 5; i++) {{
                    const y = 800 + Math.random() * 400;
                    pitchCtx.fillRect(60 + Math.random() * 130, y, 40 + Math.random() * 30, 60 + Math.random() * 40);
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.8,
                    metalness: 0.0
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.set(0, 0, 11);
                pitch.receiveShadow = true;
                pitch.castShadow = false;
                scene.add(pitch);
                
                // Pitch markings - white creases
                const creaseMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                
                // Bowling creases
                const creaseGeometry = new THREE.PlaneGeometry(2.7, 0.08);
                const crease1 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease1.rotation.x = -Math.PI / 2;
                crease1.position.set(0, 0.01, 0);
                crease1.receiveShadow = true;
                scene.add(crease1);
                
                const crease2 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease2.rotation.x = -Math.PI / 2;
                crease2.position.set(0, 0.01, 22);
                crease2.receiveShadow = true;
                scene.add(crease2);
                
                // Popping creases (4 feet in front of stumps)
                const poppingCreaseGeometry = new THREE.PlaneGeometry(2.7, 0.06);
                const poppingCrease1 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease1.rotation.x = -Math.PI / 2;
                poppingCrease1.position.set(0, 0.01, 1.22);
                scene.add(poppingCrease1);
                
                const poppingCrease2 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease2.rotation.x = -Math.PI / 2;
                poppingCrease2.position.set(0, 0.01, 20.78);
                scene.add(poppingCrease2);
                
                // Return creases (perpendicular lines)
                const returnCreaseGeometry = new THREE.PlaneGeometry(0.06, 2.44);
                for (let x of [-1.35, 1.35]) {{
                    const returnCrease1 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease1.rotation.x = -Math.PI / 2;
                    returnCrease1.position.set(x, 0.01, 0);
                    scene.add(returnCrease1);
                    
                    const returnCrease2 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease2.rotation.x = -Math.PI / 2;
                    returnCrease2.position.set(x, 0.01, 22);
                    scene.add(returnCrease2);
                }}
                
                // Stumps - realistic wooden stumps
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.7,
                    metalness: 0.1
                }});
                
                const stumpPositions = [-0.115, 0, 0.115];
                for (let x of stumpPositions) {{
                    // Bowler end stumps
                    const stump1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8), 
                        stumpMaterial
                    );
                    stump1.position.set(x, 0.355, 0);
                    stump1.castShadow = true;
                    stump1.receiveShadow = true;
                    scene.add(stump1);
                    
                    // Batter end stumps
                    const stump2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8), 
                        stumpMaterial
                    );
                    stump2.position.set(x, 0.355, 22);
                    stump2.castShadow = true;
                    stump2.receiveShadow = true;
                    scene.add(stump2);
                }}
                
                // Bails on top of stumps
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.6,
                    metalness: 0.2
                }});
                
                for (let i = 0; i < 2; i++) {{
                    const x = i === 0 ? -0.0575 : 0.0575;
                    
                    const bail1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail1.rotation.z = Math.PI / 2;
                    bail1.position.set(x, 0.73, 0);
                    bail1.castShadow = true;
                    scene.add(bail1);
                    
                    const bail2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail2.rotation.z = Math.PI / 2;
                    bail2.position.set(x, 0.73, 22);
                    bail2.castShadow = true;
                    scene.add(bail2);
                }}
                
                // Ball landing positions with enhanced materials
                const colorMap = {{ 
                    'red': 0xff0000, 
                    'purple': 0x9c27b0, 
                    'green': 0x00ff00, 
                    'blue': 0x2196f3, 
                    'gray': 0x808080 
                }};
                
                const sharedGeometry = new THREE.SphereGeometry(1, 16, 16);
                const sharedMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    sharedMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.3,
                        metalness: 0.5,
                        emissive: colorHex,
                        emissiveIntensity: 0.4
                    }});
                }}
                
                pitchData.forEach(ball => {{
                    const radius = ball.size * 0.02;
                    const material = sharedMaterials[ball.color] || sharedMaterials['gray'];
                    const sphere = new THREE.Mesh(sharedGeometry, material);
                    sphere.scale.set(radius, radius, radius);
                    sphere.position.set(ball.x, radius + 0.01, ball.y);
                    sphere.castShadow = true;
                    sphere.receiveShadow = true;
                    sphere.userData = {{ 
                        batter: ball.batter, 
                        bowler: ball.bowler, 
                        runs: ball.runs, 
                        wicket: ball.wicket 
                    }};
                    scene.add(sphere);
                }});
                
                // View preset functions
                window.setView_{div_id} = function(view) {{
                    let targetPos, targetLookAt;
                    switch(view) {{
                        case 'top':
                            targetPos = {{ x: 0, y: 50, z: 11 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'bowler':
                            targetPos = {{ x: 0, y: 8, z: -15 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'batter':
                            targetPos = {{ x: 0, y: 8, z: 38 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'side':
                            targetPos = {{ x: 25, y: 15, z: 11 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'reset':
                            targetPos = {{ x: 0, y: 30, z: 35 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                    }}
                    
                    const startPos = {{ x: camera.position.x, y: camera.position.y, z: camera.position.z }};
                    const startTime = Date.now();
                    const duration = 1200;
                    
                    function animateCamera() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
                        
                        camera.position.x = startPos.x + (targetPos.x - startPos.x) * eased;
                        camera.position.y = startPos.y + (targetPos.y - startPos.y) * eased;
                        camera.position.z = startPos.z + (targetPos.z - startPos.z) * eased;
                        
                        controls.target.set(targetLookAt.x, targetLookAt.y, targetLookAt.z);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animateCamera);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animateCamera();
                }};
                
                controls.enableDamping = false;
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_wagon_wheel(data, title, width=600, height=600):
        """Render wagon wheel visualization with realistic cricket stadium using Three.js"""
        data_json = json.dumps(data)
        div_id = f"wagon_wheel_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    font-family: 'Segoe UI', sans-serif;
                }}
                .wagon-container {{ 
                    position: relative;
                    border: 2px solid #ddd; 
                    border-radius: 10px;
                    overflow: hidden;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .wagon-title {{
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;
                    color: white;
                    padding: 10px;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .legend-box {{
                    position: absolute;
                    top: 60px;
                    right: 20px;
                    background: rgba(0,0,0,0.85);
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-size: 12px;
                    backdrop-filter: blur(10px);
                    border: 2px solid rgba(255,255,255,0.2);
                    z-index: 100;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    margin: 6px 0;
                }}
                .legend-color {{
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    margin-right: 10px;
                    border: 2px solid white;
                }}
            </style>
        </head>
        <body>
            <div class="wagon-container">
                <div class="wagon-title">{title}</div>
                <div id="{div_id}"></div>
                <div class="legend-box">
                    <div style="font-weight: bold; margin-bottom: 8px; border-bottom: 2px solid rgba(255,255,255,0.3); padding-bottom: 6px;">SHOT TYPES</div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ff0000;"></div>
                        <span>Boundaries (4s & 6s)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ff9800;"></div>
                        <span>Twos (2 runs)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #2196f3;"></div>
                        <span>Threes (3 runs)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #00ff00;"></div>
                        <span>Singles (1 run)</span>
                    </div>
                </div>
            </div>
            <script>
            (function() {{
                const wagonData = {data_json};
                const scene = new THREE.Scene();
                
                // Realistic sky gradient
                const skyCanvas = document.createElement('canvas');
                skyCanvas.width = 512; skyCanvas.height = 512;
                const skyCtx = skyCanvas.getContext('2d');
                const skyGrad = skyCtx.createLinearGradient(0, 0, 0, 512);
                skyGrad.addColorStop(0, '#1a3a5c');
                skyGrad.addColorStop(0.3, '#3a7bd5');
                skyGrad.addColorStop(0.6, '#87ceeb');
                skyGrad.addColorStop(1, '#b5e3f5');
                skyCtx.fillStyle = skyGrad;
                skyCtx.fillRect(0, 0, 512, 512);
                const skyTexture = new THREE.CanvasTexture(skyCanvas);
                scene.background = skyTexture;
                scene.fog = new THREE.Fog(0x87ceeb, 80, 200);
                
                const camera = new THREE.PerspectiveCamera(50, {width}/{height}, 0.1, 500);
                camera.position.set(0, 85, 5);
                camera.lookAt(0, 0, 0);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize({width}, {height});
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.1;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                // Warm stadium lighting
                const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.5);
                scene.add(ambientLight);
                const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x1a7a1a, 0.4);
                scene.add(hemisphereLight);
                
                const sunLight = new THREE.DirectionalLight(0xfffde6, 0.9);
                sunLight.position.set(50, 120, 50);
                sunLight.castShadow = true;
                sunLight.shadow.mapSize.width = 1024;
                sunLight.shadow.mapSize.height = 1024;
                sunLight.shadow.camera.left = -100;
                sunLight.shadow.camera.right = 100;
                sunLight.shadow.camera.top = 100;
                sunLight.shadow.camera.bottom = -100;
                scene.add(sunLight);
                
                const fillLight = new THREE.DirectionalLight(0xb0d4f1, 0.3);
                fillLight.position.set(-50, 80, -50);
                scene.add(fillLight);
                
                // Procedural grass with mowing stripes
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 1024;
                grassCanvas.height = 1024;
                const grassCtx = grassCanvas.getContext('2d');
                
                for (let i = 0; i < 20; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#157015' : '#1a7a1a';
                    grassCtx.fillRect(0, i * 51.2, 1024, 51.2);
                }}
                for (let i = 0; i < 8000; i++) {{
                    const x = Math.random() * 1024;
                    const y = Math.random() * 1024;
                    const brightness = 90 + Math.random() * 50;
                    grassCtx.fillStyle = `rgba(20, ${{brightness}}, 20, 0.6)`;
                    grassCtx.fillRect(x, y, 2, 2);
                }}
                
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                
                // Circular stadium ground (70m radius)
                const groundGeometry = new THREE.CircleGeometry(70, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    map: grassTexture,
                    roughness: 0.85,
                    metalness: 0.1
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                scene.add(ground);
                
                // 30-yard circle
                const innerCircleGeometry = new THREE.RingGeometry(27.43, 27.73, 64);
                const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff, roughness: 0.6, metalness: 0.2
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.y = 0.05;
                scene.add(innerCircle);
                
                // Boundary rope
                const boundaryGeometry = new THREE.RingGeometry(69.5, 70, 64);
                const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff, roughness: 0.4, metalness: 0.3
                }});
                const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
                boundary.rotation.x = -Math.PI / 2;
                boundary.position.y = 0.1;
                scene.add(boundary);
                
                // Load realistic 3D Stadium Model
                const loader = new THREE.GLTFLoader();
                loader.load(
                    '/app/static/stadium.glb',
                    function (gltf) {{
                        const model = gltf.scene;
                        
                        // Compute bounding box
                        const box = new THREE.Box3().setFromObject(model);
                        const size = box.getSize(new THREE.Vector3());
                        const center = box.getCenter(new THREE.Vector3());
                        
                        // Center model
                        model.position.x += (model.position.x - center.x);
                        model.position.y += (model.position.y - box.min.y) - 2;
                        model.position.z += (model.position.z - center.z);
                        
                        // Scale to cover the outfield
                        const maxDim = Math.max(size.x, size.z);
                        const scaleFactor = 250 / maxDim;
                        model.scale.set(scaleFactor, scaleFactor, scaleFactor);
                        
                        model.traverse(function (node) {{
                            if (node.isMesh) {{
                                node.castShadow = false;
                                node.receiveShadow = false;
                                if (node.material) {{
                                    node.material.roughness = 0.75;
                                    node.material.metalness = 0.15;
                                }}
                            }}
                        }});
                        
                        scene.add(model);
                        renderer.render(scene, camera);
                    }},
                    undefined,
                    function (error) {{
                        console.error('Error loading 3D stadium model:', error);
                    }}
                );
                
                // Create realistic pitch texture with wear patterns
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base pitch color (tan/brown)
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Add dirt particles for realism
                for (let i = 0; i < 10000; i++) {{
                    const x = Math.random() * 256;
                    const y = Math.random() * 2048;
                    const shade = 170 + Math.random() * 50;
                    pitchCtx.fillStyle = `rgb(${{shade}}, ${{shade * 0.75}}, ${{shade * 0.55}})`;
                    pitchCtx.fillRect(x, y, 1, 1);
                }}
                
                // Add worn patches in center (where bowlers land)
                for (let i = 0; i < 8; i++) {{
                    const y = 900 + Math.random() * 300;
                    pitchCtx.fillStyle = 'rgba(150, 120, 85, 0.4)';
                    pitchCtx.fillRect(50 + Math.random() * 30, y, 120 + Math.random() * 40, 50);
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                
                // Cricket pitch (22 yards = 20.12m length, 3.05m width)
                const pitchGeometry = new THREE.PlaneGeometry(3.05, 20.12);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.92,
                    metalness: 0.08
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.y = 0.15;
                pitch.receiveShadow = true;
                scene.add(pitch);
                
                // Cricket stumps at striker's end (center)
                const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8);
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                
                // Three stumps with proper spacing (11cm between stumps)
                [-0.11, 0, 0.11].forEach(xPos => {{
                    const stump = new THREE.Mesh(stumpGeometry, stumpMaterial);
                    stump.position.set(xPos, 0.355, 0);
                    stump.castShadow = true;
                    scene.add(stump);
                }});
                
                // Bails on top of stumps
                const bailGeometry = new THREE.CylinderGeometry(0.01, 0.01, 0.11, 8);
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                
                [-0.055, 0.055].forEach(xPos => {{
                    const bail = new THREE.Mesh(bailGeometry, bailMaterial);
                    bail.rotation.z = Math.PI / 2;
                    bail.position.set(xPos, 0.71, 0);
                    scene.add(bail);
                }});
                
                // Crease line at striker's end
                const creaseGeometry = new THREE.PlaneGeometry(3, 0.05);
                const creaseMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.6
                }});
                const crease = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease.rotation.x = -Math.PI / 2;
                crease.position.y = 0.16;
                scene.add(crease);
                
                // Wagon wheel shot lines and balls
                const colorMap = {{
                    'red': 0xff0000,      // Boundaries (4s & 6s)
                    'orange': 0xff9800,  // Twos
                    'blue': 0x2196f3,    // Threes
                    'green': 0x00ff00    // Singles
                }};
                const sharedBallGeometry = new THREE.SphereGeometry(1, 12, 12); // Reusable sphere
                const ballMaterials = {{}};
                const lineMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.3,
                        metalness: 0.7,
                        emissive: colorHex,
                        emissiveIntensity: 0.4
                    }});
                    lineMaterials[key] = new THREE.LineBasicMaterial({{ 
                        color: colorHex,
                        linewidth: 2,
                        opacity: 0.65,
                        transparent: true
                    }});
                }}
                
                // Keep the center point reusable
                const centerPoint = new THREE.Vector3(0, 0.4, 0);

                wagonData.forEach(shot => {{
                    const radius = shot.size * 0.12;
                    const ballMat = ballMaterials[shot.color] || ballMaterials['green'];
                    const lineMat = lineMaterials[shot.color] || lineMaterials['green'];

                    // Shot line from stumps to landing point
                    const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                        centerPoint,
                        new THREE.Vector3(shot.x, 0.4, shot.y)
                    ]);
                    const line = new THREE.Line(lineGeometry, lineMat);
                    scene.add(line);
                    
                    // Ball at landing point
                    const ball = new THREE.Mesh(sharedBallGeometry, ballMat);
                    ball.scale.set(radius, radius, radius);
                    ball.position.set(shot.x, radius + 0.2, shot.y);
                    ball.castShadow = true;
                    scene.add(ball);
                }});
                
                // Interactive OrbitControls
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.minDistance = 25;
                controls.maxDistance = 150;
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.target.set(0, 0, 0);
                
                controls.enableDamping = false;
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_bowling_length_map(df, team, phase=None, bowler_type=None, unique_id=""):
        """Render 3D bowling length visualization with zones and percentages"""
        pitch_data = generate_pitch_map_data_complete(df, team=team, phase=phase, bowler_type=bowler_type)
        
        if not pitch_data:
            return "<p>No data available for bowling length map</p>"
        
        div_id = f"bowling_length_{unique_id}"
        data_json = json.dumps(pitch_data)
        
        title_parts = [f"{team} - Bowling Length Analysis"]
        if phase:
            title_parts.append(f"({phase})")
        if bowler_type and bowler_type != 'All Types':
            title_parts.append(f"vs {bowler_type}")
        title = " ".join(title_parts)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 20px; 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .bowling-container {{ 
                    position: relative; 
                    text-align: center;
                    background: rgba(255,255,255,0.05);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .bowling-title {{ 
                    text-align: center; 
                    font-size: 26px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 3px;
                    text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
                }}
                #{div_id} {{ 
                    border: 3px solid rgba(255,255,255,0.3); 
                    border-radius: 12px; 
                    display: inline-block;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                    background: #000;
                }}
                .stats-overlay {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: rgba(15, 23, 42, 0.75);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    padding: 15px;
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 12px;
                    min-width: 180px;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    display: none;
                    transition: all 0.3s ease;
                }}
                .stats-overlay.show {{
                    display: block;
                    animation: slideIn 0.3s ease-out;
                }}
                @keyframes slideIn {{
                    from {{
                        opacity: 0;
                        transform: translateX(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .toggle-stats-btn {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    z-index: 100;
                }}
                .toggle-stats-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
                }}
                .toggle-views-btn {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
                    z-index: 100;
                }}
                .toggle-views-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(240, 147, 251, 0.5);
                }}
                .zone-stat {{
                    margin: 6px 0;
                    padding: 8px 10px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-left: 3px solid;
                }}
                .zone-name {{
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 10px;
                    letter-spacing: 1px;
                }}
                .zone-percentage {{
                    font-size: 20px;
                    font-weight: bold;
                }}
                .short {{ color: #ff6b6b; border-color: #ff6b6b; }}
                .length {{ color: #ffd93d; border-color: #ffd93d; }}
                .full {{ color: #6bcf7f; border-color: #6bcf7f; }}
                .yorker {{ color: #4dabf7; border-color: #4dabf7; }}
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
                .view-controls {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: rgba(0,0,0,0.9);
                    padding: 12px 14px;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    border: 2px solid rgba(255,255,255,0.2);
                    backdrop-filter: blur(10px);
                    display: none;
                    z-index: 10;
                }}
                .view-controls.show {{
                    display: block;
                    animation: slideInLeft 0.3s ease-out;
                }}
                @keyframes slideInLeft {{
                    from {{
                        opacity: 0;
                        transform: translateX(-20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .view-btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 8px 12px;
                    margin: 3px 0;
                    border-radius: 6px;
                    cursor: pointer;
                    width: 100%;
                    font-weight: bold;
                    font-size: 11px;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                }}
                .view-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5);
                }}
                .controls-title {{
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
            </style>
        </head>
        <body>
            <div class="bowling-container">
                <div class="bowling-title">{title}</div>
                <div id="{div_id}"></div>
                <button class="toggle-views-btn" onclick="toggleViews_{unique_id}()">📐 Views</button>
                <button class="toggle-stats-btn" onclick="toggleStats_{unique_id}()">📊 Statistics</button>
                <div class="view-controls" id="view-controls-{unique_id}">
                    <div class="controls-title">📐 VIEWS</div>
                    <button class="view-btn" onclick="setTopView_{unique_id}()">📍 Top</button>
                    <button class="view-btn" onclick="setBowlerView_{unique_id}()">🎯 Bowler</button>
                    <button class="view-btn" onclick="setBatterView_{unique_id}()">🏏 Batter</button>
                    <button class="view-btn" onclick="setSideView_{unique_id}()">👁️ Side</button>
                    <button class="view-btn" onclick="resetView_{unique_id}()">🔄 Reset</button>
                </div>
                <div class="stats-overlay" id="stats-overlay-{unique_id}">
                    <div class="legend-title">📊 Bowling Length %</div>
                    <div id="zone-stats-{unique_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const pitchData = {data_json};
                
                // Scene setup
                const scene = new THREE.Scene();
                // Night sky background
                scene.background = new THREE.Color(0x050a1f);
                scene.fog = new THREE.Fog(0x050a1f, 100, 250);
                
                // Camera setup
                const camera = new THREE.PerspectiveCamera(45, 900/700, 0.1, 500);
                camera.position.set(0, 45, 60);
                camera.lookAt(0, 0, 11);
                
                // Renderer setup
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(900, 700);
                renderer.shadowMap.enabled = false;
                // renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                // Controls
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.1;
                controls.target.set(0, 0, 11);
                controls.minDistance = 10;
                controls.maxDistance = 70;
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                scene.add(ambientLight);
                
                const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
                sunLight.position.set(20, 30, 20);
                sunLight.castShadow = false;
                sunLight.shadow.mapSize.width = 2048;
                sunLight.shadow.mapSize.height = 2048;
                sunLight.shadow.camera.left = -50;
                sunLight.shadow.camera.right = 50;
                sunLight.shadow.camera.top = 50;
                sunLight.shadow.camera.bottom = -50;
                sunLight.shadow.camera.far = 100;
                scene.add(sunLight);
                
                const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
                fillLight.position.set(-20, 15, -15);
                scene.add(fillLight);
                
                // --- PROCEDURAL STADIUM ---
                const groundRadius = 75;
                
                // Stadium ground with grass texture
                const groundGeometry = new THREE.CircleGeometry(groundRadius, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x1a5c1a,
                    roughness: 0.85
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.position.set(0, -0.1, 11);
                ground.receiveShadow = true;
                scene.add(ground);
                
                // Stadium Boundary Rope
                const boundaryGeo = new THREE.TorusGeometry(groundRadius - 2, 0.4, 8, 32);
                const boundaryMat = new THREE.MeshStandardMaterial({{ color: 0xffffff }});
                const boundary = new THREE.Mesh(boundaryGeo, boundaryMat);
                boundary.rotation.x = Math.PI / 2;
                boundary.position.set(0, 0.1, 11);
                scene.add(boundary);
                
                // Stadium Stands (Tier 1)
                const standsMat = new THREE.MeshStandardMaterial({{ color: 0x1a365d, roughness: 0.9 }});
                const tier1Geo = new THREE.TorusGeometry(groundRadius + 8, 12, 8, 32);
                const tier1 = new THREE.Mesh(tier1Geo, standsMat);
                tier1.rotation.x = Math.PI / 2;
                tier1.position.set(0, 2, 11);
                scene.add(tier1);
                
                // Stadium Stands (Tier 2)
                const tier2Mat = new THREE.MeshStandardMaterial({{ color: 0x2b6cb0, roughness: 0.9 }});
                const tier2Geo = new THREE.TorusGeometry(groundRadius + 22, 16, 8, 32);
                const tier2 = new THREE.Mesh(tier2Geo, tier2Mat);
                tier2.rotation.x = Math.PI / 2;
                tier2.position.set(0, 10, 11);
                scene.add(tier2);
                
                // Stadium Floodlights
                const poleGeo = new THREE.CylinderGeometry(0.5, 1, 40, 8);
                const poleMat = new THREE.MeshStandardMaterial({{ color: 0x888888, metalness: 0.8, roughness: 0.2 }});
                const lightAngles = [Math.PI/4, 3*Math.PI/4, 5*Math.PI/4, 7*Math.PI/4];
                
                lightAngles.forEach(angle => {{
                    // Pole
                    const pole = new THREE.Mesh(poleGeo, poleMat);
                    const px = Math.cos(angle) * (groundRadius + 30);
                    const pz = Math.sin(angle) * (groundRadius + 30) + 11; // center offset
                    pole.position.set(px, 20, pz);
                    scene.add(pole);
                    
                    // Light Panel
                    const panelGeo = new THREE.BoxGeometry(8, 4, 1);
                    const panelMat = new THREE.MeshStandardMaterial({{ color: 0xdddddd, emissive: 0xffffff, emissiveIntensity: 2 }});
                    const panel = new THREE.Mesh(panelGeo, panelMat);
                    panel.position.set(px, 40, pz);
                    panel.lookAt(0, 0, 11);
                    scene.add(panel);
                    
                    // Actual Spotlight
                    const floodLight = new THREE.SpotLight(0xffffff, 1.2, 250, Math.PI/4, 0.5, 1);
                    floodLight.position.set(px, 40, pz);
                    floodLight.target.position.set(0, 0, 11);
                    scene.add(floodLight);
                    scene.add(floodLight.target);
                }});
                
                // Create grass texture
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 1024;
                grassCanvas.height = 1024;
                const grassCtx = grassCanvas.getContext('2d');
                
                // Base green
                grassCtx.fillStyle = '#1a5c1a';
                grassCtx.fillRect(0, 0, 1024, 1024);
                
                // Add grass texture
                for (let i = 0; i < 500; i++) {{
                    const shade = Math.random() * 30 - 15;
                    grassCtx.fillStyle = `rgb(${{26 + shade}},${{92 + shade * 1.5}},${{26 + shade}})`;
                    grassCtx.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2);
                }}
                
                // Mowing pattern stripes
                grassCtx.globalAlpha = 0.15;
                for (let i = 0; i < 20; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#0d4a0d' : '#236b23';
                    grassCtx.fillRect(i * 51.2, 0, 51.2, 1024);
                }}
                grassCtx.globalAlpha = 1.0;
                
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                grassTexture.repeat.set(4, 4);
                ground.material.map = grassTexture;
                ground.material.needsUpdate = true;
                
                // 30-yard inner circle
                const innerCircleGeometry = new THREE.RingGeometry(27, 27.3, 64);
                const innerCircleMaterial = new THREE.MeshBasicMaterial({{ 
                    color: 0xffffff,
                    side: THREE.DoubleSide
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.set(0, -0.05, 11);
                scene.add(innerCircle);
                

                
                // Cricket pitch - realistic tan/brown surface in center
                const pitchGeometry = new THREE.PlaneGeometry(2.8, 23);
                
                // Create pitch texture
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base tan color
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Add dirt texture
                for (let i = 0; i < 8000; i++) {{
                    const shade = Math.random() * 40 - 20;
                    pitchCtx.fillStyle = `rgb(${{201 + shade}},${{168 + shade}},${{117 + shade}})`;
                    pitchCtx.fillRect(Math.random() * 256, Math.random() * 2048, 3, 3);
                }}
                
                // Worn patches
                pitchCtx.fillStyle = 'rgba(160, 130, 80, 0.3)';
                for (let i = 0; i < 5; i++) {{
                    const y = 800 + Math.random() * 400;
                    pitchCtx.fillRect(60 + Math.random() * 130, y, 40 + Math.random() * 30, 60 + Math.random() * 40);
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.85
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.y = -0.03;
                pitch.position.z = 11;
                pitch.receiveShadow = true;
                scene.add(pitch);
                
                // Pitch creases (white lines)
                const creaseMaterial = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
                
                // Bowling creases
                const creaseGeometry = new THREE.PlaneGeometry(2.9, 0.08);
                const crease1 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease1.rotation.x = -Math.PI / 2;
                crease1.position.set(0, 0.01, 0);
                scene.add(crease1);
                
                const crease2 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease2.rotation.x = -Math.PI / 2;
                crease2.position.set(0, 0.01, 22);
                scene.add(crease2);
                
                // Stumps at both ends
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.8
                }});
                
                const stumpPositions = [-0.115, 0, 0.115];
                stumpPositions.forEach(x => {{
                    // Bowler end
                    const stump1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 12),
                        stumpMaterial
                    );
                    stump1.position.set(x, 0.36, 0);
                    stump1.castShadow = true;
                    scene.add(stump1);
                    
                    // Batter end
                    const stump2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 12),
                        stumpMaterial
                    );
                    stump2.position.set(x, 0.36, 22);
                    stump2.castShadow = true;
                    scene.add(stump2);
                }});
                
                // Define bowling length zones
                const zones = [
                    {{ name: 'SHORT', start: 4, end: 10, color: 0xff6b6b, label: 'SHORT', yPos: 7 }},
                    {{ name: 'LENGTH', start: 10, end: 16, color: 0xffd93d, label: 'LENGTH', yPos: 13 }},
                    {{ name: 'FULL', start: 16, end: 20, color: 0x6bcf7f, label: 'FULL', yPos: 18 }},
                    {{ name: 'YORKER', start: 20, end: 22, color: 0x4dabf7, label: 'YORKER', yPos: 21 }}
                ];
                
                // Create zone boxes
                zones.forEach(zone => {{
                    const zoneLength = zone.end - zone.start;
                    const zoneGeometry = new THREE.BoxGeometry(3, 0.15, zoneLength);
                    const zoneMaterial = new THREE.MeshStandardMaterial({{ 
                        color: zone.color,
                        transparent: true,
                        opacity: 0.6,
                        roughness: 0.5
                    }});
                    const zoneMesh = new THREE.Mesh(zoneGeometry, zoneMaterial);
                    zoneMesh.position.set(0, 0.08, zone.start + zoneLength/2);
                    zoneMesh.castShadow = true;
                    zoneMesh.receiveShadow = true;
                    scene.add(zoneMesh);
                    
                    // Zone labels
                    const canvas = document.createElement('canvas');
                    canvas.width = 256;
                    canvas.height = 128;
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 56px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(zone.label, 128, 64);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const spriteMaterial = new THREE.SpriteMaterial({{ 
                        map: texture,
                        transparent: true
                    }});
                    const sprite = new THREE.Sprite(spriteMaterial);
                    sprite.position.set(3, 1, zone.yPos);
                    sprite.scale.set(2.5, 1.25, 1);
                    scene.add(sprite);
                }});
                
                // Add balls
                const colorMap = {{
                    'red': 0xff0000,
                    'purple': 0x9c27b0,
                    'green': 0x00ff00,
                    'blue': 0x2196f3,
                    'gray': 0x808080
                }};
                const sharedBallGeometry = new THREE.SphereGeometry(1, 12, 12);
                const ballMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.4,
                        metalness: 0.3,
                        emissive: colorHex,
                        emissiveIntensity: 0.3
                    }});
                }}
                
                pitchData.forEach(ball => {{
                    const radius = ball.size * 0.02;
                    const ballMaterial = ballMaterials[ball.color] || ballMaterials['gray'];
                    const ballMesh = new THREE.Mesh(sharedBallGeometry, ballMaterial);
                    ballMesh.scale.set(radius, radius, radius);
                    ballMesh.position.set(ball.x, radius + 0.15, ball.y);
                    ballMesh.castShadow = true;
                    scene.add(ballMesh);
                }});
                
                // Calculate zone statistics
                const zoneCounts = {{ SHORT: 0, LENGTH: 0, FULL: 0, YORKER: 0 }};
                pitchData.forEach(ball => {{
                    const y = ball.y;
                    if (y >= 4 && y < 10) zoneCounts.SHORT++;
                    else if (y >= 10 && y < 16) zoneCounts.LENGTH++;
                    else if (y >= 16 && y < 20) zoneCounts.FULL++;
                    else if (y >= 20 && y <= 22) zoneCounts.YORKER++;
                }});
                
                const total = pitchData.length;
                const statsData = [
                    {{ name: 'SHORT', count: zoneCounts.SHORT, class: 'short' }},
                    {{ name: 'LENGTH', count: zoneCounts.LENGTH, class: 'length' }},
                    {{ name: 'FULL', count: zoneCounts.FULL, class: 'full' }},
                    {{ name: 'YORKER', count: zoneCounts.YORKER, class: 'yorker' }}
                ];
                
                const statsHtml = statsData.map(stat => {{
                    const percentage = total > 0 ? ((stat.count / total) * 100).toFixed(0) : 0;
                    return `
                        <div class="zone-stat ${{stat.class}}">
                            <span class="zone-name">${{stat.name}}</span>
                            <span class="zone-percentage">${{percentage}}%</span>
                        </div>
                    `;
                }}).join('');
                
                document.getElementById('zone-stats-{unique_id}').innerHTML = statsHtml;
                
                // Camera animation helper
                function animateCamera(targetPos, targetLookAt) {{
                    const startPos = camera.position.clone();
                    const startTarget = controls.target.clone();
                    const startTime = Date.now();
                    const duration = 1000;
                    
                    function animate() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3);
                        
                        camera.position.lerpVectors(startPos, targetPos, eased);
                        controls.target.lerpVectors(startTarget, targetLookAt, eased);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animate);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animate();
                }}
                
                // View functions
                window.setTopView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 40, 11),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setBowlerView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 10, -10),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setBatterView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 10, 35),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setSideView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(30, 15, 11),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.resetView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 18, 30),
                    new THREE.Vector3(0, 0, 11)
                );
                
                controls.enableDamping = false;
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
                
                // Toggle statistics overlay
                window.toggleStats_{unique_id} = function() {{
                    const statsOverlay = document.getElementById('stats-overlay-{unique_id}');
                    statsOverlay.classList.toggle('show');
                }};
                
                // Toggle view controls
                window.toggleViews_{unique_id} = function() {{
                    const viewControls = document.getElementById('view-controls-{unique_id}');
                    viewControls.classList.toggle('show');
                }};
                
                // Toggle view controls
                window.toggleViews_{unique_id} = function() {{
                    const viewControls = document.getElementById('view-controls-{unique_id}');
                    viewControls.classList.toggle('show');
                }};
            }})();
            </script>
        </body>
        </html>
        """
        return html
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #1a1a1a; }}
                .bowling-container {{ position: relative; text-align: center; }}
                .bowling-title {{ 
                    text-align: center; 
                    font-size: 24px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }}
                #{div_id} {{ 
                    border: 2px solid #333; 
                    border-radius: 8px; 
                    display: inline-block;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
                }}
                .stats-overlay {{
                    position: absolute;
                    top: 80px;
                    right: 40px;
                    background: rgba(0,0,0,0.85);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    font-size: 14px;
                    min-width: 200px;
                    border: 2px solid #444;
                }}
                .zone-stat {{
                    margin: 12px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .zone-name {{
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 12px;
                    letter-spacing: 1px;
                }}
                .zone-percentage {{
                    font-size: 24px;
                    font-weight: bold;
                }}
                .short {{ color: #ff6b6b; }}
                .length {{ color: #ffd93d; }}
                .full {{ color: #6bcf7f; }}
                .yorker {{ color: #4dabf7; }}
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 15px;
                    font-size: 16px;
                    border-bottom: 2px solid #666;
                    padding-bottom: 10px;
                }}
                .view-controls {{
                    position: absolute;
                    top: 80px;
                    left: 20px;
                    background: rgba(15, 23, 42, 0.75);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    padding: 15px;
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 12px;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                .view-btn {{
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    color: #e2e8f0;
                    padding: 8px 12px;
                    margin: 4px 0;
                    border-radius: 6px;
                    cursor: pointer;
                    width: 100%;
                    font-weight: 600;
                    transition: all 0.3s ease;
                }}
                .view-btn:hover {{
                    transform: translateY(-2px);
                    background: rgba(56, 189, 248, 0.2);
                    border-color: rgba(56, 189, 248, 0.5);
                    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
                    color: #fff;
                }}
                .controls-title {{
                    font-weight: 700;
                    margin-bottom: 12px;
                    font-size: 13px;
                    color: #38bdf8;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    padding-bottom: 8px;
                    letter-spacing: 1px;
                }}
            </style>
        </head>
        <body>
            <div class="bowling-container">
                <div class="bowling-title">{title}</div>
                <div id="{div_id}"></div>
                <div class="view-controls">
                    <div class="controls-title">VIEW ANGLES</div>
                    <button class="view-btn" onclick="setTopView_{unique_id}()">📐 Top View</button>
                    <button class="view-btn" onclick="setBowlerView_{unique_id}()">🎯 Bowler End</button>
                    <button class="view-btn" onclick="setBatterView_{unique_id}()">🏏 Batter End</button>
                    <button class="view-btn" onclick="setSideView_{unique_id}()">👁️ Side View</button>
                    <button class="view-btn" onclick="resetView_{unique_id}()">🔄 Reset</button>
                </div>
                <div class="stats-overlay">
                    <div class="legend-title">BOWLING LENGTH %</div>
                    <div id="zone-stats-{unique_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const pitchData = {data_json};
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x87ceeb);
                scene.fog = new THREE.Fog(0x87ceeb, 100, 200);
                
                const camera = new THREE.PerspectiveCamera(50, 900/700, 0.1, 1000);
                camera.position.set(0, 15, 25);
                camera.lookAt(0, 0, 11);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(900, 700);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                renderer.shadowMap.enabled = false;
                // renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                renderer.outputEncoding = THREE.sRGBEncoding;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.08;
                controls.target.set(0, 0, 11);
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.minPolarAngle = 0;
                controls.minDistance = 10;
                controls.maxDistance = 80;
                controls.enablePan = true;
                controls.panSpeed = 0.8;
                controls.rotateSpeed = 0.6;
                
                // Enhanced Lighting
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambientLight);
                
                const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
                mainLight.position.set(15, 25, 15);
                mainLight.castShadow = true;
                mainLight.shadow.mapSize.width = 2048;
                mainLight.shadow.mapSize.height = 2048;
                mainLight.shadow.camera.near = 0.5;
                mainLight.shadow.camera.far = 150;
                mainLight.shadow.camera.left = -80;
                mainLight.shadow.camera.right = 80;
                mainLight.shadow.camera.top = 80;
                mainLight.shadow.camera.bottom = -80;
                scene.add(mainLight);
                
                const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
                fillLight.position.set(-15, 15, -10);
                scene.add(fillLight);
                
                const backLight = new THREE.DirectionalLight(0xffffff, 0.3);
                backLight.position.set(0, 10, -20);
                scene.add(backLight);
                
                // Cricket Stadium - Circular outfield
                const stadiumRadius = 70;
                
                // Stadium bowl/ground
                const stadiumGeometry = new THREE.CircleGeometry(stadiumRadius, 64);
                const stadiumMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x1a5c1a,
                    roughness: 0.85,
                    metalness: 0.1
                }});
                const stadium = new THREE.Mesh(stadiumGeometry, stadiumMaterial);
                stadium.rotation.x = -Math.PI / 2;
                stadium.position.set(0, -0.08, 11);
                stadium.receiveShadow = true;
                scene.add(stadium);
                
                // Add stadium grass texture pattern
                const stadiumTexture = document.createElement('canvas');
                stadiumTexture.width = 1024;
                stadiumTexture.height = 1024;
                const stadiumCtx = stadiumTexture.getContext('2d');
                
                // Base green
                stadiumCtx.fillStyle = '#1a5c1a';
                stadiumCtx.fillRect(0, 0, 1024, 1024);
                
                // Grass blades
                for (let i = 0; i < 500; i++) {{
                    const shade = Math.random() * 30 - 15;
                    stadiumCtx.fillStyle = `rgb(${{26 + shade}},${{92 + shade * 1.5}},${{26 + shade}})`;
                    stadiumCtx.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2);
                }}
                
                // Mowing pattern - stripes
                stadiumCtx.globalAlpha = 0.15;
                for (let i = 0; i < 20; i++) {{
                    if (i % 2 === 0) {{
                        stadiumCtx.fillStyle = '#0d4a0d';
                    }} else {{
                        stadiumCtx.fillStyle = '#236b23';
                    }}
                    const stripeWidth = 1024 / 20;
                    stadiumCtx.fillRect(i * stripeWidth, 0, stripeWidth, 1024);
                }}
                stadiumCtx.globalAlpha = 1.0;
                
                const stadTexture = new THREE.CanvasTexture(stadiumTexture);
                stadTexture.wrapS = THREE.RepeatWrapping;
                stadTexture.wrapT = THREE.RepeatWrapping;
                stadTexture.repeat.set(4, 4);
                stadium.material.map = stadTexture;
                stadium.material.needsUpdate = true;
                
                // Inner circle (30-yard circle)
                const innerCircleGeometry = new THREE.RingGeometry(27, 27.3, 64);
                const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.9,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.1
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.set(0, -0.05, 11);
                innerCircle.receiveShadow = true;
                scene.add(innerCircle);
                
                // Boundary rope
                const boundaryGeometry = new THREE.RingGeometry(stadiumRadius - 0.5, stadiumRadius, 64);
                const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
                boundary.rotation.x = -Math.PI / 2;
                boundary.position.set(0, -0.03, 11);
                scene.add(boundary);
                
                // Stadium boundary markers (advertising boards)
                const markerCount = 32;
                for (let i = 0; i < markerCount; i++) {{
                    const angle = (i / markerCount) * Math.PI * 2;
                    const radius = stadiumRadius - 2;
                    const x = Math.cos(angle) * radius;
                    const z = Math.sin(angle) * radius + 11;
                    
                    const markerGeometry = new THREE.BoxGeometry(3, 1.5, 0.2);
                    const hue = (i / markerCount) * 360;
                    const markerMaterial = new THREE.MeshStandardMaterial({{ 
                        color: new THREE.Color(`hsl(${{hue}}, 70%, 50%)`),
                        roughness: 0.5,
                        metalness: 0.3,
                        emissive: new THREE.Color(`hsl(${{hue}}, 70%, 30%)`),
                        emissiveIntensity: 0.3
                    }});
                    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                    marker.position.set(x, 0.75, z);
                    marker.lookAt(0, 0.75, 11);
                    marker.castShadow = false;
                    scene.add(marker);
                }}
                
                // Floodlight towers (4 corners)
                const floodlightPositions = [
                    {{ x: 50, z: -30 }},
                    {{ x: -50, z: -30 }},
                    {{ x: 50, z: 52 }},
                    {{ x: -50, z: 52 }}
                ];
                
                floodlightPositions.forEach(pos => {{
                    // Tower pole
                    const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 8);
                    const poleMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0x808080,
                        roughness: 0.6,
                        metalness: 0.7
                    }});
                    const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                    pole.position.set(pos.x, 20, pos.z);
                    pole.castShadow = false;
                    scene.add(pole);
                    
                    // Light fixture on top
                    const lightGeometry = new THREE.BoxGeometry(3, 2, 1);
                    const lightMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0xffff00,
                        roughness: 0.3,
                        metalness: 0.5,
                        emissive: 0xffff88,
                        emissiveIntensity: 0.8
                    }});
                    const lightFixture = new THREE.Mesh(lightGeometry, lightMaterial);
                    lightFixture.position.set(pos.x, 41, pos.z);
                    lightFixture.lookAt(0, 0, 11);
                    scene.add(lightFixture);
                }});
                
                // Cricket pitch - realistic tan/brown with detailed texture
                const pitchGeometry = new THREE.PlaneGeometry(2.6, 22.5);
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base color - light brown/tan
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Add dirt/clay texture
                for (let i = 0; i < 8000; i++) {{
                    const shade = Math.random() * 40 - 20;
                    pitchCtx.fillStyle = `rgb(${{201 + shade}},${{168 + shade}},${{117 + shade}})`;
                    pitchCtx.fillRect(Math.random() * 256, Math.random() * 2048, 3, 3);
                }}
                
                // Worn areas (darker patches in middle)
                pitchCtx.fillStyle = 'rgba(160, 130, 80, 0.3)';
                for (let i = 0; i < 5; i++) {{
                    const y = 800 + Math.random() * 400;
                    pitchCtx.fillRect(60 + Math.random() * 130, y, 40 + Math.random() * 30, 60 + Math.random() * 40);
                }}
                
                // Add some cracks
                pitchCtx.strokeStyle = 'rgba(140, 110, 70, 0.4)';
                pitchCtx.lineWidth = 2;
                for (let i = 0; i < 15; i++) {{
                    pitchCtx.beginPath();
                    const startX = Math.random() * 256;
                    const startY = 600 + Math.random() * 800;
                    pitchCtx.moveTo(startX, startY);
                    pitchCtx.lineTo(startX + Math.random() * 40 - 20, startY + Math.random() * 60);
                    pitchCtx.stroke();
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.8,
                    metalness: 0.0
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.set(0, -0.04, 11);
                pitch.receiveShadow = true;
                pitch.castShadow = false;
                scene.add(pitch);
                
                // Pitch markings - white creases
                const creaseMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                
                // Bowling creases
                const creaseGeometry = new THREE.PlaneGeometry(2.7, 0.08);
                const crease1 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease1.rotation.x = -Math.PI / 2;
                crease1.position.set(0, -0.03, 0);
                crease1.receiveShadow = true;
                scene.add(crease1);
                
                const crease2 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease2.rotation.x = -Math.PI / 2;
                crease2.position.set(0, -0.03, 22);
                crease2.receiveShadow = true;
                scene.add(crease2);
                
                // Popping creases (4 feet in front of stumps)
                const poppingCreaseGeometry = new THREE.PlaneGeometry(2.7, 0.06);
                const poppingCrease1 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease1.rotation.x = -Math.PI / 2;
                poppingCrease1.position.set(0, -0.03, 1.22);
                scene.add(poppingCrease1);
                
                const poppingCrease2 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease2.rotation.x = -Math.PI / 2;
                poppingCrease2.position.set(0, -0.03, 20.78);
                scene.add(poppingCrease2);
                
                // Return creases (perpendicular lines)
                const returnCreaseGeometry = new THREE.PlaneGeometry(0.06, 2.44);
                for (let x of [-1.35, 1.35]) {{
                    const returnCrease1 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease1.rotation.x = -Math.PI / 2;
                    returnCrease1.position.set(x, -0.03, 0);
                    scene.add(returnCrease1);
                    
                    const returnCrease2 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease2.rotation.x = -Math.PI / 2;
                    returnCrease2.position.set(x, -0.03, 22);
                    scene.add(returnCrease2);
                }}
                
                // Define length zones with 3D appearance
                const zones = [
                    {{ name: 'YORKER', start: 20, end: 22, color: 0x4dabf7, label: 'YORKER', yPos: 21 }},
                    {{ name: 'FULL', start: 16, end: 20, color: 0x6bcf7f, label: 'FULL', yPos: 18 }},
                    {{ name: 'LENGTH', start: 10, end: 16, color: 0xffd93d, label: 'LENGTH', yPos: 13 }},
                    {{ name: 'SHORT', start: 4, end: 10, color: 0xff6b6b, label: 'SHORT', yPos: 7 }}
                ];
                
                // Create 3D zone blocks (semi-transparent to show pitch)
                zones.forEach(zone => {{
                    const height = zone.end - zone.start;
                    const geometry = new THREE.BoxGeometry(2.8, 0.12, height);
                    const material = new THREE.MeshStandardMaterial({{ 
                        color: zone.color,
                        transparent: true,
                        opacity: 0.5,
                        roughness: 0.5,
                        metalness: 0.2
                    }});
                    const zoneMesh = new THREE.Mesh(geometry, material);
                    zoneMesh.position.set(0, 0.06, zone.start + height/2);
                    zoneMesh.receiveShadow = true;
                    zoneMesh.castShadow = false;
                    scene.add(zoneMesh);
                    
                    // Zone labels
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.width = 256;
                    canvas.height = 128;
                    context.fillStyle = 'white';
                    context.font = 'bold 48px Arial';
                    context.textAlign = 'center';
                    context.fillText(zone.label, 128, 80);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const spriteMaterial = new THREE.SpriteMaterial({{ 
                        map: texture,
                        transparent: true,
                        opacity: 0.9
                    }});
                    const sprite = new THREE.Sprite(spriteMaterial);
                    sprite.position.set(-2.5, 0.5, zone.yPos);
                    sprite.scale.set(2, 1, 1);
                    scene.add(sprite);
                }});
                
                // Create realistic wooden stumps
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.7,
                    metalness: 0.1
                }});
                
                const stumpPositions = [-0.115, 0, 0.115];
                
                // Bowler's end stumps
                for (let x of stumpPositions) {{
                    const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8);
                    const stump = new THREE.Mesh(stumpGeometry, stumpMaterial);
                    stump.position.set(x, 0.355, 0);
                    stump.castShadow = true;
                    stump.receiveShadow = true;
                    scene.add(stump);
                }}
                
                // Batter's end stumps
                for (let x of stumpPositions) {{
                    const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8);
                    const stump = new THREE.Mesh(stumpGeometry, stumpMaterial);
                    stump.position.set(x, 0.355, 22);
                    stump.castShadow = true;
                    stump.receiveShadow = true;
                    scene.add(stump);
                }}
                
                // Bails on top of stumps
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.6,
                    metalness: 0.2
                }});
                
                for (let i = 0; i < 2; i++) {{
                    const x = i === 0 ? -0.0575 : 0.0575;
                    
                    // Bowler's end bails
                    const bail1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail1.rotation.z = Math.PI / 2;
                    bail1.position.set(x, 0.73, 0);
                    bail1.castShadow = true;
                    scene.add(bail1);
                    
                    // Batter's end bails
                    const bail2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail2.rotation.z = Math.PI / 2;
                    bail2.position.set(x, 0.73, 22);
                    bail2.castShadow = true;
                    scene.add(bail2);
                }}
                
                // Pitch center line (visual guide)
                const lineGeometry = new THREE.BoxGeometry(0.08, 0.01, 22);
                const lineMaterial = new THREE.MeshStandardMaterial({{ color: 0x9b59b6 }});
                const centerLine = new THREE.Mesh(lineGeometry, lineMaterial);
                centerLine.position.set(0, 0.16, 11);
                scene.add(centerLine);
                
                // Crease lines (white)
                const creaseMaterial = new THREE.MeshStandardMaterial({{ color: 0xffffff }});
                for (let z of [0, 22]) {{
                    const creaseGeometry = new THREE.BoxGeometry(2.8, 0.02, 0.1);
                    const crease = new THREE.Mesh(creaseGeometry, creaseMaterial);
                    crease.position.set(0, 0.16, z);
                    scene.add(crease);
                }}
                
                // Create balls
                const colorMap = {{
                    'red': 0xff0000,
                    'purple': 0x9c27b0,
                    'green': 0x00ff00,
                    'blue': 0x2196f3,
                    'gray': 0x808080
                }};
                
                const sharedBallGeometry = new THREE.SphereGeometry(1, 12, 12);
                const ballMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.5,
                        metalness: 0.3,
                        emissive: colorHex,
                        emissiveIntensity: 0.3
                    }});
                }}
                
                pitchData.forEach(ball => {{
                    const radius = ball.size * 0.025;
                    const material = ballMaterials[ball.color] || ballMaterials['gray'];
                    const sphere = new THREE.Mesh(sharedBallGeometry, material);
                    sphere.scale.set(radius, radius, radius);
                    sphere.position.set(ball.x, radius + 0.15, ball.y);
                    sphere.castShadow = true;
                    scene.add(sphere);
                }});
                
                // Calculate zone percentages
                const zoneCounts = {{
                    'YORKER': pitchData.filter(d => d.y >= 20 && d.y <= 22).length,
                    'FULL': pitchData.filter(d => d.y >= 16 && d.y < 20).length,
                    'LENGTH': pitchData.filter(d => d.y >= 10 && d.y < 16).length,
                    'SHORT': pitchData.filter(d => d.y >= 4 && d.y < 10).length
                }};
                
                const total = pitchData.length;
                const statsHtml = [
                    {{ name: 'YORKER', count: zoneCounts.YORKER, class: 'yorker' }},
                    {{ name: 'FULL', count: zoneCounts.FULL, class: 'full' }},
                    {{ name: 'LENGTH', count: zoneCounts.LENGTH, class: 'length' }},
                    {{ name: 'SHORT', count: zoneCounts.SHORT, class: 'short' }}
                ].map(stat => {{
                    const percentage = total > 0 ? ((stat.count / total) * 100).toFixed(0) : 0;
                    return `
                        <div class="zone-stat">
                            <span class="zone-name ${{stat.class}}\">${{stat.name}}</span>
                            <span class="zone-percentage ${{stat.class}}\">${{percentage}}%</span>
                        </div>
                    `;
                }}).join('');
                
                document.getElementById('zone-stats-{unique_id}').innerHTML = statsHtml;
                
                // Camera animation helper
                function animateCamera(targetPos, targetLookAt, duration = 1000) {{
                    const startPos = camera.position.clone();
                    const startTarget = controls.target.clone();
                    const startTime = Date.now();
                    
                    function animate() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3);
                        
                        camera.position.lerpVectors(startPos, targetPos, eased);
                        controls.target.lerpVectors(startTarget, targetLookAt, eased);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animate);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animate();
                }}
                
                // View angle functions
                window.setTopView_{unique_id} = function() {{
                    animateCamera(
                        new THREE.Vector3(0, 35, 11),
                        new THREE.Vector3(0, 0, 11)
                    );
                }};
                
                window.setBowlerView_{unique_id} = function() {{
                    animateCamera(
                        new THREE.Vector3(0, 12, -8),
                        new THREE.Vector3(0, 0, 11)
                    );
                }};
                
                window.setBatterView_{unique_id} = function() {{
                    animateCamera(
                        new THREE.Vector3(0, 12, 30),
                        new THREE.Vector3(0, 0, 11)
                    );
                }};
                
                window.setSideView_{unique_id} = function() {{
                    animateCamera(
                        new THREE.Vector3(25, 15, 11),
                        new THREE.Vector3(0, 0, 11)
                    );
                }};
                
                window.resetView_{unique_id} = function() {{
                    animateCamera(
                        new THREE.Vector3(0, 15, 25),
                        new THREE.Vector3(0, 0, 11)
                    );
                }};
                
                controls.enableDamping = false;
                controls.addEventListener('change', () => renderer.render(scene, camera));
                renderer.render(scene, camera);
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_stumps_view(data, title, width=500, height=600):
        """Render stumps view visualization as 3D with interactive controls like Bowling Length Analysis"""
        data_json = json.dumps(data)
        div_id = f"stumps_view_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 20px; 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .stumps-container {{ 
                    position: relative; 
                    text-align: center;
                    background: rgba(255,255,255,0.05);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .stumps-title {{ 
                    text-align: center; 
                    font-size: 26px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 3px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .stats-overlay {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: rgba(0,0,0,0.95);
                    padding: 12px 16px;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    min-width: 160px;
                    border: 2px solid rgba(255,255,255,0.2);
                    backdrop-filter: blur(10px);
                    display: none;
                    transition: all 0.3s ease;
                }}
                .stats-overlay.show {{
                    display: block;
                    animation: slideIn 0.3s ease-out;
                }}
                @keyframes slideIn {{
                    from {{
                        opacity: 0;
                        transform: translateX(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .toggle-stats-btn {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    z-index: 100;
                }}
                .toggle-stats-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
                }}
                .toggle-views-btn {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
                    z-index: 100;
                }}
                .toggle-views-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(240, 147, 251, 0.5);
                }}
                .zone-stat {{
                    margin: 6px 0;
                    padding: 8px 10px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-left: 3px solid;
                }}
                .zone-name {{
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 10px;
                    letter-spacing: 1px;
                }}
                .zone-percentage {{
                    font-size: 20px;
                    font-weight: bold;
                }}
                .wickets {{ color: #ff6b6b; border-color: #ff6b6b; }}
                .boundaries {{ color: #9c27b0; border-color: #9c27b0; }}
                .singles {{ color: #00ff00; border-color: #00ff00; }}
                .twos {{ color: #2196f3; border-color: #2196f3; }}
                .dots {{ color: #808080; border-color: #808080; }}
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
                .view-controls {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: rgba(0,0,0,0.9);
                    padding: 12px 14px;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    border: 2px solid rgba(255,255,255,0.2);
                    backdrop-filter: blur(10px);
                    display: none;
                    z-index: 10;
                }}
                .view-controls.show {{
                    display: block;
                    animation: slideInLeft 0.3s ease-out;
                }}
                @keyframes slideInLeft {{
                    from {{
                        opacity: 0;
                        transform: translateX(-20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .view-btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 8px 12px;
                    margin: 3px 0;
                    border-radius: 6px;
                    cursor: pointer;
                    width: 100%;
                    font-weight: bold;
                    font-size: 11px;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                }}
                .view-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5);
                }}
                .controls-title {{
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
            </style>
        </head>
        <body>
            <div class="stumps-container">
                <div class="stumps-title">{title}</div>
                <div id="{div_id}"></div>
                <button class="toggle-views-btn" onclick="toggleViews_{unique_id}()">📐 Views</button>
                <button class="toggle-stats-btn" onclick="toggleStats_{unique_id}()">📊 Statistics</button>
                <div class="view-controls" id="view-controls-{unique_id}">
                    <div class="controls-title">📐 VIEWS</div>
                    <button class="view-btn" onclick="setFrontView_{unique_id}()">📍 Front</button>
                    <button class="view-btn" onclick="setTopView_{unique_id}()">🎯 Top</button>
                    <button class="view-btn" onclick="setSideView_{unique_id}()">👁️ Side</button>
                    <button class="view-btn" onclick="resetView_{unique_id}()">🔄 Reset</button>
                </div>
                <div class="stats-overlay" id="stats-overlay-{unique_id}">
                    <div class="legend-title">📊 Ball Statistics</div>
                    <div id="zone-stats-{unique_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const stumpsData = {data_json};
                const scene = new THREE.Scene();
                
                // Realistic sky gradient
                const skyCanvas = document.createElement('canvas');
                skyCanvas.width = 512; skyCanvas.height = 512;
                const skyCtx = skyCanvas.getContext('2d');
                const skyGrad = skyCtx.createLinearGradient(0, 0, 0, 512);
                skyGrad.addColorStop(0, '#1a3a5c');
                skyGrad.addColorStop(0.3, '#3a7bd5');
                skyGrad.addColorStop(0.6, '#87ceeb');
                skyGrad.addColorStop(1, '#b5e3f5');
                skyCtx.fillStyle = skyGrad;
                skyCtx.fillRect(0, 0, 512, 512);
                const skyTexture = new THREE.CanvasTexture(skyCanvas);
                scene.background = skyTexture;
                scene.fog = new THREE.Fog(0x87ceeb, 40, 120);
                
                const camera = new THREE.PerspectiveCamera(45, {width}/{height}, 0.1, 200);
                camera.position.set(0, 8, 25);
                camera.lookAt(0, 1.5, 0);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize({width}, {height});
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.1;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.minDistance = 8;
                controls.maxDistance = 50;
                controls.maxPolarAngle = Math.PI / 2;
                controls.target.set(0, 1.5, 0);
                
                // Lighting — warm stadium feel
                const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.5);
                scene.add(ambientLight);
                const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x1a7a1a, 0.4);
                scene.add(hemisphereLight);
                
                const sunLight = new THREE.DirectionalLight(0xfffde6, 0.9);
                sunLight.position.set(15, 30, 20);
                sunLight.castShadow = true;
                sunLight.shadow.mapSize.width = 1024;
                sunLight.shadow.mapSize.height = 1024;
                sunLight.shadow.camera.left = -30;
                sunLight.shadow.camera.right = 30;
                sunLight.shadow.camera.top = 30;
                sunLight.shadow.camera.bottom = -30;
                scene.add(sunLight);
                
                const fillLight = new THREE.DirectionalLight(0xb0d4f1, 0.3);
                fillLight.position.set(-10, 15, -10);
                scene.add(fillLight);
                
                // Procedural grass with mowing stripes
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 512; grassCanvas.height = 512;
                const grassCtx = grassCanvas.getContext('2d');
                for (let i = 0; i < 16; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#1a7a1a' : '#15701a';
                    grassCtx.fillRect(0, i * 32, 512, 32);
                }}
                for (let i = 0; i < 3000; i++) {{
                    const gx = Math.random() * 512;
                    const gy = Math.random() * 512;
                    grassCtx.fillStyle = `rgba(20, ${{85 + Math.random() * 50}}, 18, 0.5)`;
                    grassCtx.fillRect(gx, gy, 1, 2);
                }}
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                grassTexture.repeat.set(4, 4);
                
                // Ground — large oval outfield
                const groundGeometry = new THREE.CircleGeometry(60, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    map: grassTexture,
                    roughness: 0.85,
                    metalness: 0.05
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                scene.add(ground);
                
                // Boundary rope (white ring)
                const ropeGeo = new THREE.RingGeometry(55, 55.4, 64);
                const ropeMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.4 }});
                const rope = new THREE.Mesh(ropeGeo, ropeMat);
                rope.rotation.x = -Math.PI / 2; rope.position.y = 0.06;
                scene.add(rope);
                
                // 30-yard inner circle
                const innerGeo = new THREE.RingGeometry(27.4, 27.7, 64);
                const innerMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.5 }});
                const innerCircle = new THREE.Mesh(innerGeo, innerMat);
                innerCircle.rotation.x = -Math.PI / 2; innerCircle.position.y = 0.04;
                scene.add(innerCircle);
                
                // Load realistic 3D Stadium Model in the background
                const loader = new THREE.GLTFLoader();
                loader.load(
                    '/app/static/stadium.glb',
                    function (gltf) {{
                        const model = gltf.scene;
                        
                        // Compute bounding box
                        const box = new THREE.Box3().setFromObject(model);
                        const size = box.getSize(new THREE.Vector3());
                        const center = box.getCenter(new THREE.Vector3());
                        
                        // Center model
                        model.position.x += (model.position.x - center.x);
                        model.position.y += (model.position.y - box.min.y) - 1.5;
                        model.position.z += (model.position.z - center.z);
                        
                        // Scale to cover the outfield
                        const maxDim = Math.max(size.x, size.z);
                        const scaleFactor = 200 / maxDim;
                        model.scale.set(scaleFactor, scaleFactor, scaleFactor);
                        
                        model.traverse(function (node) {{
                            if (node.isMesh) {{
                                node.castShadow = false;
                                node.receiveShadow = false;
                                if (node.material) {{
                                    node.material.roughness = 0.75;
                                    node.material.metalness = 0.15;
                                }}
                            }}
                        }});
                        
                        scene.add(model);
                        renderer.render(scene, camera);
                    }},
                    undefined,
                    function (error) {{
                        console.error('Error loading 3D stadium model:', error);
                    }}
                );
                scene.add(ground);
                
                // Cricket pitch dimensions (22 yards = 20.12m length, 3.05m width)
                const pitchLength = 20.12;
                const pitchWidth = 3.05;
                
                // Pitch surface
                const pitchGeometry = new THREE.PlaneGeometry(pitchWidth, pitchLength);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xd4a574,
                    roughness: 0.9,
                    metalness: 0.1
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.y = 0.01;
                pitch.receiveShadow = true;
                scene.add(pitch);
                
                // Stump specifications (standard cricket dimensions)
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                const stumpHeight = 0.71; // 71cm
                const stumpRadius = 0.02; // 2cm radius
                const stumpSpacing = 0.11; // 11cm between stumps
                const stumpPositions = [-stumpSpacing, 0, stumpSpacing];
                
                // Batting stumps at near end (z = pitchLength/2)
                const battingStumpZ = pitchLength / 2;
                stumpPositions.forEach(x => {{
                    const stump = new THREE.Mesh(
                        new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 8), 
                        stumpMaterial
                    );
                    stump.position.set(x, stumpHeight / 2, battingStumpZ);
                    stump.castShadow = true;
                    scene.add(stump);
                }});
                
                // Bails on batting stumps
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                const bailLength = 0.11;
                [-stumpSpacing/2, stumpSpacing/2].forEach(x => {{
                    const bail = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.01, 0.01, bailLength, 8),
                        bailMaterial
                    );
                    bail.rotation.z = Math.PI / 2;
                    bail.position.set(x, stumpHeight, battingStumpZ);
                    scene.add(bail);
                }});
                
                // Bowling stumps at far end (z = -pitchLength/2)
                const bowlingStumpZ = -pitchLength / 2;
                stumpPositions.forEach(x => {{
                    const stump = new THREE.Mesh(
                        new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 8), 
                        stumpMaterial
                    );
                    stump.position.set(x, stumpHeight / 2, bowlingStumpZ);
                    stump.castShadow = true;
                    scene.add(stump);
                }});
                
                // Bails on bowling stumps
                [-stumpSpacing/2, stumpSpacing/2].forEach(x => {{
                    const bail = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.01, 0.01, bailLength, 8),
                        bailMaterial
                    );
                    bail.rotation.z = Math.PI / 2;
                    bail.position.set(x, stumpHeight, bowlingStumpZ);
                    scene.add(bail);
                }});
                
                // Crease lines
                const lineMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.6
                }});
                
                // Batting crease (at batting end)
                const battingCrease = new THREE.Mesh(
                    new THREE.PlaneGeometry(pitchWidth, 0.05),
                    lineMaterial
                );
                battingCrease.rotation.x = -Math.PI / 2;
                battingCrease.position.set(0, 0.02, battingStumpZ);
                scene.add(battingCrease);
                
                // Bowling crease (at bowling end)
                const bowlingCrease = new THREE.Mesh(
                    new THREE.PlaneGeometry(pitchWidth, 0.05),
                    lineMaterial
                );
                bowlingCrease.rotation.x = -Math.PI / 2;
                bowlingCrease.position.set(0, 0.02, bowlingStumpZ);
                scene.add(bowlingCrease);
                
                // Wide line markers (dashed effect with small rectangles)
                // Positioned at approximately 1.2m from center on each side
                const wideLineMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xff0000,
                    transparent: true,
                    opacity: 0.6
                }});
                
                const wideLineX = 1.2;
                for (let z = -pitchLength/2; z < pitchLength/2; z += 0.4) {{
                    // Left wide line
                    const leftWide = new THREE.Mesh(
                        new THREE.PlaneGeometry(0.03, 0.2),
                        wideLineMaterial
                    );
                    leftWide.rotation.x = -Math.PI / 2;
                    leftWide.position.set(-wideLineX, 0.02, z);
                    scene.add(leftWide);
                    
                    // Right wide line
                    const rightWide = new THREE.Mesh(
                        new THREE.PlaneGeometry(0.03, 0.2),
                        wideLineMaterial
                    );
                    rightWide.rotation.x = -Math.PI / 2;
                    rightWide.position.set(wideLineX, 0.02, z);
                    scene.add(rightWide);
                }}
                
                // Color map for balls
                const colorMap = {{
                    'red': 0xff0000,
                    'purple': 0x9c27b0,
                    'green': 0x00ff00,
                    'blue': 0x2196f3,
                    'gray': 0x808080
                }};
                
                // Statistics
                let stats = {{
                    total: stumpsData.length,
                    wickets: 0,
                    boundaries: 0,
                    singles: 0,
                    twosThrees: 0,
                    dots: 0
                }};
                
                const sharedBallGeometry = new THREE.SphereGeometry(1, 16, 16);
                const ballMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.3,
                        metalness: 0.6,
                        emissive: colorHex,
                        emissiveIntensity: 0.2
                    }});
                }}
                
                // Draw balls with better distribution across pitch
                stumpsData.forEach(ball => {{
                    // Update stats
                    switch(ball.color) {{
                        case 'red': stats.wickets++; break;
                        case 'purple': stats.boundaries++; break;
                        case 'green': stats.singles++; break;
                        case 'blue': stats.twosThrees++; break;
                        case 'gray': stats.dots++; break;
                    }}
                    
                    const radius = ball.size * 0.012;
                    const ballMaterial = ballMaterials[ball.color] || ballMaterials['gray'];
                    const sphere = new THREE.Mesh(sharedBallGeometry, ballMaterial);
                    sphere.scale.set(radius, radius, radius);
                    
                    // Position mapping for better visualization:
                    // ball.x: horizontal position (-2 to 2) - maps to line (wide left to wide right)
                    // ball.y: vertical position along pitch (0 to 5) - maps to length (bowling end to batting end)
                    // ball.z: height above ground
                    
                    // Map x coordinate: -2 to 2 range maps to -1.4 to 1.4 on pitch (within 3.05m width)
                    const xPos = ball.x * 0.7;
                    
                    // Map y coordinate: 0 to 5 range maps along full pitch length (20.12m)
                    // bowling end (-10.06) to batting end (+10.06)
                    const zPos = (ball.y * 4.024) - 10.06;
                    
                    // Height: slightly above pitch surface
                    const yPos = radius + 0.02;
                    
                    sphere.position.set(xPos, yPos, zPos);
                    sphere.castShadow = true;
                    scene.add(sphere);
                }});
                
                // Display statistics
                const statsHtml = `
                    <div class="zone-stat wickets">
                        <span class="zone-name">Wickets</span>
                        <span class="zone-percentage">${{stats.wickets}}</span>
                    </div>
                    <div class="zone-stat boundaries">
                        <span class="zone-name">Boundaries</span>
                        <span class="zone-percentage">${{stats.boundaries}}</span>
                    </div>
                    <div class="zone-stat singles">
                        <span class="zone-name">Singles</span>
                        <span class="zone-percentage">${{stats.singles}}</span>
                    </div>
                    <div class="zone-stat twos">
                        <span class="zone-name">2s/3s</span>
                        <span class="zone-percentage">${{stats.twosThrees}}</span>
                    </div>
                    <div class="zone-stat dots">
                        <span class="zone-name">Dot Balls</span>
                        <span class="zone-percentage">${{stats.dots}}</span>
                    </div>
                    <div class="zone-stat" style="border-top: 2px solid rgba(255,255,255,0.3); margin-top: 10px; padding-top: 10px;">
                        <span class="zone-name">Total</span>
                        <span class="zone-percentage">${{stats.total}}</span>
                    </div>
                `;
                document.getElementById('zone-stats-{unique_id}').innerHTML = statsHtml;
                
                // Camera animation function
                function animateCamera(targetPos, targetLookAt, duration = 1000) {{
                    const startPos = {{
                        x: camera.position.x,
                        y: camera.position.y,
                        z: camera.position.z
                    }};
                    const startTime = Date.now();
                    
                    function animate() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = progress < 0.5 
                            ? 2 * progress * progress 
                            : -1 + (4 - 2 * progress) * progress;
                        
                        camera.position.x = startPos.x + (targetPos.x - startPos.x) * eased;
                        camera.position.y = startPos.y + (targetPos.y - startPos.y) * eased;
                        camera.position.z = startPos.z + (targetPos.z - startPos.z) * eased;
                        
                        controls.target.set(targetLookAt.x, targetLookAt.y, targetLookAt.z);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animate);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animate();
                }}
                
                // View preset functions
                window.setFrontView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 8, z: 25 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                window.setTopView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 30, z: 0 }},
                    {{ x: 0, y: 0, z: 0 }}
                );
                
                window.setSideView_{unique_id} = () => animateCamera(
                    {{ x: 25, y: 8, z: 0 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                window.resetView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 8, z: 25 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                controls.enableDamping = false; // Disable damping since we don't have a continuous animation loop
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
                
                // Toggle statistics overlay
                window.toggleStats_{unique_id} = function() {{
                    const statsOverlay = document.getElementById('stats-overlay-{unique_id}');
                    statsOverlay.classList.toggle('show');
                }};
                
                // Toggle view controls
                window.toggleViews_{unique_id} = function() {{
                    const viewControls = document.getElementById('view-controls-{unique_id}');
                    viewControls.classList.toggle('show');
                }};
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    
    def render_advanced_pitch_viz(data, title, width=1200, height=450):
        """Render advanced 4-panel pitch visualization with heat maps"""
        import json
        
        if not data:
            return "<p>No data available</p>"
        
        data_json = json.dumps(data)
        div_id = f"advanced_pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        
        # Separate wickets and non-wickets
        wickets = [d for d in data if d['wicket'] == 1]
        hitting = [d for d in data if d['wicket'] == 0]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
            <style>
                .viz-container-{div_id} {{ 
                    display: grid; 
                    grid-template-columns: repeat(2, 1fr); 
                    gap: 15px; 
                    margin: 20px 0;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .viz-item-{div_id} {{ 
                    border: 2px solid #e0e0e0; 
                    border-radius: 10px; 
                    padding: 10px;
                    background: white;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }}
                .viz-item-{div_id}:hover {{ 
                    transform: translateY(-4px);
                    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                    border-color: #667eea;
                }}
                .viz-subtitle-{div_id} {{ 
                    text-align: center; 
                    font-size: 14px; 
                    font-weight: bold; 
                    margin-bottom: 10px;
                    color: #333;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
            </style>
        </head>
        <body>
            <div class="viz-container-{div_id}">
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Wickets</div>
                    <div id="plot1_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Not Hitting</div>
                    <div id="plot2_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Density Heat Map</div>
                    <div id="plot3_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Combined</div>
                    <div id="plot4_{div_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const allData = {data_json};
                const wickets = allData.filter(d => d.wicket === 1);
                const hitting = allData.filter(d => d.wicket === 0);
                
                const commonLayout = {{
                    height: 400,
                    margin: {{ t: 5, r: 10, b: 25, l: 30 }},
                    xaxis: {{ 
                        range: [-1.5, 1.5], 
                        showgrid: true, 
                        gridcolor: 'rgba(255, 255, 255, 0.3)',
                        gridwidth: 1,
                        zeroline: false,
                        title: '',
                        tickfont: {{ size: 9 }}
                    }},
                    yaxis: {{ 
                        range: [0, 22], 
                        showgrid: true,
                        gridcolor: 'rgba(255, 255, 255, 0.3)',
                        gridwidth: 1,
                        zeroline: false,
                        title: '',
                        tickfont: {{ size: 9 }}
                    }},
                    plot_bgcolor: '#d4a574',
                    paper_bgcolor: 'white',
                    showlegend: false,
                    images: [
                        // Pitch center strip (lighter color for worn area)
                        {{
                            source: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMSIgaGVpZ2h0PSIxIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNjNDk1NjQiLz48L3N2Zz4=',
                            xref: 'x',
                            yref: 'y',
                            x: -0.5,
                            y: 22,
                            sizex: 1,
                            sizey: 22,
                            sizing: 'stretch',
                            opacity: 0.6,
                            layer: 'below'
                        }}
                    ]
                }};
                
                // Cricket stumps (3 vertical lines for each end)
                const stumpHeight = 0.3;
                
                // Batting end stumps (bottom)
                const battingStumps = [
                    {{ x: [-0.11, -0.11], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    {{ x: [0, 0], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    {{ x: [0.11, 0.11], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    // Bails
                    {{ x: [-0.11, 0.11], y: [stumpHeight, stumpHeight], mode: 'lines', line: {{ color: '#8B4513', width: 3 }}, hoverinfo: 'skip' }}
                ];
                
                // Bowling end stumps (top)
                const bowlingStumps = [
                    {{ x: [-0.11, -0.11], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    {{ x: [0, 0], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    {{ x: [0.11, 0.11], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#8B4513', width: 4 }}, hoverinfo: 'skip' }},
                    // Bails
                    {{ x: [-0.11, 0.11], y: [22 - stumpHeight, 22 - stumpHeight], mode: 'lines', line: {{ color: '#8B4513', width: 3 }}, hoverinfo: 'skip' }}
                ];
                
                // Crease lines
                const creaseLines = [
                    // Batting crease (bottom)
                    {{ x: [-0.6, 0.6], y: [0, 0], mode: 'lines', line: {{ color: 'white', width: 3 }}, hoverinfo: 'skip' }},
                    // Bowling crease (top)
                    {{ x: [-0.6, 0.6], y: [22, 22], mode: 'lines', line: {{ color: 'white', width: 3 }}, hoverinfo: 'skip' }},
                    // Popping crease markers (dashed)
                    {{ x: [-0.6, 0.6], y: [0.5, 0.5], mode: 'lines', line: {{ color: 'white', width: 2, dash: 'dot' }}, hoverinfo: 'skip' }},
                    {{ x: [-0.6, 0.6], y: [21.5, 21.5], mode: 'lines', line: {{ color: 'white', width: 2, dash: 'dot' }}, hoverinfo: 'skip' }}
                ];
                
                // Plot 1: Wickets
                const wicketsTrace = {{
                    x: wickets.map(d => d.x),
                    y: wickets.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 7,
                        color: '#ef5350',
                        opacity: 0.7,
                        line: {{ width: 1, color: 'white' }}
                    }},
                    hovertemplate: '<b>WICKET</b><br>%{{text}}<extra></extra>',
                    text: wickets.map(d => d.batter)
                }};
                
                Plotly.newPlot('plot1_{div_id}', [wicketsTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
                
                // Plot 2: Hitting
                const hittingTrace = {{
                    x: hitting.map(d => d.x),
                    y: hitting.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 5,
                        color: '#2196f3',
                        opacity: 0.6,
                        line: {{ width: 0.5, color: 'white' }}
                    }},
                    hovertemplate: '<b>%{{text}} run(s)</b><extra></extra>',
                    text: hitting.map(d => d.runs)
                }};
                
                Plotly.newPlot('plot2_{div_id}', [hittingTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
                
                // Plot 3: Heat map
                const heatmapTrace = {{
                    x: allData.map(d => d.x),
                    y: allData.map(d => d.y),
                    type: 'histogram2dcontour',
                    colorscale: [
                        [0, '#d4a574'],
                        [0.2, '#c49564'],
                        [0.4, '#ffeb3b'],
                        [0.6, '#ff9800'],
                        [0.8, '#ff5722'],
                        [1, '#b71c1c']
                    ],
                    showscale: true,
                    colorbar: {{
                        len: 0.6,
                        thickness: 8,
                        x: 1.02,
                        tickfont: {{ size: 8 }}
                    }},
                    contours: {{
                        coloring: 'heatmap',
                        showlabels: false
                    }},
                    hoverinfo: 'skip'
                }};
                
                Plotly.newPlot('plot3_{div_id}', [heatmapTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
                
                // Plot 4: Combined
                const wicketsCombined = {{
                    x: wickets.map(d => d.x),
                    y: wickets.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 7,
                        color: '#ef5350',
                        opacity: 0.8
                    }},
                    hovertemplate: '<b>WICKET</b><br>%{{text}}<extra></extra>',
                    text: wickets.map(d => d.batter)
                }};
                
                const hittingCombined = {{
                    x: hitting.map(d => d.x),
                    y: hitting.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 5,
                        color: '#ff9800',
                        opacity: 0.5
                    }},
                    hovertemplate: '<b>%{{text}} runs</b><extra></extra>',
                    text: hitting.map(d => d.runs)
                }};
                
                Plotly.newPlot('plot4_{div_id}', [hittingCombined, wicketsCombined, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_player_stats_cards(stats_df, title):
        """Render player statistics cards"""
        if stats_df.empty:
            return "<p>No player statistics available</p>"
        div_id = f"player_stats_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        players_data = []
        for idx, row in stats_df.iterrows():
            players_data.append({
                'name': str(row['batter']),
                'runs': int(row['runs_off_bat']),
                'balls': int(row['ball']),
                'sr': float(row['strike_rate']),
                'avg': float(row['average']),
                'fours': int(row['fours']),
                'sixes': int(row['sixes']),
                'dismissals': int(row['is_wicket']),
                'highest': int(row['highest_score'])
            })
        
        data_json = json.dumps(players_data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                .stats-container-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                    gap: 16px;
                    padding: 15px;
                }}
                .player-card-{div_id} {{
                    background: rgba(15, 23, 42, 0.7);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 16px;
                    color: #f8fafc;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }}
                .player-card-{div_id}::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 3px;
                    background: var(--accent-color, #3b82f6);
                }}
                .player-card-{div_id}:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 15px var(--accent-color);
                    border-color: rgba(255, 255, 255, 0.2);
                }}
                .player-rank-{div_id} {{
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                    border: 1px solid rgba(255,255,255,0.2);
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--accent-color);
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }}
                .player-name-{div_id} {{
                    font-size: 17px;
                    font-weight: 700;
                    margin-bottom: 15px;
                    padding-right: 45px;
                    letter-spacing: 0.5px;
                    color: #ffffff;
                }}
                .main-stats-{div_id} {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    padding: 12px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.05);
                }}
                .stat-item-{div_id} {{
                    text-align: center;
                }}
                .stat-value-{div_id} {{
                    font-size: 20px;
                    font-weight: 800;
                    display: block;
                    color: #38bdf8;
                }}
                .stat-label-{div_id} {{
                    font-size: 10px;
                    opacity: 0.7;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .boundaries-{div_id} {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 12px;
                }}
                .boundary-badge-{div_id} {{
                    flex: 1;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 8px;
                    border-radius: 6px;
                    text-align: center;
                    transition: background 0.2s;
                }}
                .boundary-badge-{div_id}:hover {{
                    background: rgba(255, 255, 255, 0.1);
                }}
                .boundary-value-{div_id} {{
                    font-size: 16px;
                    font-weight: 700;
                    display: block;
                    color: #e2e8f0;
                }}
                .boundary-label-{div_id} {{
                    font-size: 9px;
                    opacity: 0.6;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .secondary-stats-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }}
                .secondary-stat-{div_id} {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: 8px 12px;
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    border: 1px solid rgba(255,255,255,0.03);
                }}
                .secondary-stat-{div_id} span {{
                    color: #94a3b8;
                }}
                .secondary-stat-{div_id} strong {{
                    color: #f1f5f9;
                }}
            </style>
        </head>
        <body>
            <div class="stats-container-{div_id}" id="{div_id}"></div>
            
            <script>
            (function() {{
                const players = {data_json};
                const container = document.getElementById('{div_id}');
                
                const neonColors = [
                    '#3b82f6', // blue
                    '#ef4444', // red
                    '#10b981', // emerald
                    '#8b5cf6', // violet
                    '#f97316', // orange
                    '#06b6d4', // cyan
                    '#ec4899', // pink
                    '#84cc16', // lime
                    '#6366f1', // indigo
                    '#14b8a6'  // teal
                ];
                
                players.forEach((player, index) => {{
                    const card = document.createElement('div');
                    card.className = 'player-card-{div_id}';
                    const accentColor = neonColors[index % neonColors.length];
                    card.style.setProperty('--accent-color', accentColor);
                    
                    card.innerHTML = `
                        <div class="player-rank-{div_id}">${{index + 1}}</div>
                        <div class="player-name-{div_id}">${{player.name}}</div>
                        
                        <div class="main-stats-{div_id}">
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}" style="color: ${{accentColor}}">${{player.runs}}</span>
                                <span class="stat-label-{div_id}">Runs</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{player.balls}}</span>
                                <span class="stat-label-{div_id}">Balls</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{player.sr.toFixed(1)}}</span>
                                <span class="stat-label-{div_id}">SR</span>
                            </div>
                        </div>
                        
                        <div class="boundaries-{div_id}">
                            <div class="boundary-badge-{div_id}">
                                <span class="boundary-value-{div_id}">${{player.fours}}</span>
                                <span class="boundary-label-{div_id}">4s</span>
                            </div>
                            <div class="boundary-badge-{div_id}">
                                <span class="boundary-value-{div_id}">${{player.sixes}}</span>
                                <span class="boundary-label-{div_id}">6s</span>
                            </div>
                        </div>
                        
                        <div class="secondary-stats-{div_id}">
                            <div class="secondary-stat-{div_id}">
                                <span>Avg</span>
                                <strong>${{player.avg.toFixed(1)}}</strong>
                            </div>
                            <div class="secondary-stat-{div_id}">
                                <span>Out</span>
                                <strong>${{player.dismissals}}</strong>
                            </div>
                        </div>
                    `;
                    
                    container.appendChild(card);
                }});
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    # -----------------------------------------------------------------------------
    # 4. Main Application
    # -----------------------------------------------------------------------------
    
    # ── Futuristic Top Navigation Bar ─────────────────────────────────────────
    _uname = st.session_state.get("username", "analyst")
    st.markdown(f"""
    <div class="top-nav">
      <div class="nav-brand">🏏 IPL ANALYTICS</div>
      <div style="display:flex;align-items:center;gap:16px">
        <span style="font-size:12px;color:rgba(148,163,184,.6);letter-spacing:1px;text-transform:uppercase">Performance Intelligence</span>
        <div class="nav-user"><span class="nav-dot"></span>{_uname.capitalize()}</div>
      </div>
    </div>
    <style>
        /* Hide the native Streamlit page navigation (app, Login) */
        [data-testid="stSidebarNav"] {{display: none !important;}}
    </style>
    """, unsafe_allow_html=True)
    
    # Logout in sidebar within an expander button
    with st.sidebar:
        with st.expander("👤 Account & Profile", expanded=False):
            st.markdown("""
        <div style="background:rgba(102,126,234,.1);border:1px solid rgba(102,126,234,.2);border-radius:12px;padding:12px 16px;margin-bottom:16px;text-align:center">
          <div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(148,163,184,.7);margin-bottom:4px">Signed in as</div>
          <div style="font-size:15px;font-weight:700;color:#c4b5fd">""" + _uname.capitalize() + """</div>
        </div>
        """, unsafe_allow_html=True)
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
    
    with st.spinner("Loading Data..."):
        df = load_data()
    
    # Sidebar Controls
    st.sidebar.markdown("## ⚙️ Analysis Settings")
    
    # Season/Year Filter
    with st.sidebar.expander("📅 Season Selection", expanded=True):
        filter_mode = "Overall Statistics (2008-Present)"  # Default value
        selected_seasons = []  # Default value
        
        if 'season' in df.columns:
            df['season'] = pd.to_numeric(df['season'], errors='coerce')
            available_seasons = sorted(df['season'].dropna().unique())
            
            filter_mode = st.radio(
                "Filter Mode",
                ["Overall Statistics (2008-Present)", "Specific Season(s)"],
                help="Choose to view all-time stats or filter by specific seasons",
                label_visibility="collapsed"
            )
            
            if filter_mode == "Overall Statistics (2008-Present)":
                st.info(f"📊 Analyzing data from **{int(min(available_seasons))}** to **{int(max(available_seasons))}**\n\n**Total Seasons:** {len(available_seasons)}")
                filtered_df = df.copy()
            else:
                selected_seasons = st.multiselect(
                    "Select Season(s)",
                    options=available_seasons,
                    default=[max(available_seasons)] if available_seasons else [],
                    help="Select one or multiple seasons to analyze"
                )
                
                if selected_seasons:
                    filtered_df = df[df['season'].isin(selected_seasons)]
                    st.success(f"✅ Filtered to {len(selected_seasons)} season(s)")
                else:
                    st.warning("⚠️ No season selected. Showing all data.")
                    filtered_df = df.copy()
        else:
            filtered_df = df.copy()
            st.info("Season data not available in dataset")
    
    with st.sidebar.expander("🏏 Team Selection", expanded=True):
        # Remove NaN values from teams list
        teams = sorted([t for t in filtered_df['batting_team'].unique() if pd.notna(t)])
        
        if len(teams) < 2:
            st.error("⚠️ Not enough teams in selected data. Please adjust filters.")
            st.stop()
        
        team1 = st.selectbox("Team 1", teams, index=0, help="Select first team for comparison")
        
        # Filter team2 options to exclude team1
        team2_options = [t for t in teams if t != team1]
        if team2_options:
            team2 = st.selectbox("Team 2", team2_options, index=0, help="Select second team for comparison")
        else:
            team2 = st.selectbox("Team 2", teams, index=1 if len(teams) > 1 else 0, help="Select second team for comparison")
        
        # Validation check
        if team1 == team2:
            st.warning("⚠️ Same team selected for both. Results may be identical.")
        
    with st.sidebar.expander("🎯 Bowler Analysis", expanded=False):
        bowler_types = ['All Types', 'Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
        bowler_type = st.selectbox("Bowler Type", bowler_types, help="Filter analysis by bowler type", label_visibility="collapsed")
        
    with st.sidebar.expander("⏱️ Match Phase Filter", expanded=False):
        phase_options = ['All Phases', 'Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        selected_phase = st.selectbox(
            "Match Phase",
            phase_options,
            help="Filter analysis by match phase",
            label_visibility="collapsed"
        )
        phase_filter = None if selected_phase == 'All Phases' else selected_phase
    
    # Update df to be filtered_df for all subsequent analysis
    df = filtered_df

    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info("""
    **IPL Analytics Dashboard**
    
    Comprehensive cricket analytics with:
    - 3D visualizations
    - Interactive pitch maps
    - Player performance metrics
    - Advanced statistics
    
    Data Source: Cricsheet
    """)
    
    # Compact summary bar instead of large info block
    st.markdown("---")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📊 Total Matches", f"{df['match_id'].nunique():,}")
    with col_s2:
        st.metric("⚾ Total Balls", f"{len(df):,}")
    with col_s3:
        st.metric(f"🏏 {team1}", f"{len(df[df['batting_team'] == team1]):,} balls")
    with col_s4:
        st.metric(f"🏏 {team2}", f"{len(df[df['batting_team'] == team2]):,} balls")
    
    # =====================================================================
    # SECTION-BASED NAVIGATION (radio buttons — only active section renders)
    # =====================================================================
    active_section = st.radio(
        "📌 Select Analysis Section",
        ["📊 Phase Analysis", "🎯 Pitch Maps & Wagon Wheel", "👤 Player Stats",
         "🎳 Bowling Analysis", "📈 Statistical Charts", "🎬 Animations"],
        horizontal=True, key="main_nav"
    )
    st.markdown("---")
    
    # =====================================================================
    # SECTION 1: Phase Analysis
    # =====================================================================
    if active_section == "📊 Phase Analysis":
        st.markdown("## 📊 Phase Analysis: Run Rate Comparison")
        st.markdown(f"**{team1}** vs **{team2}** — 3D interactive visualization showing run rates across match phases")
    
        t1_stats = calculate_run_rate_by_phase(df, team1)
        t2_stats = calculate_run_rate_by_phase(df, team2)
        phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        
        # Extract run rates for both teams
        t1_rr = [float(t1_stats[t1_stats['phase'] == p]['run_rate'].values[0]) if not t1_stats[t1_stats['phase'] == p].empty else 0.0 for p in phases]
        t2_rr = [float(t2_stats[t2_stats['phase'] == p]['run_rate'].values[0]) if not t2_stats[t2_stats['phase'] == p].empty else 0.0 for p in phases]
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric(f"{team1} Avg Run Rate", f"{t1_stats['run_rate'].mean():.2f}", help="Average run rate across all phases")
        with col_b:
            st.metric(f"{team2} Avg Run Rate", f"{t2_stats['run_rate'].mean():.2f}", help="Average run rate across all phases")
        with col_c:
            diff = t1_stats['run_rate'].mean() - t2_stats['run_rate'].mean()
            st.metric("Difference", f"{abs(diff):.2f}", delta=f"{diff:.2f}")
    
        st.markdown("")
        
        # Simple cool Plotly 2D Grouped Bar Chart
        import plotly.graph_objects as go
        fig = go.Figure()
        
        t1_color = IPL_TEAM_COLORS.get(team1, '#3b82f6')
        t2_color = IPL_TEAM_COLORS.get(team2, '#ef4444')
        
        fig.add_trace(go.Bar(
            x=phases,
            y=t1_rr,
            name=team1,
            marker_color=t1_color,
            text=[f"{rr:.2f}" for rr in t1_rr],
            textposition='auto',
            hovertemplate="%{x}<br>Run Rate: %{y:.2f}<extra></extra>"
        ))
        
        fig.add_trace(go.Bar(
            x=phases,
            y=t2_rr,
            name=team2,
            marker_color=t2_color,
            text=[f"{rr:.2f}" for rr in t2_rr],
            textposition='auto',
            hovertemplate="%{x}<br>Run Rate: %{y:.2f}<extra></extra>"
        ))
        
        fig.update_layout(
            barmode='group',
            title=dict(
                text="<b>Run Rate Comparison by Phase</b>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(showgrid=False, tickfont=dict(size=13, color='#cbd5e1')),
            yaxis=dict(
                title="Run Rate (Runs per Over)",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)',
                font=dict(size=13)
            ),
            margin=dict(t=80, b=40, l=40, r=20),
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
        # Matchup Analysis
        st.markdown("---")
        st.subheader(f"🎯 Player Matchups vs {bowler_type}")
        c1, c2 = st.columns(2)
    
        with c1:
            st.markdown(f"**{team1} Top Batters**")
            batters1_df = get_top_batters(df, team1, n=5)
            if not batters1_df.empty:
                batters1 = batters1_df['batter'].tolist()
                m1_data = []
                for b in batters1:
                    s = calculate_player_matchup(df, b, bowler_type)
                    if s: 
                        m1_data.append({'label': str(b), 'value': float(s['strike_rate']),
                            'balls': int(s['balls_faced']), 'runs': int(s['runs_scored']),
                            'dismissals': int(s['dismissals'])})
                if m1_data:
                    components.html(render_threejs_chart(m1_data, 'bar_3d', f"{team1} vs {bowler_type}", 450, 400), height=450)
                    st.dataframe(pd.DataFrame(m1_data)[['label', 'runs', 'balls', 'value']].rename(
                        columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}), hide_index=True)
                else:
                    st.info(f"No data for {team1} vs {bowler_type}")
            else:
                st.warning(f"No batters found for {team1}")
    
        with c2:
            st.markdown(f"**{team2} Top Batters**")
            batters2_df = get_top_batters(df, team2, n=5)
            if not batters2_df.empty:
                batters2 = batters2_df['batter'].tolist()
                m2_data = []
                for b in batters2:
                    s = calculate_player_matchup(df, b, bowler_type)
                    if s: 
                        m2_data.append({'label': str(b), 'value': float(s['strike_rate']),
                            'balls': int(s['balls_faced']), 'runs': int(s['runs_scored']),
                            'dismissals': int(s['dismissals'])})
                if m2_data:
                    components.html(render_threejs_chart(m2_data, 'bar_3d', f"{team2} vs {bowler_type}", 450, 400), height=450)
                    st.dataframe(pd.DataFrame(m2_data)[['label', 'runs', 'balls', 'value']].rename(
                        columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}), hide_index=True)
                else:
                    st.info(f"No data for {team2} vs {bowler_type}")
            else:
                st.warning(f"No batters found for {team2}")
    
        # Runs Distribution
        st.subheader("📈 Runs Distribution")
        d1, d2 = st.columns(2)
        
        import plotly.graph_objects as go
        
        def create_donut_chart(data_series, title, team_name):
            team_color = IPL_TEAM_COLORS.get(team_name, '#3b82f6')
            hex_c = team_color.lstrip('#')
            if len(hex_c) == 6:
                r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
            else:
                r, g, b = 59, 130, 246
                
            colors = {
                '0': f"rgba({r},{g},{b},0.15)",
                '1': f"rgba({r},{g},{b},0.35)",
                '2': f"rgba({r},{g},{b},0.55)",
                '3': f"rgba({r},{g},{b},0.70)",
                '4': f"rgba({r},{g},{b},0.85)",
                '6': f"rgba({r},{g},{b},1.0)"
            }
            labels = [str(k) for k in data_series.index]
            values = data_series.values
            marker_colors = [colors.get(l, '#94a3b8') for l in labels]
            
            # Map labels to human-readable names
            label_map = {'0': 'Dots (0)', '1': 'Singles (1)', '2': 'Twos (2)', '3': 'Threes (3)', '4': 'Fours (4)', '6': 'Sixes (6)'}
            display_labels = [label_map.get(l, f"{l} Runs") for l in labels]
            
            fig = go.Figure(data=[go.Pie(
                labels=display_labels,
                values=values,
                hole=0.55,
                marker=dict(colors=marker_colors, line=dict(color='#0f172a', width=2)),
                textposition='inside',
                textinfo='percent',
                hoverinfo='label+value+percent',
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
            )])
            
            fig.update_layout(
                title=dict(text=f"<b>{title}</b>", x=0.5, font=dict(size=15, color='#f8fafc')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family='Segoe UI'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                margin=dict(t=50, b=40, l=20, r=20),
                height=350
            )
            # Add center text
            fig.add_annotation(
                text=f"Total<br><b>{sum(values)}</b>",
                x=0.5, y=0.5,
                font=dict(size=16, color='#f8fafc'),
                showarrow=False
            )
            return fig

        with d1:
            rd1 = df[df['batting_team'] == team1]['runs_off_bat'].value_counts().sort_index()
            st.plotly_chart(create_donut_chart(rd1, f"{team1} Runs Breakdown", team1), use_container_width=True)
            
        with d2:
            rd2 = df[df['batting_team'] == team2]['runs_off_bat'].value_counts().sort_index()
            st.plotly_chart(create_donut_chart(rd2, f"{team2} Runs Breakdown", team2), use_container_width=True)
    
    # =====================================================================
    # SECTION 2: Pitch Maps & Wagon Wheel
    # =====================================================================
    if active_section == "🎯 Pitch Maps & Wagon Wheel":
        phase_val = None if selected_phase == 'All Phases' else selected_phase
    
        st.subheader("🎯 Advanced Pitch Maps - Multi-Panel Analysis")
        st.markdown("_4-panel view: Wickets, Hitting, Density Heat Map, and Combined (2×2 grid)_")
        st.markdown(f"### {team1} - Advanced Pitch Analysis")
        pitch_data1 = generate_pitch_map_data_complete(df, team=team1, bowler_type=bowler_type, phase=phase_val)
        if pitch_data1:
            components.html(render_advanced_pitch_viz(pitch_data1, f"{team1} - {selected_phase}", 1200, 900), height=960)
            st.caption(f"📊 Deliveries: {len(pitch_data1)} | Wickets: {sum(1 for d in pitch_data1 if d['wicket'] == 1)}")
        else:
            st.info(f"No data available for {team1}")
        st.markdown(f"### {team2} - Advanced Pitch Analysis")
        pitch_data2 = generate_pitch_map_data_complete(df, team=team2, bowler_type=bowler_type, phase=phase_val)
        if pitch_data2:
            components.html(render_advanced_pitch_viz(pitch_data2, f"{team2} - {selected_phase}", 1200, 900), height=960)
            st.caption(f"📊 Deliveries: {len(pitch_data2)} | Wickets: {sum(1 for d in pitch_data2 if d['wicket'] == 1)}")
        else:
            st.info(f"No data available for {team2}")
    
        # Stumps View
        st.markdown("---")
        st.subheader("🎯 Stumps View - Line & Length Analysis")
        sv1, sv2 = st.columns(2)
        with sv1:
            st.markdown(f"**{team1} Stumps View**")
            stumps_data1 = generate_stumps_view_data(df, team=team1, phase=phase_val)
            if stumps_data1:
                components.html(render_stumps_view(stumps_data1, f"{team1} - {selected_phase}", 500, 600), height=650)
            else:
                st.info(f"No data available for {team1}")
        with sv2:
            st.markdown(f"**{team2} Stumps View**")
            stumps_data2 = generate_stumps_view_data(df, team=team2, phase=phase_val)
            if stumps_data2:
                components.html(render_stumps_view(stumps_data2, f"{team2} - {selected_phase}", 500, 600), height=650)
            else:
                st.info(f"No data available for {team2}")
    
        # Wagon Wheel
        st.markdown("---")
        st.subheader("⚾ Wagon Wheel - Shot Directions & Scoring Zones")
        ww1, ww2 = st.columns(2)
        with ww1:
            st.markdown(f"**{team1} Wagon Wheel**")
            wagon_data1 = generate_wagon_wheel_data(df, team=team1, phase=phase_val)
            if wagon_data1:
                components.html(render_wagon_wheel(wagon_data1, f"{team1} - {selected_phase}", 600, 600), height=650)
                st.caption(f"📊 Total scoring shots: {len(wagon_data1)}")
            else:
                st.info(f"No data available for {team1}")
        with ww2:
            st.markdown(f"**{team2} Wagon Wheel**")
            wagon_data2 = generate_wagon_wheel_data(df, team=team2, phase=phase_val)
            if wagon_data2:
                components.html(render_wagon_wheel(wagon_data2, f"{team2} - {selected_phase}", 600, 600), height=650)
                st.caption(f"📊 Total scoring shots: {len(wagon_data2)}")
            else:
                st.info(f"No data available for {team2}")
    
    # =====================================================================
    # SECTION 3: Player Stats
    # =====================================================================
    if active_section == "👤 Player Stats":
        st.markdown("## 📊 Player Statistics - Top Performers")
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        st.markdown(f"### {team1} - Top Batters")
        stats1 = get_player_statistics(df, team1, phase=phase_val)
        if not stats1.empty:
            components.html(render_player_stats_cards(stats1, f"{team1}"), height=900, scrolling=True)
            st.caption(f"📈 Showing top {len(stats1)} batters with minimum 30 balls faced")
        else:
            st.info(f"No player statistics available for {team1}")
        st.markdown(f"### {team2} - Top Batters")
        stats2 = get_player_statistics(df, team2, phase=phase_val)
        if not stats2.empty:
            components.html(render_player_stats_cards(stats2, f"{team2}"), height=900, scrolling=True)
            st.caption(f"📈 Showing top {len(stats2)} batters with minimum 30 balls faced")
        else:
            st.info(f"No player statistics available for {team2}")
    
    # =====================================================================
    # SECTION 4: Bowling Analysis
    # =====================================================================
    if active_section == "🎳 Bowling Analysis":
        st.markdown("## 🎳 Bowling Length Analysis - 3D Pitch Zones")
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} Bowling Length**")
            bowling_html_1 = render_bowling_length_map(df, team1, phase=phase_val, unique_id="team1_bowling")
            components.html(bowling_html_1, height=800, scrolling=True)
        with col2:
            st.markdown(f"**{team2} Bowling Length**")
            bowling_html_2 = render_bowling_length_map(df, team2, phase=phase_val, unique_id="team2_bowling")
            components.html(bowling_html_2, height=800, scrolling=True)
    
    # =====================================================================
    # SECTION 5: Statistical Charts
    # =====================================================================
    if active_section == "📈 Statistical Charts":
        st.markdown("## 📈 Statistical Analysis - Interactive Altair Charts")
        phase_val = None if selected_phase == 'All Phases' else selected_phase
    
        st.markdown("### 📊 Runs Distribution Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} - Runs per Ball Distribution**")
            runs_chart_1 = create_runs_distribution_chart(df, team1, phase=phase_val)
            if runs_chart_1:
                st.plotly_chart(runs_chart_1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No data available")
        with col2:
            st.markdown(f"**{team2} - Runs per Ball Distribution**")
            runs_chart_2 = create_runs_distribution_chart(df, team2, phase=phase_val)
            if runs_chart_2:
                st.plotly_chart(runs_chart_2, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No data available")
    
        st.markdown("### ⚡ Strike Rate Comparison - Top Performers")
        strike_rate_chart = create_strike_rate_comparison(df, phase=phase_val)
        if strike_rate_chart:
            st.plotly_chart(strike_rate_chart, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 🎯 Boundary & Dot Ball Analysis")
        boundary_chart = create_boundary_percentage_chart(df, [team1, team2], phase=phase_val)
        if boundary_chart:
            st.plotly_chart(boundary_chart, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 📈 Runs Progression Over Overs")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} - Over-by-Over Progression**")
            progression_1 = create_runs_over_progression(df, team1, phase=phase_val)
            if progression_1:
                st.plotly_chart(progression_1, use_container_width=True, config={'displayModeBar': False})
        with col2:
            st.markdown(f"**{team2} - Over-by-Over Progression**")
            progression_2 = create_runs_over_progression(df, team2, phase=phase_val)
            if progression_2:
                st.plotly_chart(progression_2, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 🎯 Wicket Fall Timeline")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} Bowling - Wickets Timeline**")
            wicket_chart_1 = create_wicket_timeline(df, team1, phase=phase_val)
            if wicket_chart_1:
                st.plotly_chart(wicket_chart_1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info(f"No wickets data available for {team1}")
        with col2:
            st.markdown(f"**{team2} Bowling - Wickets Timeline**")
            wicket_chart_2 = create_wicket_timeline(df, team2, phase=phase_val)
            if wicket_chart_2:
                st.plotly_chart(wicket_chart_2, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info(f"No wickets data available for {team2}")
    
        st.markdown("### 💰 Bowler Economy Rate Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} - Bowler Economy Rates**")
            economy_chart_1 = create_bowler_economy_chart(df, team1, phase=phase_val)
            if economy_chart_1:
                st.altair_chart(economy_chart_1, use_container_width=True)
        with col2:
            st.markdown(f"**{team2} - Bowler Economy Rates**")
            economy_chart_2 = create_bowler_economy_chart(df, team2, phase=phase_val)
            if economy_chart_2:
                st.altair_chart(economy_chart_2, use_container_width=True)
    
    # =====================================================================
    # SECTION 6: Animations
    # =====================================================================
    # 3D Ball Trajectory Animation Section
    # =====================================================================
    if active_section == "🎬 Animations":
        st.markdown("## 🎬 3D Interactive Ball Trajectory Animation")
        st.markdown("""Explore an **interactive 3D animation** showing cricket ball trajectories 
        from the stumps view with different lines and lengths. You can rotate and zoom the camera while it plays!""")
        
        with st.container():
            fig = create_3d_animated_trajectory()
            st.plotly_chart(fig, use_container_width=True)
