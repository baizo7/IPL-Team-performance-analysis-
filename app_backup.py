import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import uuid
import altair as alt
import streamlit.components.v1 as components
import tempfile

# Set page configuration
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Auth Gate ──────────────────────────────────────────────────────────────
VALID_USERS = {"admin": "ipl2024", "analyst": "cricket123", "demo": "demo"}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
.main .block-container{padding-top:0!important;max-width:100%!important}
header[data-testid="stHeader"]{display:none!important}
section[data-testid="stSidebar"]{display:none!important}
#MainMenu,footer{visibility:hidden}
.stApp{background:#030712;font-family:'Inter',sans-serif}
/* bg grid */
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(102,126,234,.07)1px,transparent 1px),linear-gradient(90deg,rgba(102,126,234,.07)1px,transparent 1px);background-size:44px 44px;animation:gs 25s linear infinite;z-index:0}
@keyframes gs{from{background-position:0 0}to{background-position:44px 44px}}
/* orbs */
body::after{content:'';position:fixed;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(102,126,234,.18) 0%,transparent 70%);top:-200px;left:-150px;filter:blur(60px);z-index:0;animation:orb 10s ease-in-out infinite alternate}
@keyframes orb{from{transform:scale(1)}to{transform:scale(1.2)}}
.login-card{position:relative;z-index:10;max-width:460px;margin:0 auto;background:rgba(15,23,42,.88);backdrop-filter:blur(24px);border:1px solid rgba(102,126,234,.25);border-radius:24px;padding:44px 40px 36px;box-shadow:0 25px 50px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.05);animation:ci .7s cubic-bezier(.16,1,.3,1)}
@keyframes ci{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:translateY(0)}}
.brand-icon{width:54px;height:54px;border-radius:14px;background:linear-gradient(135deg,#667eea,#764ba2);display:inline-flex;align-items:center;justify-content:center;font-size:28px;box-shadow:0 0 24px rgba(102,126,234,.45);margin-bottom:12px}
.brand-name{font-family:'Orbitron',monospace;font-size:22px;font-weight:900;letter-spacing:2px;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.brand-tag{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:rgba(148,163,184,.65);font-weight:600;margin-top:2px}
.login-title{font-size:26px;font-weight:700;color:#f1f5f9;margin:24px 0 4px;letter-spacing:-.5px}
.login-sub{font-size:13px;color:rgba(148,163,184,.75);margin-bottom:28px}
.fl{font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:rgba(148,163,184,.85);margin-bottom:6px}
.stTextInput>div>div>input{background:rgba(30,41,59,.85)!important;border:1px solid rgba(102,126,234,.25)!important;border-radius:12px!important;color:#f1f5f9!important;padding:13px 15px!important;font-size:15px!important;transition:all .25s ease!important}
.stTextInput>div>div>input:focus{border-color:rgba(102,126,234,.8)!important;box-shadow:0 0 0 3px rgba(102,126,234,.15)!important}
.stTextInput>div>div>input::placeholder{color:rgba(100,116,139,.6)!important}
.stButton>button{width:100%!important;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb)!important;background-size:200% 200%!important;color:white!important;border:none!important;border-radius:12px!important;padding:14px!important;font-size:15px!important;font-weight:700!important;letter-spacing:.5px!important;box-shadow:0 4px 25px rgba(102,126,234,.4)!important;transition:all .3s ease!important;animation:gbg 4s ease infinite}
@keyframes gbg{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 35px rgba(102,126,234,.6)!important}
.demo-box{background:rgba(102,126,234,.08);border:1px solid rgba(102,126,234,.2);border-radius:12px;padding:14px 18px;display:flex;gap:20px;flex-wrap:wrap;margin-top:24px}
.demo-item{flex:1;text-align:center}
.demo-lbl{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(102,126,234,.7);font-weight:600}
.demo-val{font-size:15px;color:#c4b5fd;font-weight:600;margin-top:3px;font-family:monospace}
.stat-strip{display:flex;margin-top:28px;border-top:1px solid rgba(102,126,234,.15);padding-top:22px}
.sc{flex:1;text-align:center;padding:0 6px;border-right:1px solid rgba(102,126,234,.1)}
.sc:last-child{border-right:none}
.sn{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sd{font-size:10px;color:rgba(100,116,139,.7);letter-spacing:1px;text-transform:uppercase;margin-top:3px}
</style>
""", unsafe_allow_html=True)

    # center the card
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
<div class="login-card">
  <div class="brand-icon">🏏</div>
  <div class="brand-name">IPL ANALYTICS</div>
  <div class="brand-tag">Performance Intelligence Platform</div>
  <div class="login-title">Welcome Back</div>
  <div class="login-sub">Sign in to access your analytics dashboard</div>
</div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<div class="fl">Username</div>', unsafe_allow_html=True)
            uname = st.text_input("Username", placeholder="e.g. demo", label_visibility="collapsed", key="li_u")
            st.markdown('<div class="fl" style="margin-top:14px">Password</div>', unsafe_allow_html=True)
            pwd = st.text_input("Password", placeholder="Enter password", type="password", label_visibility="collapsed", key="li_p")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("⚡  Sign In to Dashboard", use_container_width=True)

        if submitted:
            if uname in VALID_USERS and VALID_USERS[uname] == pwd:
                st.session_state.authenticated = True
                st.session_state.username = uname
                st.success(f"✅ Welcome **{uname}**! Loading dashboard…")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try demo / demo")

        st.markdown("""
<div class="demo-box">
  <div class="demo-item"><div class="demo-lbl">Username</div><div class="demo-val">demo</div></div>
  <div class="demo-item"><div class="demo-lbl">Password</div><div class="demo-val">demo</div></div>
  <div class="demo-item"><div class="demo-lbl">Access</div><div class="demo-val">Full</div></div>
</div>
<div class="stat-strip">
  <div class="sc"><div class="sn">17</div><div class="sd">Seasons</div></div>
  <div class="sc"><div class="sn">1200+</div><div class="sd">Matches</div></div>
  <div class="sc"><div class="sn">6M+</div><div class="sd">Balls</div></div>
  <div class="sc"><div class="sn">800+</div><div class="sd">Players</div></div>
</div>
""", unsafe_allow_html=True)

    st.stop()

# ── Futuristic Dashboard CSS (post-login) ──────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* === Base === */
.main .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:100%}
.stApp{font-family:'Inter',sans-serif;background:#030712}
/* === Animated Grid bg === */
.stApp::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(102,126,234,.05)1px,transparent 1px),linear-gradient(90deg,rgba(102,126,234,.05)1px,transparent 1px);background-size:50px 50px;animation:gbg 30s linear infinite;pointer-events:none;z-index:0}
@keyframes gbg{from{background-position:0 0}to{background-position:50px 50px}}
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
    
    # Sample data if too large (for performance)
    if len(filtered_df) > 500:
        filtered_df = filtered_df.sample(500, random_state=42)
    
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
    """Create comprehensive runs distribution analysis from scratch"""
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
    
    # Create color mapping for different run types
    def get_run_color(runs):
        if runs == 0:
            return '#808080'  # Gray for dots
        elif runs == 1:
            return '#00ff00'  # Green for singles
        elif runs == 2:
            return '#2196f3'  # Blue for twos
        elif runs == 3:
            return '#ff9800'  # Orange for threes
        elif runs == 4:
            return '#9c27b0'  # Purple for fours
        elif runs == 6:
            return '#ff0000'  # Red for sixes
        else:
            return '#ffc107'  # Yellow for others
    
    runs_counts['color'] = runs_counts['runs'].apply(get_run_color)
    
    # Create run type labels
    def get_run_label(runs):
        if runs == 0:
            return 'Dot Balls'
        elif runs == 1:
            return 'Singles'
        elif runs == 2:
            return 'Twos'
        elif runs == 3:
            return 'Threes'
        elif runs == 4:
            return 'Fours'
        elif runs == 6:
            return 'Sixes'
        else:
            return f'{int(runs)} Runs'
    
    runs_counts['label'] = runs_counts['runs'].apply(get_run_label)
    
    # Calculate summary statistics
    total_runs = int(team_data['runs_off_bat'].sum())
    avg_runs_per_ball = round(total_runs / total_balls, 2)
    dots = int(len(team_data[team_data['runs_off_bat'] == 0]))
    boundaries = int(len(team_data[(team_data['runs_off_bat'] == 4) | (team_data['runs_off_bat'] == 6)]))
    dot_pct = round((dots / total_balls) * 100, 1)
    boundary_pct = round((boundaries / total_balls) * 100, 1)
    
    # Create the main bar chart
    bars = alt.Chart(runs_counts).mark_bar(
        cornerRadiusTopLeft=8,
        cornerRadiusTopRight=8,
        opacity=0.9,
        size=45
    ).encode(
        x=alt.X('runs:O', 
                title='Runs Scored per Ball',
                axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
        y=alt.Y('count:Q', 
                title='Number of Balls',
                axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
        color=alt.Color('color:N',
                       scale=None,  # Use custom colors
                       legend=None),
        tooltip=[
            alt.Tooltip('label:N', title='📊 Type'),
            alt.Tooltip('runs:Q', title='🏏 Runs'),
            alt.Tooltip('count:Q', title='⚾ Balls'),
            alt.Tooltip('percentage:Q', title='📈 Percentage', format='.1f'),
            alt.Tooltip('cumulative_pct:Q', title='📊 Cumulative %', format='.1f')
        ]
    )
    
    # Add text labels on top of bars showing count
    count_text = alt.Chart(runs_counts).mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=13,
        fontWeight='bold',
        color='#333333'
    ).encode(
        x=alt.X('runs:O'),
        y=alt.Y('count:Q'),
        text=alt.Text('count:Q')
    )
    
    # Add percentage labels
    pct_text = alt.Chart(runs_counts).mark_text(
        align='center',
        baseline='bottom',
        dy=-20,
        fontSize=11,
        color='#666666',
        fontStyle='italic'
    ).encode(
        x=alt.X('runs:O'),
        y=alt.Y('count:Q'),
        text=alt.Text('percentage:Q', format='.1f%')
    )
    
    # Combine all layers
    chart = (bars + count_text + pct_text).properties(
        width=700,
        height=450,
        title={
            'text': [f'{team} - Runs Distribution per Ball'],
            'subtitle': [
                f'Total Balls: {total_balls} | Total Runs: {total_runs} | Avg: {avg_runs_per_ball}',
                f'Dot Balls: {dot_pct}% | Boundaries: {boundary_pct}%'
            ],
            'fontSize': 18,
            'fontWeight': 'bold',
            'subtitleFontSize': 12,
            'subtitleColor': '#555555',
            'anchor': 'start',
            'offset': 15
        }
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        titleFontWeight='bold',
        gridOpacity=0.3
    ).configure_view(
        strokeWidth=0,
        fill='#fafafa'
    ).interactive()
    
    return chart

def create_strike_rate_comparison(df, phase=None):
    """Create strike rate comparison chart for top batters across teams"""
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
    batter_stats = batter_stats.sort_values('strike_rate', ascending=False).head(15)
    
    chart = alt.Chart(batter_stats).mark_bar().encode(
        x=alt.X('strike_rate:Q', title='Strike Rate', scale=alt.Scale(domain=[0, 250])),
        y=alt.Y('batter:N', sort='-x', title='Batter'),
        color=alt.Color('batting_team:N', title='Team', scale=alt.Scale(scheme='category20')),
        tooltip=[
            alt.Tooltip('batter:N', title='Player'),
            alt.Tooltip('batting_team:N', title='Team'),
            alt.Tooltip('strike_rate:Q', title='Strike Rate', format='.2f'),
            alt.Tooltip('runs_off_bat:Q', title='Total Runs'),
            alt.Tooltip('ball:Q', title='Balls Faced')
        ]
    ).properties(
        width=700,
        height=500,
        title='Top 15 Batters by Strike Rate (min 50 balls)'
    ).interactive()
    
    return chart

def create_boundary_percentage_chart(df, teams, phase=None):
    """Create comprehensive boundary and dot ball analysis from scratch"""
    results = []
    
    # Collect data for each team
    for team in teams:
        team_data = df[df['batting_team'] == team].copy()
        
        # Apply phase filter if specified
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        total_balls = len(team_data)
        if total_balls == 0:
            continue
        
        # Calculate detailed statistics
        fours = len(team_data[team_data['runs_off_bat'] == 4])
        sixes = len(team_data[team_data['runs_off_bat'] == 6])
        dots = len(team_data[team_data['runs_off_bat'] == 0])
        singles = len(team_data[team_data['runs_off_bat'] == 1])
        twos = len(team_data[team_data['runs_off_bat'] == 2])
        threes = len(team_data[team_data['runs_off_bat'] == 3])
        
        # Calculate totals
        total_boundaries = fours + sixes
        total_runs_from_boundaries = (fours * 4) + (sixes * 6)
        total_runs = int(team_data['runs_off_bat'].sum())
        
        # Calculate percentages
        four_pct = round((fours / total_balls) * 100, 1)
        six_pct = round((sixes / total_balls) * 100, 1)
        boundary_pct = round((total_boundaries / total_balls) * 100, 1)
        dot_pct = round((dots / total_balls) * 100, 1)
        scoring_pct = round(((total_balls - dots) / total_balls) * 100, 1)
        boundary_runs_pct = round((total_runs_from_boundaries / total_runs) * 100, 1) if total_runs > 0 else 0
        
        # Add rows for each category
        results.append({
            'team': team,
            'category': 'Fours (4s)',
            'type': 'Boundary',
            'count': fours,
            'percentage': four_pct,
            'color': '#9c27b0'
        })
        results.append({
            'team': team,
            'category': 'Sixes (6s)',
            'type': 'Boundary',
            'count': sixes,
            'percentage': six_pct,
            'color': '#ff0000'
        })
        results.append({
            'team': team,
            'category': 'Dot Balls',
            'type': 'Defense',
            'count': dots,
            'percentage': dot_pct,
            'color': '#808080'
        })
        results.append({
            'team': team,
            'category': 'Singles (1s)',
            'type': 'Rotation',
            'count': singles,
            'percentage': round((singles / total_balls) * 100, 1),
            'color': '#00ff00'
        })
        results.append({
            'team': team,
            'category': 'Twos (2s)',
            'type': 'Running',
            'count': twos,
            'percentage': round((twos / total_balls) * 100, 1),
            'color': '#2196f3'
        })
    
    if len(results) == 0:
        return None
    
    chart_df = pd.DataFrame(results)
    
    # Create grouped bar chart
    bars = alt.Chart(chart_df).mark_bar(
        cornerRadiusTopLeft=8,
        cornerRadiusTopRight=8,
        opacity=0.9
    ).encode(
        x=alt.X('category:N', 
                title='Ball Type',
                axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
        y=alt.Y('percentage:Q', 
                title='Percentage of Balls (%)',
                axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
        xOffset=alt.XOffset('team:N', title='Team'),
        color=alt.Color('team:N',
                       title='Team',
                       scale=alt.Scale(scheme='set2'),
                       legend=alt.Legend(
                           orient='top',
                           titleFontSize=13,
                           labelFontSize=12
                       )),
        tooltip=[
            alt.Tooltip('team:N', title='🏏 Team'),
            alt.Tooltip('category:N', title='📊 Category'),
            alt.Tooltip('count:Q', title='⚾ Count'),
            alt.Tooltip('percentage:Q', title='📈 Percentage', format='.1f'),
        ]
    )
    
    # Add text labels showing percentages
    text = alt.Chart(chart_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=11,
        fontWeight='bold',
        color='#333333'
    ).encode(
        x=alt.X('category:N'),
        y=alt.Y('percentage:Q'),
        xOffset=alt.XOffset('team:N'),
        text=alt.Text('percentage:Q', format='.1f')
    )
    
    # Combine layers
    chart = (bars + text).properties(
        width=800,
        height=500,
        title={
            'text': ['Boundary & Dot Ball Analysis - Team Comparison'],
            'subtitle': [
                'Compare attacking intent (boundaries) vs defensive play (dots) between teams',
                'Higher boundary % = More aggressive | Higher dot % = More defensive'
            ],
            'fontSize': 18,
            'fontWeight': 'bold',
            'subtitleFontSize': 12,
            'subtitleColor': '#555555',
            'anchor': 'start',
            'offset': 15
        }
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=14,
        titleFontWeight='bold',
        gridOpacity=0.3
    ).configure_view(
        strokeWidth=0,
        fill='#fafafa'
    ).interactive()
    
    return chart

def create_runs_over_progression(df, team, phase=None):
    """Create runs progression over overs using Altair"""
    team_data = df[df['batting_team'] == team].copy()
    if phase:
        team_data = team_data[team_data['phase'] == phase]
    
    # Group by over and calculate cumulative runs
    over_runs = team_data.groupby('over')['runs_off_bat'].sum().reset_index()
    over_runs['cumulative_runs'] = over_runs['runs_off_bat'].cumsum()
    
    # Line chart for cumulative runs
    line = alt.Chart(over_runs).mark_line(
        color='#667eea',
        strokeWidth=3,
        point=alt.OverlayMarkDef(color='#764ba2', size=60)
    ).encode(
        x=alt.X('over:Q', title='Over', scale=alt.Scale(domain=[0, 20])),
        y=alt.Y('cumulative_runs:Q', title='Cumulative Runs'),
        tooltip=[
            alt.Tooltip('over:Q', title='Over'),
            alt.Tooltip('runs_off_bat:Q', title='Runs in Over'),
            alt.Tooltip('cumulative_runs:Q', title='Total Runs')
        ]
    )
    
    # Bar chart for runs per over
    bars = alt.Chart(over_runs).mark_bar(
        opacity=0.3,
        color='#f093fb'
    ).encode(
        x=alt.X('over:Q', title='Over'),
        y=alt.Y('runs_off_bat:Q', title='Runs per Over'),
        tooltip=[
            alt.Tooltip('over:Q', title='Over'),
            alt.Tooltip('runs_off_bat:Q', title='Runs')
        ]
    )
    
    chart = (bars + line).properties(
        width=700,
        height=400,
        title=f'{team} - Runs Progression Over Overs'
    ).interactive()
    
    return chart

def create_wicket_timeline(df, bowling_team, phase=None):
    """Create wicket fall timeline using Altair"""
    team_data = df[df['bowling_team'] == bowling_team].copy()
    if phase:
        team_data = team_data[team_data['phase'] == phase]
    
    wickets = team_data[team_data['is_wicket'] == 1].copy()
    
    if wickets.empty:
        return None
    
    wickets['wicket_num'] = range(1, len(wickets) + 1)
    
    chart = alt.Chart(wickets).mark_circle(size=200).encode(
        x=alt.X('over:Q', title='Over', scale=alt.Scale(domain=[0, 20])),
        y=alt.Y('wicket_num:Q', title='Wicket Number'),
        color=alt.Color('wicket_type:N', title='Dismissal Type', scale=alt.Scale(scheme='set2')),
        tooltip=[
            alt.Tooltip('over:Q', title='Over'),
            alt.Tooltip('batter:N', title='Batter Out'),
            alt.Tooltip('bowler:N', title='Bowler'),
            alt.Tooltip('wicket_type:N', title='Dismissal')
        ]
    ).properties(
        width=700,
        height=400,
        title=f'{bowling_team} - Wicket Fall Timeline'
    ).interactive()
    
    return chart

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
    
    # Create the base chart
    base = alt.Chart(bowler_stats).encode(
        y=alt.Y('bowler:N', 
                sort=alt.EncodingSortField(field='economy', order='ascending'),
                title='Bowler',
                axis=alt.Axis(labelLimit=200, labelFontSize=11))
    )
    
    # Create horizontal bars with color gradient
    bars = base.mark_bar(
        cornerRadiusTopLeft=10,
        cornerRadiusTopRight=10,
        size=30,
        opacity=0.9
    ).encode(
        x=alt.X('economy:Q', 
                title='Economy Rate (Runs per Over)', 
                scale=alt.Scale(domain=[0, max(15, bowler_stats['economy'].max() + 1)])),
        color=alt.Color('economy:Q',
                       scale=alt.Scale(
                           domain=[4, 6, 8, 10, 12, 15],
                           range=['#00ff00', '#7fff00', '#ffff00', '#ffa500', '#ff6347', '#ff0000']
                       ),
                       legend=alt.Legend(
                           title='Economy Rate',
                           orient='right',
                           titleFontSize=12,
                           labelFontSize=11
                       )),
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
        fontSize=12,
        fontWeight='bold',
        color='#333333'
    ).encode(
        x=alt.X('economy:Q'),
        text=alt.Text('economy:Q', format='.2f')
    )
    
    # Add wickets count as secondary text
    wicket_labels = base.mark_text(
        align='left',
        baseline='middle',
        dx=50,
        fontSize=10,
        color='#666666',
        fontStyle='italic'
    ).encode(
        x=alt.X('economy:Q'),
        text=alt.Text('is_wicket:Q', format='W')
    )
    
    # Combine all layers
    chart = (bars + text_labels + wicket_labels).properties(
        width=800,
        height=550,
        title={
            'text': [f'{team} - Bowler Economy Rate Analysis'],
            'subtitle': [
                'Best economy rates ranked (minimum 4 overs bowled)',
                'Lower economy = Better bowling performance'
            ],
            'fontSize': 20,
            'fontWeight': 'bold',
            'subtitleFontSize': 13,
            'subtitleColor': '#555555',
            'anchor': 'start',
            'offset': 20
        }
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=14,
        titleFontWeight='bold',
        gridOpacity=0.3
    ).configure_view(
        strokeWidth=0,
        fill='#fafafa'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=11,
        symbolSize=200,
        padding=10
    ).interactive()
    
    return chart

# -----------------------------------------------------------------------------
# Manim Cricket Ball Animation
# -----------------------------------------------------------------------------

# Manim is lazy-loaded only when animation is requested
def _get_manim_scene_class():
    from manim import Scene, Text, Write, Rectangle, VGroup, Line, Circle, Flash, Create, FadeIn, FadeOut
    from manim import WHITE, BLUE_E, RED, YELLOW, GREEN, BLUE, ORANGE, UP, DOWN, DR
    from manim import rush_into
    import numpy as np

    class CricketBallTrajectory(Scene):
        """Manim animation showing cricket ball trajectory from stumps view"""
        
        def construct(self):
            # Set background
            self.camera.background_color = "#1a1a2e"
            
            # Title
            title = Text("Cricket Ball Trajectory - Stumps View", font_size=36, color=WHITE)
            title.to_edge(UP)
            self.play(Write(title), run_time=1)
            self.wait(0.5)
            
            # Create pitch outline (stumps view - looking down the pitch)
            pitch_width = 6
            pitch_height = 8
            pitch = Rectangle(
                width=pitch_width, 
                height=pitch_height,
                color="#8B6F47",
                fill_opacity=0.3,
                stroke_color=WHITE,
                stroke_width=2
            )
            pitch.shift(DOWN * 0.5)
            
            # Stumps at bottom
            stump_positions = [-0.3, 0, 0.3]
            stumps = VGroup()
            for x_pos in stump_positions:
                stump = Rectangle(
                    width=0.15,
                    height=0.8,
                    color=WHITE,
                    fill_opacity=1,
                    stroke_width=2
                )
                stump.move_to([x_pos, -pitch_height/2 + 0.4, 0])
                stumps.add(stump)
            
            # Bails on top of stumps
            bail = Rectangle(width=1, height=0.1, color=WHITE, fill_opacity=1)
            bail.move_to([0, -pitch_height/2 + 0.85, 0])
            
            # Draw pitch and stumps
            self.play(Create(pitch), run_time=0.8)
            self.play(Create(stumps), Create(bail), run_time=0.6)
            
            # Create grid for line and length zones
            grid_lines = VGroup()
            
            # Vertical lines (line)
            for x in np.linspace(-pitch_width/2, pitch_width/2, 5):
                line = Line(
                    start=[x, -pitch_height/2, 0],
                    end=[x, pitch_height/2, 0],
                    color=BLUE_E,
                    stroke_width=1,
                    stroke_opacity=0.3
                )
                grid_lines.add(line)
            
            # Horizontal lines (length)
            for y in np.linspace(-pitch_height/2, pitch_height/2, 7):
                line = Line(
                    start=[-pitch_width/2, y, 0],
                    end=[pitch_width/2, y, 0],
                    color=BLUE_E,
                    stroke_width=1,
                    stroke_opacity=0.3
                )
                grid_lines.add(line)
            
            self.play(Create(grid_lines), run_time=0.8)
            
            # Zone labels
            zone_labels = VGroup(
                Text("Wide", font_size=20, color=RED).move_to([-pitch_width/2 + 0.8, 2, 0]),
                Text("Off Stump", font_size=20, color=YELLOW).move_to([-1, 2, 0]),
                Text("Middle", font_size=20, color=GREEN).move_to([0, 2, 0]),
                Text("Leg Side", font_size=20, color=BLUE).move_to([1.5, 2, 0]),
            )
            self.play(FadeIn(zone_labels), run_time=0.6)
            
            # Length zones on the right
            length_labels = VGroup(
                Text("Full", font_size=18, color=GREEN).move_to([pitch_width/2 + 1.5, -2.5, 0]),
                Text("Good Length", font_size=18, color=YELLOW).move_to([pitch_width/2 + 1.5, 0, 0]),
                Text("Short", font_size=18, color=RED).move_to([pitch_width/2 + 1.5, 2.5, 0]),
            )
            self.play(FadeIn(length_labels), run_time=0.6)
            
            # Animate multiple ball trajectories
            ball_data = [
                {"start": [0, 4, 0], "end": [0, -3, 0], "color": GREEN, "label": "Yorker"},
                {"start": [-1.5, 4, 0], "end": [-1.5, -1, 0], "color": YELLOW, "label": "Off Stump"},
                {"start": [1, 4, 0], "end": [1.2, 1, 0], "color": BLUE, "label": "Leg Side"},
                {"start": [-2.5, 4, 0], "end": [-2.5, 2, 0], "color": RED, "label": "Wide"},
                {"start": [0.5, 4, 0], "end": [0.5, 0, 0], "color": ORANGE, "label": "Good Length"},
            ]
            
            for i, ball_info in enumerate(ball_data):
                # Create ball
                ball = Circle(radius=0.15, color=ball_info["color"], fill_opacity=1)
                ball.set_sheen(-0.4, DR)
                ball.move_to(ball_info["start"])
                
                # Ball label
                label = Text(ball_info["label"], font_size=16, color=ball_info["color"])
                label.next_to(ball, UP, buff=0.2)
                
                # Trajectory line
                trajectory = Line(
                    start=ball_info["start"],
                    end=ball_info["end"],
                    color=ball_info["color"],
                    stroke_width=3,
                    stroke_opacity=0.5
                )
                
                # Animate
                self.play(
                    Create(trajectory),
                    FadeIn(ball),
                    FadeIn(label),
                    run_time=0.4
                )
                
                self.play(
                    ball.animate.move_to(ball_info["end"]),
                    label.animate.next_to(ball_info["end"], UP, buff=0.2),
                    run_time=1.2,
                    rate_func=rush_into
                )
                
                # Add impact marker
                impact = Circle(radius=0.2, color=ball_info["color"], stroke_width=4)
                impact.move_to(ball_info["end"])
                self.play(
                    Flash(impact, color=ball_info["color"], flash_radius=0.4),
                    run_time=0.3
                )
                
                self.wait(0.2)
            
            # Final hold
            self.wait(2)
            
            # Fade out
            self.play(
                *[FadeOut(mob) for mob in self.mobjects],
                run_time=1
            )

    return CricketBallTrajectory

def create_manim_animation(output_path="cricket_animation.mp4"):
    """Generate Manim animation and return the video path (lazy-loads manim)"""
    try:
        import shutil
        from manim import config, tempconfig
        CricketBallTrajectory = _get_manim_scene_class()
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path) or "."
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use tempconfig context manager to properly set configuration
        with tempconfig({
            "pixel_height": 720,
            "pixel_width": 1280,
            "frame_rate": 30,
            "background_color": "#1a1a2e",
            "output_file": "CricketBallTrajectory",
            "quality": "medium_quality",
            "preview": False,
            "write_to_movie": True,
        }):
            # Render the scene
            scene = CricketBallTrajectory()
            scene.render()
            
            # The rendered file will be in the default media directory
            # Get the output file path from the scene
            if hasattr(scene.renderer, 'file_writer') and scene.renderer.file_writer:
                output_file = scene.renderer.file_writer.movie_file_path
                if output_file and os.path.exists(output_file):
                    shutil.copy(output_file, output_path)
                    return output_path
            
            # Fallback: search for the video in default locations
            home_dir = os.path.expanduser("~")
            possible_dirs = [
                os.path.join(home_dir, "media", "videos"),
                os.path.join(".", "media", "videos"),
                os.path.join(os.getcwd(), "media", "videos"),
            ]
            
            for base_dir in possible_dirs:
                if os.path.exists(base_dir):
                    video_files = glob.glob(os.path.join(base_dir, "**", "*.mp4"), recursive=True)
                    if video_files:
                        # Get the most recent video file
                        latest_video = max(video_files, key=os.path.getctime)
                        shutil.copy(latest_video, output_path)
                        return output_path
            
            return None
            
    except Exception as e:
        st.error(f"Error creating animation: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

# -----------------------------------------------------------------------------
# 3. Three.js 3D Visualization Helper
# -----------------------------------------------------------------------------

def render_threejs_chart(data, chart_type, title, width=600, height=400):
    div_id = f"chart_{uuid.uuid4().hex[:8]}"
    data_json = json.dumps(data)
    
    if chart_type == 'grouped_bar_3d':
        script = f"""
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f5f5);
        
        const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
        camera.position.set(15, 15, 15);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize({width}, {height});
        document.getElementById('{div_id}').appendChild(renderer.domElement);
        
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
        const colors = [0xFDB913, 0x004BA0];
        
        data.forEach((category, catIndex) => {{
            category.values.forEach((val, teamIndex) => {{
                const height = (val.value / maxValue) * 10;
                const geometry = new THREE.BoxGeometry(barWidth, height, barDepth);
                const material = new THREE.MeshPhongMaterial({{ color: colors[teamIndex], shininess: 100 }});
                const bar = new THREE.Mesh(geometry, material);
                
                const xPos = catIndex * spacing - (data.length * spacing / 2);
                const zPos = teamIndex * groupSpacing - 1;
                bar.position.set(xPos, height/2, zPos);
                
                bar.userData = {{
                    team: val.label,
                    phase: category.category,
                    value: val.value.toFixed(2),
                    balls: val.balls || 0,
                    wickets: val.wickets || 0
                }};
                
                scene.add(bar);
            }});
        }});
        
        const gridHelper = new THREE.GridHelper(30, 30, 0x888888, 0xdddddd);
        scene.add(gridHelper);
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
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
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
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
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
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
    div_id = f"pitch_{uuid.uuid4().hex[:8]}"
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
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
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
            for (let i = 0; i < 5000; i++) {{
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
                marker.castShadow = true;
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
                const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 16);
                const poleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x808080,
                    roughness: 0.6,
                    metalness: 0.7
                }});
                const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                pole.position.set(pos.x, 20, pos.z);
                pole.castShadow = true;
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
                    new THREE.CylinderGeometry(0.022, 0.022, 0.71, 16), 
                    stumpMaterial
                );
                stump1.position.set(x, 0.355, 0);
                stump1.castShadow = true;
                stump1.receiveShadow = true;
                scene.add(stump1);
                
                // Batter end stumps
                const stump2 = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.022, 0.022, 0.71, 16), 
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
                    new THREE.CylinderGeometry(0.012, 0.012, 0.115, 16),
                    bailMaterial
                );
                bail1.rotation.z = Math.PI / 2;
                bail1.position.set(x, 0.73, 0);
                bail1.castShadow = true;
                scene.add(bail1);
                
                const bail2 = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.012, 0.012, 0.115, 16),
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
            
            pitchData.forEach(ball => {{
                const radius = ball.size * 0.02;
                const geometry = new THREE.SphereGeometry(radius, 16, 16);
                const material = new THREE.MeshStandardMaterial({{ 
                    color: colorMap[ball.color],
                    roughness: 0.3,
                    metalness: 0.5,
                    emissive: colorMap[ball.color],
                    emissiveIntensity: 0.4
                }});
                const sphere = new THREE.Mesh(geometry, material);
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
                        requestAnimationFrame(animateCamera);
                    }}
                }}
                animateCamera();
            }};
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        }})();
        </script>
    </body>
    </html>
    """
    return html

def render_wagon_wheel(data, title, width=600, height=600):
    """Render wagon wheel visualization with realistic cricket stadium using Three.js"""
    data_json = json.dumps(data)
    div_id = f"wagon_wheel_{uuid.uuid4().hex[:8]}"
    unique_id = uuid.uuid4().hex[:8]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
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
            scene.background = new THREE.Color(0x87ceeb);
            
            const camera = new THREE.PerspectiveCamera(50, {width}/{height}, 0.1, 1000);
            camera.position.set(0, 85, 5);
            camera.lookAt(0, 0, 0);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            // Enhanced Lighting System
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
            scene.add(ambientLight);
            
            const sunLight = new THREE.DirectionalLight(0xffffff, 0.9);
            sunLight.position.set(50, 120, 50);
            sunLight.castShadow = true;
            sunLight.shadow.mapSize.width = 2048;
            sunLight.shadow.mapSize.height = 2048;
            sunLight.shadow.camera.left = -100;
            sunLight.shadow.camera.right = 100;
            sunLight.shadow.camera.top = 100;
            sunLight.shadow.camera.bottom = -100;
            scene.add(sunLight);
            
            const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
            fillLight.position.set(-50, 80, -50);
            scene.add(fillLight);
            
            // Create procedural grass texture
            const grassCanvas = document.createElement('canvas');
            grassCanvas.width = 1024;
            grassCanvas.height = 1024;
            const grassCtx = grassCanvas.getContext('2d');
            
            // Base grass with mowing pattern
            for (let i = 0; i < 20; i++) {{
                grassCtx.fillStyle = i % 2 === 0 ? '#157015' : '#1a7a1a';
                grassCtx.fillRect(0, i * 51.2, 1024, 51.2);
            }}
            
            // Add realistic grass texture
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
            
            // Circular stadium ground (70m radius - regulation size)
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
            
            // 30-yard circle (regulation inner circle)
            const innerCircleGeometry = new THREE.RingGeometry(27.43, 27.73, 64);
            const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                color: 0xffffff,
                roughness: 0.6,
                metalness: 0.2
            }});
            const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
            innerCircle.rotation.x = -Math.PI / 2;
            innerCircle.position.y = 0.05;
            scene.add(innerCircle);
            
            // Boundary rope (white)
            const boundaryGeometry = new THREE.RingGeometry(69.5, 70, 64);
            const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                color: 0xffffff,
                roughness: 0.4,
                metalness: 0.3
            }});
            const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
            boundary.rotation.x = -Math.PI / 2;
            boundary.position.y = 0.1;
            scene.add(boundary);
            
            // Advertising boards around boundary (32 boards)
            const adColors = [
                0xff0000, 0x00ff00, 0x0000ff, 0xffff00, 
                0xff00ff, 0x00ffff, 0xff8800, 0x8800ff
            ];
            
            for (let i = 0; i < 32; i++) {{
                const angle = (i / 32) * Math.PI * 2;
                const x = Math.cos(angle) * 68;
                const z = Math.sin(angle) * 68;
                
                const boardGeometry = new THREE.BoxGeometry(3.5, 1.8, 0.3);
                const boardMaterial = new THREE.MeshStandardMaterial({{ 
                    color: adColors[i % adColors.length],
                    roughness: 0.4,
                    metalness: 0.5,
                    emissive: adColors[i % adColors.length],
                    emissiveIntensity: 0.2
                }});
                const board = new THREE.Mesh(boardGeometry, boardMaterial);
                board.position.set(x, 0.9, z);
                board.lookAt(0, 0.9, 0);
                board.castShadow = true;
                scene.add(board);
            }}
            
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
            const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 16);
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
            
            wagonData.forEach(shot => {{
                // Shot line from stumps to landing point
                const lineMaterial = new THREE.LineBasicMaterial({{ 
                    color: colorMap[shot.color],
                    linewidth: 2,
                    opacity: 0.65,
                    transparent: true
                }});
                const lineGeometry = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(0, 0.4, 0),
                    new THREE.Vector3(shot.x, 0.4, shot.y)
                ]);
                const line = new THREE.Line(lineGeometry, lineMaterial);
                scene.add(line);
                
                // Ball at landing point
                const radius = shot.size * 0.12;
                const ballGeometry = new THREE.SphereGeometry(radius, 20, 20);
                const ballMaterial = new THREE.MeshStandardMaterial({{ 
                    color: colorMap[shot.color],
                    roughness: 0.3,
                    metalness: 0.7,
                    emissive: colorMap[shot.color],
                    emissiveIntensity: 0.4
                }});
                const ball = new THREE.Mesh(ballGeometry, ballMaterial);
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
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
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
            scene.background = new THREE.Color(0x87ceeb);
            
            // Camera setup
            const camera = new THREE.PerspectiveCamera(45, 900/700, 0.1, 500);
            camera.position.set(0, 18, 30);
            camera.lookAt(0, 0, 11);
            
            // Renderer setup
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(900, 700);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
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
            sunLight.castShadow = true;
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
            
            // Cricket Stadium - Full circular outfield
            const stadiumRadius = 70;
            
            // Stadium ground with grass texture
            const groundGeometry = new THREE.CircleGeometry(stadiumRadius, 64);
            const groundMaterial = new THREE.MeshStandardMaterial({{ 
                color: 0x1a5c1a,
                roughness: 0.85
            }});
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.position.set(0, -0.1, 11);
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Create grass texture
            const grassCanvas = document.createElement('canvas');
            grassCanvas.width = 1024;
            grassCanvas.height = 1024;
            const grassCtx = grassCanvas.getContext('2d');
            
            // Base green
            grassCtx.fillStyle = '#1a5c1a';
            grassCtx.fillRect(0, 0, 1024, 1024);
            
            // Add grass texture
            for (let i = 0; i < 5000; i++) {{
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
            
            // Boundary rope
            const boundaryGeometry = new THREE.RingGeometry(stadiumRadius - 0.5, stadiumRadius, 64);
            const boundaryMaterial = new THREE.MeshBasicMaterial({{ 
                color: 0xffffff,
                side: THREE.DoubleSide
            }});
            const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
            boundary.rotation.x = -Math.PI / 2;
            boundary.position.set(0, -0.04, 11);
            scene.add(boundary);
            
            // Advertising boards around boundary
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
                marker.castShadow = true;
                scene.add(marker);
            }}
            
            // Floodlight towers at corners
            const floodlightPositions = [
                {{ x: 50, z: -30 }},
                {{ x: -50, z: -30 }},
                {{ x: 50, z: 52 }},
                {{ x: -50, z: 52 }}
            ];
            
            floodlightPositions.forEach(pos => {{
                // Tower pole
                const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 16);
                const poleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x808080,
                    roughness: 0.6,
                    metalness: 0.7
                }});
                const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                pole.position.set(pos.x, 20, pos.z);
                pole.castShadow = true;
                scene.add(pole);
                
                // Light fixture
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
            
            pitchData.forEach(ball => {{
                const radius = ball.size * 0.02;
                const ballGeometry = new THREE.SphereGeometry(radius, 12, 12);
                const ballMaterial = new THREE.MeshStandardMaterial({{ 
                    color: colorMap[ball.color],
                    roughness: 0.4,
                    metalness: 0.3,
                    emissive: colorMap[ball.color],
                    emissiveIntensity: 0.3
                }});
                const ballMesh = new THREE.Mesh(ballGeometry, ballMaterial);
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
                    
                    if (progress < 1) requestAnimationFrame(animate);
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
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
            
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
                background: rgba(0,0,0,0.85);
                padding: 15px;
                border-radius: 10px;
                color: white;
                font-size: 12px;
                border: 2px solid #444;
            }}
            .view-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                color: white;
                padding: 8px 12px;
                margin: 4px 0;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                font-weight: bold;
                transition: all 0.3s;
            }}
            .view-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            .controls-title {{
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 14px;
                border-bottom: 2px solid #666;
                padding-bottom: 8px;
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
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
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
            for (let i = 0; i < 5000; i++) {{
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
                marker.castShadow = true;
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
                const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 16);
                const poleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x808080,
                    roughness: 0.6,
                    metalness: 0.7
                }});
                const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                pole.position.set(pos.x, 20, pos.z);
                pole.castShadow = true;
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
                const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 16);
                const stump = new THREE.Mesh(stumpGeometry, stumpMaterial);
                stump.position.set(x, 0.355, 0);
                stump.castShadow = true;
                stump.receiveShadow = true;
                scene.add(stump);
            }}
            
            // Batter's end stumps
            for (let x of stumpPositions) {{
                const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 16);
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
                    new THREE.CylinderGeometry(0.012, 0.012, 0.115, 16),
                    bailMaterial
                );
                bail1.rotation.z = Math.PI / 2;
                bail1.position.set(x, 0.73, 0);
                bail1.castShadow = true;
                scene.add(bail1);
                
                // Batter's end bails
                const bail2 = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.012, 0.012, 0.115, 16),
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
            
            pitchData.forEach(ball => {{
                const radius = ball.size * 0.025;
                const geometry = new THREE.SphereGeometry(radius, 12, 12);
                const material = new THREE.MeshStandardMaterial({{ 
                    color: colorMap[ball.color],
                    roughness: 0.5,
                    metalness: 0.3,
                    emissive: colorMap[ball.color],
                    emissiveIntensity: 0.3
                }});
                const sphere = new THREE.Mesh(geometry, material);
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
                        requestAnimationFrame(animate);
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
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        }})();
        </script>
    </body>
    </html>
    """
    return html

def render_stumps_view(data, title, width=500, height=600):
    """Render stumps view visualization as 3D with interactive controls like Bowling Length Analysis"""
    data_json = json.dumps(data)
    div_id = f"stumps_view_{uuid.uuid4().hex[:8]}"
    unique_id = uuid.uuid4().hex[:8]
    
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
            scene.background = new THREE.Color(0x87ceeb);
            
            const camera = new THREE.PerspectiveCamera(45, {width}/{height}, 0.1, 1000);
            camera.position.set(0, 8, 25);
            camera.lookAt(0, 1.5, 0);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.minDistance = 10;
            controls.maxDistance = 50;
            controls.maxPolarAngle = Math.PI / 2;
            controls.target.set(0, 1.5, 0);
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
            scene.add(ambientLight);
            
            const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
            sunLight.position.set(5, 15, 10);
            sunLight.castShadow = true;
            sunLight.shadow.mapSize.width = 2048;
            sunLight.shadow.mapSize.height = 2048;
            scene.add(sunLight);
            
            const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
            fillLight.position.set(-5, 8, 5);
            scene.add(fillLight);
            
            // Ground plane
            const groundGeometry = new THREE.CircleGeometry(20, 64);
            const groundMaterial = new THREE.MeshStandardMaterial({{ 
                color: 0x1a7a1a,
                roughness: 0.8,
                metalness: 0.1
            }});
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
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
                    new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 16), 
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
                    new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 16), 
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
                const ballGeometry = new THREE.SphereGeometry(radius, 16, 16);
                const ballMaterial = new THREE.MeshStandardMaterial({{ 
                    color: colorMap[ball.color],
                    roughness: 0.3,
                    metalness: 0.6,
                    emissive: colorMap[ball.color],
                    emissiveIntensity: 0.2
                }});
                const sphere = new THREE.Mesh(ballGeometry, ballMaterial);
                
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
                        requestAnimationFrame(animate);
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
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
            
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
    div_id = f"advanced_pitch_{uuid.uuid4().hex[:8]}"
    
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
                grid-template-columns: repeat(4, 1fr); 
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
                width: 280,
                height: 380,
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
            
            Plotly.newPlot('plot1_{div_id}', [wicketsTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false}});
            
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
            
            Plotly.newPlot('plot2_{div_id}', [hittingTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false}});
            
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
            
            Plotly.newPlot('plot3_{div_id}', [heatmapTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false}});
            
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
            
            Plotly.newPlot('plot4_{div_id}', [hittingCombined, wicketsCombined, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false}});
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
    
    div_id = f"player_stats_{uuid.uuid4().hex[:8]}"
    
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
            .stats-container-{div_id} {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: 12px;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 8px;
            }}
            .player-card-{div_id} {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 16px;
                color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                transition: transform 0.2s;
                position: relative;
            }}
            .player-card-{div_id}:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            }}
            .player-rank-{div_id} {{
                position: absolute;
                top: 8px;
                right: 8px;
                background: rgba(255,255,255,0.3);
                width: 35px;
                height: 35px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                font-weight: bold;
            }}
            .player-name-{div_id} {{
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 12px;
                padding-right: 45px;
            }}
            .main-stats-{div_id} {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 12px;
                padding: 10px;
                background: rgba(255,255,255,0.15);
                border-radius: 6px;
            }}
            .stat-item-{div_id} {{
                text-align: center;
            }}
            .stat-value-{div_id} {{
                font-size: 20px;
                font-weight: bold;
                display: block;
            }}
            .stat-label-{div_id} {{
                font-size: 10px;
                opacity: 0.9;
                text-transform: uppercase;
            }}
            .boundaries-{div_id} {{
                display: flex;
                gap: 8px;
                margin-bottom: 10px;
            }}
            .boundary-badge-{div_id} {{
                flex: 1;
                background: rgba(255,255,255,0.2);
                padding: 6px;
                border-radius: 5px;
                text-align: center;
            }}
            .boundary-value-{div_id} {{
                font-size: 18px;
                font-weight: bold;
                display: block;
            }}
            .boundary-label-{div_id} {{
                font-size: 10px;
                opacity: 0.9;
            }}
            .secondary-stats-{div_id} {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 6px;
            }}
            .secondary-stat-{div_id} {{
                background: rgba(255,255,255,0.1);
                padding: 6px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
                font-size: 11px;
            }}
        </style>
    </head>
    <body>
        <div class="stats-container-{div_id}" id="{div_id}"></div>
        
        <script>
        (function() {{
            const players = {data_json};
            const container = document.getElementById('{div_id}');
            
            const solidColors = [
                {{ bg: '#2563eb', accent: '#1e40af' }},
                {{ bg: '#dc2626', accent: '#991b1b' }},
                {{ bg: '#059669', accent: '#047857' }},
                {{ bg: '#7c3aed', accent: '#6d28d9' }},
                {{ bg: '#ea580c', accent: '#c2410c' }},
                {{ bg: '#0891b2', accent: '#0e7490' }},
                {{ bg: '#db2777', accent: '#be185d' }},
                {{ bg: '#65a30d', accent: '#4d7c0f' }},
                {{ bg: '#4f46e5', accent: '#4338ca' }},
                {{ bg: '#0d9488', accent: '#0f766e' }}
            ];
            
            players.forEach((player, index) => {{
                const card = document.createElement('div');
                card.className = 'player-card-{div_id}';
                const colorScheme = solidColors[index % solidColors.length];
                card.style.background = colorScheme.bg;
                card.style.borderTop = `4px solid ${{colorScheme.accent}}`;
                card.style.boxShadow = `0 4px 15px ${{colorScheme.accent}}40`;
                
                card.innerHTML = `
                    <div class="player-rank-{div_id}">${{index + 1}}</div>
                    <div class="player-name-{div_id}">${{player.name}}</div>
                    
                    <div class="main-stats-{div_id}">
                        <div class="stat-item-{div_id}">
                            <span class="stat-value-{div_id}">${{player.runs}}</span>
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
""", unsafe_allow_html=True)

# Logout in sidebar
with st.sidebar:
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
st.sidebar.markdown("---")

# Season/Year Filter
st.sidebar.markdown("### 📅 Season Selection")
filter_mode = "Overall Statistics (2008-Present)"  # Default value
selected_seasons = []  # Default value

if 'season' in df.columns:
    df['season'] = pd.to_numeric(df['season'], errors='coerce')
    available_seasons = sorted(df['season'].dropna().unique())
    
    filter_mode = st.sidebar.radio(
        "Filter Mode",
        ["Overall Statistics (2008-Present)", "Specific Season(s)"],
        help="Choose to view all-time stats or filter by specific seasons"
    )
    
    if filter_mode == "Overall Statistics (2008-Present)":
        st.sidebar.info(f"📊 Analyzing data from **{int(min(available_seasons))}** to **{int(max(available_seasons))}**\n\n**Total Seasons:** {len(available_seasons)}")
        filtered_df = df.copy()
    else:
        selected_seasons = st.sidebar.multiselect(
            "Select Season(s)",
            options=available_seasons,
            default=[max(available_seasons)] if available_seasons else [],
            help="Select one or multiple seasons to analyze"
        )
        
        if selected_seasons:
            filtered_df = df[df['season'].isin(selected_seasons)]
            st.sidebar.success(f"✅ Filtered to {len(selected_seasons)} season(s)")
        else:
            st.sidebar.warning("⚠️ No season selected. Showing all data.")
            filtered_df = df.copy()
else:
    filtered_df = df.copy()
    st.sidebar.info("Season data not available in dataset")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏏 Team Selection")
# Remove NaN values from teams list
teams = sorted([t for t in filtered_df['batting_team'].unique() if pd.notna(t)])

if len(teams) < 2:
    st.sidebar.error("⚠️ Not enough teams in selected data. Please adjust filters.")
    st.stop()

team1 = st.sidebar.selectbox("Team 1", teams, index=0, help="Select first team for comparison")

# Filter team2 options to exclude team1
team2_options = [t for t in teams if t != team1]
if team2_options:
    team2 = st.sidebar.selectbox("Team 2", team2_options, index=0, help="Select second team for comparison")
else:
    team2 = st.sidebar.selectbox("Team 2", teams, index=1 if len(teams) > 1 else 0, help="Select second team for comparison")

# Validation check
if team1 == team2:
    st.sidebar.warning("⚠️ Same team selected for both. Results may be identical.")


st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Bowler Analysis")
bowler_types = ['All Types', 'Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
bowler_type = st.sidebar.selectbox("Bowler Type", bowler_types, help="Filter analysis by bowler type")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Match Phase Filter")
phase_options = ['All Phases', 'Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
selected_phase = st.sidebar.selectbox(
    "Match Phase",
    phase_options,
    help="Filter analysis by match phase"
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
# TAB-BASED NAVIGATION
# =====================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Phase Analysis",
    "🎯 Pitch Maps & Wagon Wheel",
    "👤 Player Stats",
    "🎳 Bowling Analysis",
    "📈 Statistical Charts",
    "🎬 Animations"
])

# =====================================================================
# TAB 1: Phase Analysis
# =====================================================================
with tab1:
    st.markdown("## 📊 Phase Analysis: Run Rate Comparison")
    st.markdown(f"**{team1}** vs **{team2}** — 3D interactive visualization showing run rates across match phases")

    t1_stats = calculate_run_rate_by_phase(df, team1)
    t2_stats = calculate_run_rate_by_phase(df, team2)
    phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
    phase_data = []
    for phase in phases:
        t1_phase = t1_stats[t1_stats['phase'] == phase]
        t2_phase = t2_stats[t2_stats['phase'] == phase]
        
        val1 = float(t1_phase['run_rate'].values[0]) if not t1_phase.empty else 0.0
        val2 = float(t2_phase['run_rate'].values[0]) if not t2_phase.empty else 0.0
        balls1 = int(t1_phase['ball'].values[0]) if not t1_phase.empty else 0
        balls2 = int(t2_phase['ball'].values[0]) if not t2_phase.empty else 0
        wickets1 = int(t1_phase['wickets'].values[0]) if not t1_phase.empty else 0
        wickets2 = int(t2_phase['wickets'].values[0]) if not t2_phase.empty else 0
        
        phase_data.append({
            'category': str(phase),
            'values': [
                {'label': str(team1), 'value': val1, 'balls': balls1, 'wickets': wickets1},
                {'label': str(team2), 'value': val2, 'balls': balls2, 'wickets': wickets2}
            ]
        })

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(f"{team1} Avg Run Rate", f"{t1_stats['run_rate'].mean():.2f}", help="Average run rate across all phases")
    with col_b:
        st.metric(f"{team2} Avg Run Rate", f"{t2_stats['run_rate'].mean():.2f}", help="Average run rate across all phases")
    with col_c:
        diff = t1_stats['run_rate'].mean() - t2_stats['run_rate'].mean()
        st.metric("Difference", f"{abs(diff):.2f}", delta=f"{diff:.2f}")

    st.markdown("")
    components.html(render_threejs_chart(phase_data, 'grouped_bar_3d', "3D Run Rate Comparison by Phase", 900, 500), height=550)

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
    with d1:
        rd1 = df[df['batting_team'] == team1]['runs_off_bat'].value_counts().sort_index()
        pie1_data = [{'label': str(k), 'value': int(v)} for k, v in rd1.items()]
        components.html(render_threejs_chart(pie1_data, 'pie_3d', f"{team1} Runs", 450, 400), height=450)
    with d2:
        rd2 = df[df['batting_team'] == team2]['runs_off_bat'].value_counts().sort_index()
        pie2_data = [{'label': str(k), 'value': int(v)} for k, v in rd2.items()]
        components.html(render_threejs_chart(pie2_data, 'pie_3d', f"{team2} Runs", 450, 400), height=450)

# =====================================================================
# TAB 2: Pitch Maps & Wagon Wheel
# =====================================================================
with tab2:
    phase_val = None if selected_phase == 'All Phases' else selected_phase

    st.subheader("🎯 Advanced Pitch Maps - Multi-Panel Analysis")
    st.markdown("_4-panel view: Wickets, Hitting, Density Heat Map, and Combined_")
    st.markdown(f"### {team1} - Advanced Pitch Analysis")
    pitch_data1 = generate_pitch_map_data(df, team=team1, bowler_type=bowler_type, phase=phase_val)
    if pitch_data1:
        components.html(render_advanced_pitch_viz(pitch_data1, f"{team1} - {selected_phase}", 1200, 450), height=500)
        st.caption(f"📊 Deliveries: {len(pitch_data1)} | Wickets: {sum(1 for d in pitch_data1 if d['wicket'] == 1)}")
    else:
        st.info(f"No data available for {team1}")
    st.markdown(f"### {team2} - Advanced Pitch Analysis")
    pitch_data2 = generate_pitch_map_data(df, team=team2, bowler_type=bowler_type, phase=phase_val)
    if pitch_data2:
        components.html(render_advanced_pitch_viz(pitch_data2, f"{team2} - {selected_phase}", 1200, 450), height=500)
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
# TAB 3: Player Stats
# =====================================================================
with tab3:
    st.markdown("## 📊 Player Statistics - Top Performers")
    phase_val = None if selected_phase == 'All Phases' else selected_phase
    st.markdown(f"### {team1} - Top Batters")
    stats1 = get_player_statistics(df, team1, phase=phase_val)
    if not stats1.empty:
        components.html(render_player_stats_cards(stats1, f"{team1}"), height=600)
        st.caption(f"📈 Showing top {len(stats1)} batters with minimum 30 balls faced")
    else:
        st.info(f"No player statistics available for {team1}")
    st.markdown(f"### {team2} - Top Batters")
    stats2 = get_player_statistics(df, team2, phase=phase_val)
    if not stats2.empty:
        components.html(render_player_stats_cards(stats2, f"{team2}"), height=600)
        st.caption(f"📈 Showing top {len(stats2)} batters with minimum 30 balls faced")
    else:
        st.info(f"No player statistics available for {team2}")

# =====================================================================
# TAB 4: Bowling Analysis
# =====================================================================
with tab4:
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
# TAB 5: Statistical Charts
# =====================================================================
with tab5:
    st.markdown("## 📈 Statistical Analysis - Interactive Altair Charts")
    phase_val = None if selected_phase == 'All Phases' else selected_phase

    st.markdown("### 📊 Runs Distribution Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{team1} - Runs per Ball Distribution**")
        runs_chart_1 = create_runs_distribution_chart(df, team1, phase=phase_val)
        if runs_chart_1:
            st.altair_chart(runs_chart_1, use_container_width=True)
        else:
            st.info("No data available")
    with col2:
        st.markdown(f"**{team2} - Runs per Ball Distribution**")
        runs_chart_2 = create_runs_distribution_chart(df, team2, phase=phase_val)
        if runs_chart_2:
            st.altair_chart(runs_chart_2, use_container_width=True)
        else:
            st.info("No data available")

    st.markdown("### ⚡ Strike Rate Comparison - Top Performers")
    strike_rate_chart = create_strike_rate_comparison(df, phase=phase_val)
    if strike_rate_chart:
        st.altair_chart(strike_rate_chart, use_container_width=True)

    st.markdown("### 🎯 Boundary & Dot Ball Analysis")
    boundary_chart = create_boundary_percentage_chart(df, [team1, team2], phase=phase_val)
    if boundary_chart:
        st.altair_chart(boundary_chart, use_container_width=True)

    st.markdown("### 📈 Runs Progression Over Overs")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{team1} - Over-by-Over Progression**")
        progression_1 = create_runs_over_progression(df, team1, phase=phase_val)
        if progression_1:
            st.altair_chart(progression_1, use_container_width=True)
    with col2:
        st.markdown(f"**{team2} - Over-by-Over Progression**")
        progression_2 = create_runs_over_progression(df, team2, phase=phase_val)
        if progression_2:
            st.altair_chart(progression_2, use_container_width=True)

    st.markdown("### 🎯 Wicket Fall Timeline")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{team1} Bowling - Wickets Timeline**")
        wicket_chart_1 = create_wicket_timeline(df, team1, phase=phase_val)
        if wicket_chart_1:
            st.altair_chart(wicket_chart_1, use_container_width=True)
        else:
            st.info(f"No wickets data available for {team1}")
    with col2:
        st.markdown(f"**{team2} Bowling - Wickets Timeline**")
        wicket_chart_2 = create_wicket_timeline(df, team2, phase=phase_val)
        if wicket_chart_2:
            st.altair_chart(wicket_chart_2, use_container_width=True)
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
# TAB 6: Animations
# =====================================================================
with tab6:
    st.markdown("## 🎬 Ball Trajectory Animation (Manim)")
    st.markdown("""Generate a **professional Manim animation** showing cricket ball trajectories 
    from the stumps view with different lines and lengths.""")
    
    if st.button("🎥 Generate Manim Animation", key="manim_btn"):
        with st.spinner("Creating animation... This may take 30-60 seconds..."):
            try:
                video_path = create_manim_animation("cricket_trajectory.mp4")
                if video_path and os.path.exists(video_path):
                    st.success("✅ Animation created successfully!")
                    st.video(video_path)
                    with open(video_path, "rb") as file:
                        st.download_button(label="📥 Download Animation", data=file,
                            file_name="cricket_ball_trajectory.mp4", mime="video/mp4")
                else:
                    st.warning("⚠️ Manim library may not be installed. Install with: `pip install manim`")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure manim is installed: `pip install manim`")
