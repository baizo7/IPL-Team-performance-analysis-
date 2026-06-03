import re
with open('api/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_startup = '''@app.on_event("startup")
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
'''

code = re.sub(r'@app\.on_event\("startup"\).*?def read_root\(\):', new_startup + '\n@app.get("/")\ndef read_root():', code, flags=re.DOTALL)

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.write(code)
