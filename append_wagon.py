import codecs
with codecs.open('api/main.py', 'a', 'utf-8') as f:
    f.write('''
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
''')
