"""
Hawk-Eye Simulator - Generates synthetic Hawk-Eye trajectory data for 2022-2026 seasons
using pattern distributions learned from real 2009-2021 Hawk-Eye data.
"""
import pandas as pd
import numpy as np
import os
import json
from hawkeye_pattern_engine import HawkeyePatternEngine

class HawkeyeSimulator:
    def __init__(self, pattern_engine=None):
        self.engine = pattern_engine if pattern_engine is not None else HawkeyePatternEngine()
        self.patterns_loaded = False
    
    def load_patterns(self, pattern_file):
        self.engine.load_patterns(pattern_file)
        self.patterns_loaded = True
    
    def learn_from_real_data(self, real_data_file):
        df = pd.read_csv(real_data_file, low_memory=False)
        self.engine.learn_from_data(df)
        self.patterns_loaded = True
    
    def simulate_season(self, cricsheet_df, season_year, seed=42):
        """Generate synthetic Hawk-Eye data for all deliveries in a season."""
        np.random.seed(seed + int(str(season_year).split('/')[0]))
        
        season_df = cricsheet_df[cricsheet_df['season'].astype(str) == str(season_year)].copy()
        if len(season_df) == 0:
            # Try matching year in format '2020/21'
            for s in cricsheet_df['season'].unique():
                if str(season_year) in str(s):
                    season_df = cricsheet_df[cricsheet_df['season'] == s].copy()
                    break
        
        if len(season_df) == 0:
            print(f"No data found for season {season_year}")
            return None
        
        n = len(season_df)
        
        # Get bowler type for each delivery
        bowler_types = [self.engine.get_bowler_type(name) for name in season_df['bowler']]
        
        # Generate per-delivery trajectory data
        pitch_coords = np.array([self.engine.generate_pitch_coords(bt, 1)[0] for bt in bowler_types])
        stump_coords = np.array([self.engine.generate_stump_coords(bt, 1)[0] for bt in bowler_types])
        speeds = np.array([self.engine.generate_speed(bt, 1)[0] for bt in bowler_types])
        
        # Generate field positions based on runs
        field_coords = np.array([self.engine.generate_field_coords(int(r), 1)[0] for r in season_df['runs_off_bat']])
        
        # Generate new fields per delivery
        swing_vals = np.array([self.engine.generate_swing(bt, 1)[0] for bt in bowler_types])
        deviation_vals = np.array([self.engine.generate_deviation(bt, 1)[0] for bt in bowler_types])
        crease_z_vals = np.array([self.engine.generate_crease_z(1)[0] for _ in bowler_types])
        
        # Six distance only for 6s
        six_dist_vals = np.full(n, np.nan)
        six_mask = season_df['runs_off_bat'] == 6
        if six_mask.any():
            n_sixes = six_mask.sum()
            six_dist_vals[six_mask] = np.random.normal(78, 12, n_sixes)
        
        # Build synthetic dataset
        synthetic = pd.DataFrame({
            'matchId': season_df['match_id'].values,
            'season': season_year,
            'delivery': season_df.apply(
                lambda r: f"{r['innings']}.{r['ball']}", axis=1),
            'ball': season_df['ball'].values,
            'innings': season_df['innings'].values,
            'batter': season_df['striker'].values,
            'bowler': season_df['bowler'].values,
            'bowlerType': bowler_types,
            'ballSpeed': speeds / 3.6,  # Convert km/h back to m/s
            'runs': season_df['runs_off_bat'].values,
            'extras': season_df['extras'].fillna(0).values,
            'wicket': (~season_df['wicket_type'].isna()).astype(int).values,
            'pitchX': pitch_coords[:, 0],
            'pitchY': pitch_coords[:, 1],
            'stumpsX': stump_coords[:, 0],
            'stumpsY': stump_coords[:, 1],
            'fieldX': field_coords[:, 0],
            'fieldY': field_coords[:, 1],
            'swing': swing_vals,
            'deviation': deviation_vals,
            'creaseZ': crease_z_vals,
            'sixDistance': six_dist_vals,
            'dataSource': 'pattern_simulated',
        })
        
        return synthetic
    
    def simulate_seasons(self, cricsheet_df, seasons, output_dir=None):
        """Generate synthetic data for multiple seasons."""
        results = []
        for season in seasons:
            print(f"Simulating {season}...")
            sim = self.simulate_season(cricsheet_df, season)
            if sim is not None:
                results.append(sim)
                print(f"  Generated {len(sim)} deliveries")
        
        if not results:
            return None
        
        combined = pd.concat(results, ignore_index=True)
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(output_dir, 'hawkeye_simulated_2022_2026.csv')
            combined.to_csv(out_path, index=False)
            print(f"\nSaved {len(combined)} simulated deliveries to {out_path}")
        
        return combined


def build_for_dashboard(real_data_file, cricsheet_file, pattern_file, output_dir):
    """Build complete pipeline: learn patterns -> simulate -> combine."""
    print("=== Learning patterns from real Hawk-Eye data ===")
    real_df = pd.read_csv(real_data_file, low_memory=False)
    engine = HawkeyePatternEngine()
    engine.learn_from_data(real_df)
    
    # Save patterns with bowler lookup
    dists = {}
    for bt, d in engine.distributions.items():
        dists[bt] = {}
        for k, v in d.items():
            if isinstance(v, (np.floating, np.integer)):
                dists[bt][k] = float(v)
            else:
                dists[bt][k] = v
    
    with open(pattern_file, 'w') as f:
        json.dump({
            'bowler_types': dists,
            'field_positions': engine.field_distributions,
            'bowler_lookup': {k: v for k, v in engine.bowler_lookup.items()}
        }, f, indent=2)
    print(f"Saved patterns to {pattern_file}")
    
    print("\n=== Simulating 2022-2026 data ===")
    sim = HawkeyeSimulator(engine)
    cricsheet = pd.read_csv(cricsheet_file, low_memory=False, dtype={'season': str})
    
    valid_seasons = [s for s in ['2022', '2023', '2024', '2025', '2026'] if s in cricsheet['season'].unique()]
    
    if not valid_seasons:
        print("No 2022-2026 seasons found. Available:", cricsheet['season'].unique())
        return
    
    combined = sim.simulate_seasons(cricsheet, valid_seasons, output_dir)
    
    if combined is not None:
        print(f"\n=== Final dataset: {len(combined)} deliveries ===")
        print(combined[['matchId', 'season', 'ballSpeed', 'pitchX', 'pitchY', 'dataSource']].head(10))


if __name__ == "__main__":
    build_for_dashboard(
        real_data_file="D:\\projects\\IPL+perfromance analysis\\hawkeye_mens_ipl.csv",
        cricsheet_file="D:\\projects\\IPL+perfromance analysis\\all_ipl_matches.csv",
        pattern_file="D:\\projects\\IPL+perfromance analysis\\hawkeye_pattern_distributions.json",
        output_dir="D:\\projects\\IPL+perfromance analysis"
    )
