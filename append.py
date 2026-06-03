with open('api/main.py', 'a', encoding='utf-8') as f:
    f.write('''

from charts_legacy import create_runs_distribution_chart, create_strike_rate_comparison, create_boundary_percentage_chart, create_runs_over_progression, create_wicket_timeline
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
''')
