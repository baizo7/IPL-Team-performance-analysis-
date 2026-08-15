import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import sys
import json
from typing import Optional, List
from dotenv import load_dotenv

# Load env
load_dotenv()

# Ensure root project dir is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.auth import (
    DEMO_USERS,
    verify_password,
    create_access_token,
    get_current_user
)
from ipl_data_cleaner import build_clean_dataset

# Global data holders
df = None
hawkeye_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global df, hawkeye_processor
    print("Loading IPL dataset...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(base_dir, 'all_ipl_matches.csv')
    try:
        if os.path.exists(file_path):
            raw_df = pd.read_csv(file_path, low_memory=False)
            clean_df, report = build_clean_dataset(raw_df)
            df = clean_df
            
            if 'start_date' in df.columns:
                df['date'] = pd.to_datetime(df['start_date'])
                df['season'] = df['date'].dt.year
                
            df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21], labels=['Powerplay', 'Middle', 'Death'])
            print(f"Successfully cleaned and loaded {len(df)} match rows.")
    except Exception as e:
        print(f"Failed to load match dataset: {e}")

    try:
        from hawkeye_processor import HawkeyeProcessor
        hp = HawkeyeProcessor()
        hp.load()
        if hp.has_data():
            hawkeye_processor = hp
            print(f"Successfully loaded HawkeyeProcessor with {len(hp.df)} deliveries.")
    except Exception as e:
        print(f"Failed to initialize HawkeyeProcessor: {e}")
    yield
    print("Shutting down API resources.")

app = FastAPI(title="IPL Analysis API with OAuth2", lifespan=lifespan)

# Configure CORS safely from env
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic Rate Limiter Middleware (Token Bucket / Sliding Window)
REQUEST_HISTORY = {}
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    # Clean up old timestamps (> 60 sec)
    if client_ip in REQUEST_HISTORY:
        REQUEST_HISTORY[client_ip] = [t for t in REQUEST_HISTORY[client_ip] if now - t < 60]
    else:
        REQUEST_HISTORY[client_ip] = []

    if len(REQUEST_HISTORY[client_ip]) >= RATE_LIMIT_PER_MIN:
        return status.HTTP_429_TOO_MANY_REQUESTS
    
    REQUEST_HISTORY[client_ip].append(now)
    response = await call_next(request)
    return response


# --- Authentication Endpoints ---

@app.post("/api/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DEMO_USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@app.get("/api/auth/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# --- Data & Filter Endpoints ---

@app.get("/")
def read_root():
    return {
        "status": "API is running",
        "match_data_loaded": df is not None,
        "hawkeye_data_loaded": hawkeye_processor is not None and hawkeye_processor.has_data()
    }

@app.get("/api/teams")
def get_teams():
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    teams = sorted(list(set(df['batting_team'].dropna().unique()) | set(df['bowling_team'].dropna().unique())))
    return {"teams": teams}

@app.get("/api/seasons")
def get_seasons():
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    seasons = sorted([int(s) for s in df['season'].dropna().unique()])
    return {"seasons": seasons}

@app.get("/api/venues")
def get_venues():
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    venues = sorted(list(df['venue'].dropna().unique()))
    return {"venues": venues}

def filter_df(
    data: pd.DataFrame,
    team: Optional[str] = None,
    opponent: Optional[str] = None,
    season_min: Optional[int] = None,
    season_max: Optional[int] = None,
    venue: Optional[str] = None,
    phase: Optional[str] = None
) -> pd.DataFrame:
    filtered = data.copy()
    if team:
        filtered = filtered[(filtered['batting_team'] == team) | (filtered['bowling_team'] == team)]
    if opponent and team:
        filtered = filtered[
            ((filtered['batting_team'] == team) & (filtered['bowling_team'] == opponent)) |
            ((filtered['batting_team'] == opponent) & (filtered['bowling_team'] == team))
        ]
    if season_min:
        filtered = filtered[filtered['season'] >= season_min]
    if season_max:
        filtered = filtered[filtered['season'] <= season_max]
    if venue and venue != "All Venues":
        filtered = filtered[filtered['venue'] == venue]
    if phase and phase != "All Phases":
        filtered = filtered[filtered['phase'] == phase]
    return filtered

@app.get("/api/player-stats")
def get_player_stats(
    team: str,
    phase: str = "All Phases",
    season_min: Optional[int] = None,
    season_max: Optional[int] = None,
    venue: Optional[str] = None
):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
        
    team_data = df[df['batting_team'] == team].copy()
    if season_min:
        team_data = team_data[team_data['season'] >= season_min]
    if season_max:
        team_data = team_data[team_data['season'] <= season_max]
    if venue and venue != "All Venues":
        team_data = team_data[team_data['venue'] == venue]
    if phase and phase != "All Phases":
        team_data = team_data[team_data['phase'] == phase]
        
    if team_data.empty:
        return {"stats": []}

    batter_stats = team_data.groupby('striker').agg({
        'runs_off_bat': 'sum',
        'ball': 'count'
    }).reset_index()
    
    batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(2)
    
    # Boundaries
    boundaries = team_data[team_data['runs_off_bat'].isin([4, 6])].groupby('striker').size().reset_index(name='boundaries')
    batter_stats = batter_stats.merge(boundaries, on='striker', how='left').fillna(0)
    
    # Match runs for 30s, 50s, 100s
    match_runs = team_data.groupby(['match_id', 'striker'])['runs_off_bat'].sum().reset_index()
    milestones = match_runs.groupby('striker').agg(
        runs_30=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: ((x >= 30) & (x < 50)).sum()),
        runs_50=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: ((x >= 50) & (x < 100)).sum()),
        runs_100=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: (x >= 100).sum())
    ).reset_index()
    
    batter_stats = batter_stats.merge(milestones, on='striker', how='left').fillna(0)
    batter_stats = batter_stats.rename(columns={'striker': 'batter'})
    
    top_run_scorers = batter_stats.sort_values('runs_off_bat', ascending=False).head(6)
    result = top_run_scorers.to_dict(orient='records')
    return {"stats": result}

from api.charts_legacy import (
    create_runs_distribution_chart, 
    create_strike_rate_comparison, 
    create_boundary_percentage_chart, 
    create_runs_over_progression, 
    create_wicket_timeline,
    create_bowler_economy_chart
)

@app.get('/api/charts/dashboard')
def get_dashboard_charts(
    team: str,
    opponent: Optional[str] = None,
    phase: Optional[str] = None,
    season_min: Optional[int] = None,
    season_max: Optional[int] = None,
    venue: Optional[str] = None
):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    
    filtered = filter_df(df, team=team, opponent=opponent, season_min=season_min, season_max=season_max, venue=venue, phase=phase)
    charts = {}
    try:
        fig_runs = create_runs_distribution_chart(filtered, team, phase)
        if fig_runs: charts['runs_distribution'] = json.loads(fig_runs.to_json())
        
        fig_sr = create_strike_rate_comparison(filtered, phase)
        if fig_sr: charts['strike_rate'] = json.loads(fig_sr.to_json())
        
        fig_prog = create_runs_over_progression(filtered, team, phase)
        if fig_prog: charts['runs_progression'] = json.loads(fig_prog.to_json())
        
        fig_wkt = create_wicket_timeline(filtered, team, phase)
        if fig_wkt: charts['wickets'] = json.loads(fig_wkt.to_json())
        
        fig_econ = create_bowler_economy_chart(filtered, team, phase)
        if fig_econ: charts['bowler_economy'] = json.loads(fig_econ.to_json())

        if opponent:
            fig_bound = create_boundary_percentage_chart(filtered, [team, opponent], phase)
            if fig_bound: charts['boundaries'] = json.loads(fig_bound.to_json())
    except Exception as e:
        print(f'Error generating charts: {e}')
        
    return charts

from ipl_analytics.analytics_engine import (
    calculate_win_probability,
    analyze_toss_venue_impact,
    calculate_player_impact_scores,
    get_season_over_season_comparison,
    export_to_csv
)
from ipl_analytics.predictor_engine import MLFuturePredictor

ml_predictor = MLFuturePredictor()

@app.get('/api/predict/match')
def get_match_prediction(
    team1: str = Query("Chennai Super Kings"),
    team2: str = Query("Mumbai Indians"),
    venue: Optional[str] = Query("Wankhede Stadium"),
    toss_winner: Optional[str] = Query(None),
    toss_decision: Optional[str] = Query("bat")
):
    """Predict future match winner, best batter, best bowler, allrounder, fielder, POTM."""
    if df is not None:
        ml_predictor.set_data(df)
    return ml_predictor.predict_full_match(
        team1=team1,
        team2=team2,
        venue=venue,
        toss_winner=toss_winner or team1,
        toss_decision=toss_decision or "bat"
    )

@app.get('/api/analytics/win-probability')
def get_win_probability(
    target: int = Query(180),
    current_runs: int = Query(90),
    overs_bowled: float = Query(10.0),
    wickets_lost: int = Query(2)
):
    return calculate_win_probability(target, current_runs, overs_bowled, wickets_lost)

@app.get('/api/analytics/toss-venue-impact')
def get_toss_venue_impact(venue: Optional[str] = Query(None)):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    return analyze_toss_venue_impact(df, venue)

@app.get('/api/analytics/player-impact')
def get_player_impact(team: Optional[str] = Query(None)):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    impact_data = calculate_player_impact_scores(df, team)
    return {"impact_scores": impact_data}

@app.get('/api/analytics/season-comparison')
def get_season_comparison(team: str = Query("Chennai Super Kings")):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    return {"seasons": get_season_over_season_comparison(df, team)}

@app.get('/api/pitch-map-data')
def get_pitch_map(
    team: Optional[str] = Query(None),
    bowler_type: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    venue: Optional[str] = Query(None)
):
    """Fetch real Hawk-Eye pitch map coordinates."""
    if hawkeye_processor and hawkeye_processor.has_data():
        pitch_data = hawkeye_processor.get_pitch_map_data(team=team, bowler_type=bowler_type, phase=phase, venue=venue)
        if pitch_data is not None:
            return {"data": pitch_data}
    return {"data": []}

@app.get('/api/wagon-wheel-data')
def get_wagon_wheel(
    team: Optional[str] = Query(None),
    batter: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    venue: Optional[str] = Query(None),
    boundary_radius: Optional[float] = Query(65.0)
):
    """Fetch real Hawk-Eye wagon wheel coordinates scaled to venue boundary radius."""
    if hawkeye_processor and hawkeye_processor.has_data():
        wagon_data = hawkeye_processor.get_wagon_wheel_data(team=team, batter=batter, phase=phase, venue=venue, boundary_radius=boundary_radius)
        if wagon_data is not None:
            return {"data": wagon_data}
    return {"data": []}

@app.get('/api/stumps-view-data')
def get_stumps_view(team: Optional[str] = Query(None), phase: Optional[str] = Query(None)):
    """Fetch stumps / delivery release point ball tracking coordinates."""
    if hawkeye_processor and hawkeye_processor.has_data():
        stumps_data = hawkeye_processor.get_pitch_map_data(team=team, phase=phase)
        if stumps_data is not None:
            # Format coordinates for stumps view (X height, Z deviation)
            formatted = []
            for item in stumps_data[:40]:
                formatted.append({
                    "x": item.get("x", 0),
                    "y": item.get("y", 0.5),
                    "z": item.get("z", 0),
                    "bowler": item.get("bowler", "Unknown"),
                    "speed": item.get("speed", 135),
                    "length": "Good Length" if abs(item.get("z", 0)) < 4 else "Short"
                })
            return {"data": formatted}
    return {"data": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
