import codecs
with codecs.open('api/main.py', 'a', 'utf-8') as f:
    f.write('''

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
''')
