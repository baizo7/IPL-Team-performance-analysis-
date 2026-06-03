from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os

app = FastAPI(title="IPL Analysis API")

# Configure CORS for React frontend (Vite defaults to port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dataframe
df = None

@app.on_event("startup")
def startup_event():
    global df
    print("Loading IPL dataset...")
    file_path = os.path.join(os.path.dirname(__file__), '..', 'all_ipl_matches.csv')
    try:
        df = pd.read_csv(file_path, low_memory=False)
        if 'start_date' in df.columns:
            df['date'] = pd.to_datetime(df['start_date'])
            df['season'] = df['date'].dt.year
            
        # Basic columns
        if 'ball' in df.columns:
            df['ball'] = pd.to_numeric(df['ball'], errors='coerce').fillna(0)
            df['over'] = df['ball'].astype(int) + 1
            
        # Runs
        if 'runs_off_bat' in df.columns and 'extras' in df.columns:
            df['runs_off_bat'] = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
            df['extras'] = pd.to_numeric(df['extras'], errors='coerce').fillna(0)
            df['total_runs'] = df['runs_off_bat'] + df['extras']
            
        # Phase
        df['phase'] = pd.cut(df['over'], bins=[0, 6, 15, 21], labels=['Powerplay', 'Middle', 'Death'])
        
        # Wickets
        if 'wicket_type' in df.columns:
            df['is_wicket'] = df['wicket_type'].notna().astype(int)
        else:
            df['is_wicket'] = 0
            
        print(f"Successfully loaded {len(df)} rows.")
    except Exception as e:
        print(f"Failed to load dataset: {e}")

@app.get("/")
def read_root():
    return {"status": "API is running. Data loaded: " + str(df is not None)}

@app.get("/api/teams")
def get_teams():
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
    teams = sorted(list(set(df['batting_team'].dropna().unique()) | set(df['bowling_team'].dropna().unique())))
    return {"teams": teams}

@app.get("/api/player-stats")
def get_player_stats(team: str, phase: str = "All Phases"):
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded yet")
        
    team_data = df[df['batting_team'] == team].copy()
    if phase and phase != "All Phases":
        team_data = team_data[team_data['phase'] == phase]
        
    batter_stats = team_data.groupby('striker').agg({
        'runs_off_bat': 'sum',
        'ball': 'count'
    }).reset_index()
    
    batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(2)
    
    # Calculate boundaries
    boundaries = team_data[team_data['runs_off_bat'].isin([4, 6])].groupby('striker').size().reset_index(name='boundaries')
    batter_stats = batter_stats.merge(boundaries, on='striker', how='left').fillna(0)
    
    # Calculate match runs for 30s, 50s, 100s
    match_runs = team_data.groupby(['match_id', 'striker'])['runs_off_bat'].sum().reset_index()
    milestones = match_runs.groupby('striker').agg(
        runs_30=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: ((x >= 30) & (x < 50)).sum()),
        runs_50=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: ((x >= 50) & (x < 100)).sum()),
        runs_100=pd.NamedAgg(column='runs_off_bat', aggfunc=lambda x: (x >= 100).sum())
    ).reset_index()
    
    batter_stats = batter_stats.merge(milestones, on='striker', how='left')
    batter_stats = batter_stats.rename(columns={'striker': 'batter'})
    
    top_run_scorers = batter_stats.sort_values('runs_off_bat', ascending=False).head(5)
    
    # Format for JSON response
    result = top_run_scorers.to_dict(orient='records')
    return {"stats": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


from api.charts_legacy import create_runs_distribution_chart, create_strike_rate_comparison, create_boundary_percentage_chart, create_runs_over_progression, create_wicket_timeline
import json

@app.get('/api/charts/dashboard')
def get_dashboard_charts(team: str, opponent: str = None, phase: str = None):
    if df is None: return {'error': 'Data not loaded'}
    charts = {}
    try:
        # 1. Runs Distribution
        fig_runs = create_runs_distribution_chart(df, team, phase)
        if fig_runs: charts['runs_distribution'] = json.loads(fig_runs.to_json())
        
        # 2. Strike Rate Comparison
        fig_sr = create_strike_rate_comparison(df, phase)
        if fig_sr: charts['strike_rate'] = json.loads(fig_sr.to_json())
        
        # 3. Runs Progression
        fig_prog = create_runs_over_progression(df, team, phase)
        if fig_prog: charts['runs_progression'] = json.loads(fig_prog.to_json())
        
        # 4. Wickets Timeline
        fig_wkt = create_wicket_timeline(df, team, phase)
        if fig_wkt: charts['wickets'] = json.loads(fig_wkt.to_json())
        
        if opponent:
            fig_bound = create_boundary_percentage_chart(df, [team, opponent], phase)
            if fig_bound: charts['boundaries'] = json.loads(fig_bound.to_json())
    except Exception as e:
        print(f'Error generating charts: {e}')
        
    return charts


import random

@app.get('/api/pitch-map-data')
def get_pitch_map(team: str):
    if df is None: return {'error': 'Data not loaded'}
    team_data = df[df['bowling_team'] == team]
    if len(team_data) == 0: return {'data': []}
    
    top_bowlers = team_data['bowler'].value_counts().head(5).index.tolist()
    
    pitch_data = []
    # Pitch dimensions: length roughly 20.12m, width 3.05m
    for bowler in top_bowlers:
        # Generate 30 random deliveries per top bowler
        for _ in range(30):
            # length from batsman stumps (0) to bowler stumps (20.12)
            length = random.uniform(2.0, 18.0) 
            # width deviation (-1.5 to 1.5)
            width = random.gauss(0, 0.5) 
            
            # Determine outcome
            outcome_rand = random.random()
            if outcome_rand < 0.1: outcome = "Wicket"
            elif outcome_rand < 0.3: outcome = "Boundary"
            elif outcome_rand < 0.6: outcome = "Dot Ball"
            else: outcome = "Run(s)"
            
            # Speed km/h
            speed = random.uniform(125.0, 150.0)
            
            pitch_data.append({
                "x": width,
                "y": 0.1, # slightly above pitch
                "z": length - 10, # center is 0
                "bowler": bowler,
                "outcome": outcome,
                "speed": round(speed, 1)
            })
            
    return {"data": pitch_data}

import math

@app.get('/api/wagon-wheel-data')
def get_wagon_wheel(team: str):
    if df is None: return {'error': 'Data not loaded'}
    team_data = df[df['batting_team'] == team]
    if len(team_data) == 0: return {'data': []}
    
    # We want to show top scoring shots
    scoring_shots = team_data[team_data['runs_off_bat'] > 0].copy()
    # Sample up to 100 shots to prevent visual clutter
    if len(scoring_shots) > 100:
        scoring_shots = scoring_shots.sample(100)
        
    wagon_data = []
    
    for _, row in scoring_shots.iterrows():
        runs = row['runs_off_bat']
        
        # Determine approximate angle based on runs/random distribution
        # Cricket ground 360 degrees:
        # 0 = Straight down the ground
        # 90 = Square leg / Cover
        # 180 = Fine leg / Third man
        angle_deg = random.uniform(0, 360)
        
        # Distance based on runs
        if runs == 6:
            distance = random.uniform(70, 90) # Over boundary
        elif runs == 4:
            distance = random.uniform(60, 75) # Boundary
        elif runs == 3:
            distance = random.uniform(40, 60)
        elif runs == 2:
            distance = random.uniform(25, 45)
        else: # 1 run
            distance = random.uniform(10, 30)
            
        angle_rad = math.radians(angle_deg)
        x = distance * math.sin(angle_rad)
        z = distance * math.cos(angle_rad) # Using z for depth in 3D
        
        wagon_data.append({
            "x": x,
            "y": 0.5 if runs == 6 else 0.1, # Sixes go higher
            "z": z,
            "runs": int(runs),
            "batter": str(row['striker'])
        })
        
    return {"data": wagon_data}
