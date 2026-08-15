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


PHASE_ORDER = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
PHASE_COLORS = {
    'Powerplay (1-6)': 'rgba(34, 197, 94, 0.12)',
    'Middle (7-15)': 'rgba(59, 130, 246, 0.10)',
    'Death (16-20)': 'rgba(239, 68, 68, 0.12)',
}
PHASE_LABEL_COLORS = {
    'Powerplay (1-6)': '#4ade80',
    'Middle (7-15)': '#60a5fa',
    'Death (16-20)': '#f87171',
}

BOWLER_TYPE_COLORS = {
    'Right-Arm Pace': '#3b82f6',
    'Left-Arm Pace': '#06b6d4',
    'Right-Arm Leg Spin': '#a855f7',
    'Right-Arm Off Spin': '#ec4899',
    'Left-Arm Orthodox': '#10b981',
    'Left-Arm Wrist Spin': '#f59e0b',
}

WICKET_TYPE_COLORS = {
    'caught': '#3b82f6',
    'bowled': '#ef4444',
    'lbw': '#eab308',
    'run out': '#f97316',
    'stumped': '#8b5cf6',
    'caught and bowled': '#10b981',
    'hit wicket': '#ec4899',
    'retired hurt': '#64748b',
}

RUN_COLOR_MAP = {
    0: 'rgba(59,130,246,0.15)',
    1: 'rgba(59,130,246,0.35)',
    2: 'rgba(59,130,246,0.55)',
    3: 'rgba(59,130,246,0.70)',
    4: 'rgba(59,130,246,0.85)',
    6: 'rgba(59,130,246,1.0)',
}

RUN_LABEL_MAP = {
    0: 'Dot Balls',
    1: 'Singles',
    2: 'Twos',
    3: 'Threes',
    4: 'Fours',
    6: 'Sixes',
}

BASE_CSS = """
<style>
/* === Base === */
.main .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:100%}
.stApp{font-family:'Inter',sans-serif;background:#030712}
.stApp::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(102,126,234,.05)1px,transparent 1px),linear-gradient(90deg,rgba(102,126,234,.05)1px,transparent 1px);background-size:50px 50px;pointer-events:none;z-index:0}
h1{font-family:'Orbitron',monospace!important;background:linear-gradient(135deg,#667eea 0%,#f093fb 50%,#f5576c 100%)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important;font-weight:900!important;letter-spacing:1px!important;font-size:2rem!important}
h2{color:#e2e8f0;font-weight:700;border-bottom:1px solid rgba(102,126,234,.3);padding-bottom:.5rem;margin-top:1.5rem}
h3{color:#cbd5e1;font-weight:600}
[data-testid="stMetric"]{background:rgba(15,23,42,.75)!important;backdrop-filter:blur(16px)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:16px!important;padding:1.2rem!important;box-shadow:0 4px 24px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.05)!important;transition:all .3s ease!important}
[data-testid="stMetric"]:hover{border-color:rgba(102,126,234,.45)!important;box-shadow:0 8px 32px rgba(102,126,234,.15)!important;transform:translateY(-2px)!important}
[data-testid="stMetricValue"]{font-family:'Orbitron',monospace!important;font-size:1.9rem!important;font-weight:800!important;background:linear-gradient(135deg,#667eea,#f093fb)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important}
[data-testid="stMetricLabel"]{font-weight:600!important;text-transform:uppercase!important;letter-spacing:.8px!important;font-size:.72rem!important;color:rgba(148,163,184,.8)!important}
[data-testid="column"]{border-radius:16px;padding:1.2rem;background:rgba(15,23,42,.6);backdrop-filter:blur(12px);border:1px solid rgba(102,126,234,.12);box-shadow:0 4px 20px rgba(0,0,0,.2);transition:all .3s ease}
[data-testid="column"]:hover{border-color:rgba(102,126,234,.3);box-shadow:0 8px 32px rgba(102,126,234,.1)}
.stButton>button{border-radius:10px!important;font-weight:600!important;background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;border:none!important;padding:.6rem 1.5rem!important;transition:all .3s cubic-bezier(.4,0,.2,1)!important;box-shadow:0 4px 15px rgba(102,126,234,.3)!important}
.stButton>button:hover{transform:translateY(-3px)!important;box-shadow:0 8px 25px rgba(102,126,234,.5)!important}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:rgba(15,23,42,.8);padding:5px;border-radius:14px;border:1px solid rgba(102,126,234,.15);backdrop-filter:blur(12px)}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:10px 22px;font-weight:600;transition:all .3s ease;color:rgba(148,163,184,.75)!important;font-size:.85rem}
.stTabs [data-baseweb="tab"]:hover{background:rgba(102,126,234,.12)!important;color:#c4b5fd!important}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,rgba(102,126,234,.3),rgba(118,75,162,.3))!important;color:#c4b5fd!important;box-shadow:0 0 12px rgba(102,126,234,.2)!important}
section[data-testid="stSidebar"]{background:rgba(15,23,42,.95)!important;border-right:1px solid rgba(102,126,234,.18)!important;backdrop-filter:blur(20px)!important}
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#e2e8f0;border:none;font-family:'Inter',sans-serif!important}
.stSidebar [data-testid="stSelectbox"]>div>div{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important}
.stSelectbox>div>div,.stMultiSelect>div>div{border-radius:10px!important}
.stTextInput>div>div>input{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important;color:#f1f5f9!important}
.stDataFrame{border-radius:12px;overflow:hidden;border:1px solid rgba(102,126,234,.15)!important}
.stAlert{border-radius:12px;backdrop-filter:blur(8px)}
hr{margin:2.5rem 0;border:none;height:1px;background:linear-gradient(90deg,transparent,rgba(102,126,234,.4),transparent)}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:rgba(15,23,42,.5)}
::-webkit-scrollbar-thumb{background:rgba(102,126,234,.4);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(102,126,234,.7)}
@keyframes fadeInUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.element-container{animation:fadeInUp .35s ease-out}
html{scroll-behavior:smooth}
</style>
"""


def get_team_color(team: str, default: str = '#3b82f6') -> str:
    """Get the hex color for a team."""
    return IPL_TEAM_COLORS.get(team, default)


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex color to rgba string."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        r, g, b = 59, 130, 246
    return f"rgba({r}, {g}, {b}, {alpha})"