import pandas as pd
import sys

# Add directory to path to import legacy_app
sys.path.append('d:\\projects\\IPL+perfromance analysis')
from legacy_app import create_wicket_timeline

# Create dummy data
df = pd.DataFrame({
    'bowling_team': ['Team A', 'Team A', 'Team A'],
    'phase': ['Powerplay', 'Middle', 'Death'],
    'is_wicket': [1, 1, 1],
    'wicket_type': ['bowled', 'caught', 'lbw'],
    'batter': ['Player 1', 'Player 2', 'Player 3'],
    'bowler': ['Bowler 1', 'Bowler 2', 'Bowler 3'],
    'over': [2.1, 10.5, 18.2]
})

try:
    print("Creating chart...")
    fig = create_wicket_timeline(df, 'Team A')
    print("Chart created.")
    
    print("Converting to JSON...")
    import time
    start = time.time()
    fig.to_json()
    print(f"JSON conversion done in {time.time() - start} seconds.")
    print("SUCCESS: Chart rendered and serialized to JSON without errors.")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
