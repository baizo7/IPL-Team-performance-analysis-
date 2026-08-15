"""
Hawkeye data processor for IPL ball-tracking data.
Loads real Hawk-Eye data (2009-2021) and pattern-simulated data (2022+).
Provides pitchX/pitchY, fieldX/fieldY, ball speed, stumps coordinates,
swing, deviation, crease position, and six-hit distance.
"""
import hashlib
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent

class HawkeyeProcessor:
    def __init__(self, hawkeye_path=None, simulated_path=None, mapping_path=None):
        self.hawkeye_path = hawkeye_path or str(DATA_DIR / 'hawkeye_mens_ipl.csv')
        self.simulated_path = simulated_path or str(DATA_DIR / 'hawkeye_simulated_2022_2026.csv')
        self.mapping_path = mapping_path or str(DATA_DIR / 'hawkeye_match_map.json')
        self.df = None
        self.match_map = {}
        self._loaded = False
        
        # New field columns
        self.new_fields = ['swing', 'deviation', 'creaseZ', 'sixDistance']
        
    def load(self):
        if self._loaded:
            return self.df
        
        frames = []
        
        # Load real Hawk-Eye data (2009-2021)
        if os.path.exists(self.hawkeye_path):
            real_df = pd.read_csv(self.hawkeye_path)
            try:
                from ipl_data_cleaner import clean_hawkeye_mens_dataset
                real_df, _ = clean_hawkeye_mens_dataset(real_df)
            except Exception as e:
                print(f"Cleaner warning (real hawkeye): {e}")
            real_df['dataSource'] = 'hawkeye'
            frames.append(real_df)
            print(f"Loaded {len(real_df)} cleaned real Hawk-Eye deliveries")
        
        # Load simulated data (2022+)
        if self.simulated_path and os.path.exists(self.simulated_path):
            sim_df = pd.read_csv(self.simulated_path, low_memory=False)
            try:
                from ipl_data_cleaner import clean_hawkeye_simulated_dataset
                sim_df, _ = clean_hawkeye_simulated_dataset(sim_df)
            except Exception as e:
                print(f"Cleaner warning (sim hawkeye): {e}")
            sim_df['dataSource'] = sim_df.get('dataSource', 'pattern_simulated')
            # Convert matchId to int if string
            if sim_df['matchId'].dtype == object:
                sim_df['matchId'] = sim_df['matchId'].astype(float).astype('Int64')
            frames.append(sim_df)
            print(f"Loaded {len(sim_df)} cleaned simulated deliveries (2022+)")
        
        if not frames:
            print("No Hawk-Eye data found")
            return None
        
        self.df = pd.concat(frames, ignore_index=True)
        
        # Load team mapping
        if os.path.exists(self.mapping_path):
            with open(self.mapping_path) as f:
                raw = json.load(f)
                self.match_map = {int(k): v for k, v in raw.items()}
        
        if not self.match_map:
            print("No team mapping found. Some features limited.")
        
        # Build team map from Cricsheet data for simulated matches not in match_map
        cricsheet_file = str(DATA_DIR / 'all_ipl_matches.csv')
        if os.path.exists(cricsheet_file):
            try:
                cric = pd.read_csv(cricsheet_file, low_memory=False)
                cric_uniq = cric.drop_duplicates(subset=['match_id'])
                existing = set(self.match_map.keys())
                added = 0
                for _, r in cric_uniq.iterrows():
                    try:
                        mid_int = int(r['match_id'])
                    except (ValueError, TypeError):
                        continue
                    if mid_int in existing:
                        continue
                    t1, t2 = r.get('batting_team'), r.get('bowling_team')
                    season_raw = r.get('season')
                    season_str = str(season_raw).split('/')[0][:4] if pd.notna(season_raw) else 'unknown'
                    venue_raw = r.get('venue') if 'venue' in r and pd.notna(r['venue']) else None
                    self.match_map[mid_int] = {'season': season_str, 'teams': [t1, t2], 'venue': venue_raw}
                    added += 1
                if added:
                    print(f"Added {added} match mappings from Cricsheet")
                    
                # Build squad team_batters_map from all_ipl_matches.parquet to enforce strict player-to-team filtering
                try:
                    parquet_path = str(BASE_DIR / 'all_ipl_matches.parquet')
                    if os.path.exists(parquet_path):
                        cric_df = pd.read_parquet(parquet_path)
                        stk_col = 'striker' if 'striker' in cric_df.columns else 'batter'
                        bwl_col = 'bowler' if 'bowler' in cric_df.columns else None
                        self.team_batters_map = cric_df.groupby('batting_team')[stk_col].unique().to_dict()
                        if bwl_col:
                            self.team_bowlers_map = cric_df.groupby('bowling_team')[bwl_col].unique().to_dict()
                    else:
                        stk_col = 'striker' if 'striker' in cric.columns else ('batter' if 'batter' in cric.columns else None)
                        bwl_col = 'bowler' if 'bowler' in cric.columns else None
                        if stk_col:
                            self.team_batters_map = cric.groupby('batting_team')[stk_col].unique().to_dict()
                        else:
                            self.team_batters_map = {}
                        if bwl_col:
                            self.team_bowlers_map = cric.groupby('bowling_team')[bwl_col].unique().to_dict()
                        else:
                            self.team_bowlers_map = {}
                except Exception:
                    self.team_batters_map = {}
                    self.team_bowlers_map = {}
            except Exception as e:
                print(f"Could not load Cricsheet mapping: {e}")
        
        def parse_over_ball_cricsheet(ball_val):
            """Parse Cricsheet 'over.ball' format (0.1, 0.2, ..., 19.6)."""
            try:
                b = float(ball_val)
                over = int(b)
                ball_in_over = int(round((b - over) * 10))
                return over + 1, ball_in_over
            except (ValueError, TypeError):
                return 0, 0
        
        if 'delivery' in self.df.columns:
            def parse_real_delivery(d):
                parts = str(d).split('.')
                if len(parts) == 3:
                    return int(parts[0]), int(parts[1]), int(parts[2])
                return None, 0, 0
            
            parsed = self.df['delivery'].apply(parse_real_delivery)
            inns_list = [p[0] for p in parsed]
            over_list = [p[1] for p in parsed]
            ball_list = [p[2] for p in parsed]
            
            # Fill innings only where it's NaN (real data has innings encoded in delivery)
            if 'innings' not in self.df.columns:
                self.df['innings'] = inns_list
            else:
                mask = self.df['innings'].isna()
                if mask.any():
                    inns_arr = np.array(inns_list)
                    self.df.loc[mask, 'innings'] = inns_arr[mask.to_numpy()]
            
            self.df['over'] = over_list
            self.df['ball_in_over'] = ball_list
        
        if 'ball' in self.df.columns and self.df['ball'].dtype in ['float64', 'int64']:
            # Cricsheet-style ball column (0.1, 0.2, ... 19.6)
            overs = []
            balls = []
            for v in self.df['ball']:
                ov, bv = parse_over_ball_cricsheet(v)
                overs.append(ov)
                balls.append(bv)
            
            # Only overwrite if delivery parsing didn't work or isn't available
            if 'over' not in self.df.columns or self.df['over'].isna().all():
                self.df['over'] = overs
                self.df['ball_in_over'] = balls
        
        # Add phase
        if 'over' in self.df.columns:
            self.df['phase'] = pd.cut(
                self.df['over'],
                bins=[0, 6, 15, 21],
                labels=['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
            )
        
        # Convert ballSpeed m/s to km/h if needed
        if 'ballSpeed' in self.df.columns and 'ball_speed_kmh' not in self.df.columns:
            self.df['ball_speed_kmh'] = self.df['ballSpeed'] * 3.6
            self.df['ball_speed_kmh'] = self.df['ball_speed_kmh'].replace(-3.6, np.nan)
        
        # Clip pitch coordinates
        if 'pitchX' in self.df.columns:
            self.df['pitchX'] = self.df['pitchX'].clip(-2.5, 2.5)
            self.df['pitchY'] = self.df['pitchY'].clip(0, 22)
        
        # Clip stump coordinates
        if 'stumpsX' in self.df.columns:
            self.df['stumpsX'] = self.df['stumpsX'].clip(-1.5, 1.5)
            self.df['stumpsY'] = self.df['stumpsY'].clip(-0.5, 2.0)
        
        # Add team info
        self._add_team_info()
        
        # Compute wickets
        if 'dismissalDetails' in self.df.columns:
            self.df['is_wicket'] = self.df['dismissalDetails'].notna().astype(int)
        elif 'wicket' in self.df.columns:
            self.df['is_wicket'] = self.df['wicket'].astype(int)
        else:
            self.df['is_wicket'] = 0
        
        # Rename for compatibility
        if 'runs_off_bat' not in self.df.columns and 'runs' in self.df.columns:
            self.df['runs_off_bat'] = self.df['runs']
        elif 'runs' not in self.df.columns and 'runs_off_bat' in self.df.columns:
            self.df['runs'] = self.df['runs_off_bat']
        
        if 'batter' in self.df.columns:
            self.df['batter_name'] = self.df['batter']
        if 'bowler' in self.df.columns:
            self.df['bowler_name'] = self.df['bowler']
        
        # Force detailed bowlerType mapping based on bowler name to match UI perfectly
        if 'bowler' in self.df.columns:
            try:
                from ipl_data_loader import _guess_bowler_type
                self.df['bowlerType'] = self.df['bowler'].apply(_guess_bowler_type)
            except ImportError:
                pass
        
        # Fill new fields with NaN if missing
        for field in self.new_fields:
            if field not in self.df.columns:
                self.df[field] = np.nan
        
        # Add season info for simulated (already has season column)
        if 'season' not in self.df.columns and self.match_map:
            self.df['season'] = self.df['matchId'].map(
                lambda mid: self.match_map.get(mid, {}).get('season', 'unknown')
            )
        
        self._loaded = True
        return self.df
    
    def _add_team_info(self):
        if not self.match_map or self.df is None or len(self.df) == 0:
            return
        
        # Build map dictionaries for fast vectorized lookups
        match_teams = {}
        match_venues = {}
        for mid, info in self.match_map.items():
            teams = info.get('teams')
            if teams and len(teams) >= 2:
                match_teams[mid] = (teams[0], teams[1])
            venue = info.get('venue')
            if venue:
                match_venues[mid] = venue
        
        mids = pd.to_numeric(self.df['matchId'], errors='coerce')
        innings = pd.to_numeric(self.df.get('innings', 1), errors='coerce').fillna(1).astype(int)
        
        team_tuples = mids.map(match_teams)
        t1_series = team_tuples.map(lambda x: x[0] if isinstance(x, tuple) and len(x) >= 2 else None)
        t2_series = team_tuples.map(lambda x: x[1] if isinstance(x, tuple) and len(x) >= 2 else None)
        
        self.df['batting_team'] = np.where(innings == 1, t1_series, np.where(innings == 2, t2_series, None))
        self.df['bowling_team'] = np.where(innings == 1, t2_series, np.where(innings == 2, t1_series, None))
        
        if 'venue' not in self.df.columns or self.df['venue'].isna().all():
            self.df['venue'] = mids.map(match_venues)
        
        try:
            from ipl_data_cleaner import TEAM_MAPPING, clean_venues
            self.df['batting_team'] = self.df['batting_team'].map(lambda t: TEAM_MAPPING.get(t, t) if pd.notna(t) else t)
            self.df['bowling_team'] = self.df['bowling_team'].map(lambda t: TEAM_MAPPING.get(t, t) if pd.notna(t) else t)
            self.df, _ = clean_venues(self.df)
        except Exception:
            pass
    
    def has_data(self):
        return self._loaded and self.df is not None and len(self.df) > 0
    
    def get_data_summary(self):
        """Return summary of loaded data."""
        if not self.has_data():
            return {'total': 0}
        
        real = len(self.df[self.df['dataSource'] == 'hawkeye']) if 'dataSource' in self.df.columns else 0
        sim = len(self.df[self.df['dataSource'] == 'pattern_simulated']) if 'dataSource' in self.df.columns else 0
        
        seasons = self.df['season'].value_counts().to_dict() if 'season' in self.df.columns else {}
        
        return {
            'total': len(self.df),
            'real_hawkeye': real,
            'pattern_simulated': sim,
            'seasons': {str(k): int(v) for k, v in seasons.items()},
            'has_swing': self.df['swing'].notna().any(),
            'has_deviation': self.df['deviation'].notna().any(),
            'has_crease': self.df['creaseZ'].notna().any(),
            'has_six_distance': self.df['sixDistance'].notna().any(),
        }
    
    def get_teams(self):
        if not self.has_data():
            return []
        teams = pd.unique(self.df['batting_team'].dropna()).tolist()
        return sorted(teams)
    
    def get_bowler_types(self):
        """Get available bowler types for filtering."""
        if not self.has_data():
            return ['All Types']
        types = pd.unique(self.df['bowlerType'].dropna()).tolist()
        return ['All Types'] + sorted(types)
    
    def _normalize_bowler_type(self, bt):
        if not bt or bt == 'All Types':
            return None
        if isinstance(bt, list):
            res = []
            for item in bt:
                norm = self._normalize_bowler_type(item)
                if isinstance(norm, list):
                    res.extend(norm)
                elif norm:
                    res.append(norm)
            return list(set(res)) if res else None
        
        bt_lower = str(bt).lower().strip()
        if bt_lower == 'pace':
            return ['Right-Arm Pace', 'Left-Arm Pace']
        if bt_lower == 'spin':
            return ['Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
        if 'right' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
            return 'Right-Arm Pace'
        if 'left' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
            return 'Left-Arm Pace'
        if 'off' in bt_lower or 'offbreak' in bt_lower:
            return 'Right-Arm Off Spin'
        if 'leg' in bt_lower or 'legbreak' in bt_lower:
            return 'Right-Arm Leg Spin'
        if 'orthodox' in bt_lower:
            return 'Left-Arm Orthodox'
        if 'wrist' in bt_lower or 'unorthodox' in bt_lower:
            return 'Left-Arm Wrist Spin'
        return bt

    def get_pitch_map_data(self, team=None, bowler_type=None, phase=None, max_samples=500, source=None, venue=None, over_range=None, *args, **kwargs):
        if not self.has_data():
            return None
        
        venue = venue or kwargs.get('venue')
        over_range = over_range or kwargs.get('over_range')
        opp_team = kwargs.get('opp_team')
        filtered = self.df.copy()
        if team:
            team_aliases = [team]
            if team == 'Royal Challengers Bengaluru':
                team_aliases.append('Royal Challengers Bangalore')
            elif team == 'Royal Challengers Bangalore':
                team_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['batting_team'].isin(team_aliases)]

        if opp_team:
            opp_aliases = [opp_team]
            if opp_team == 'Royal Challengers Bengaluru':
                opp_aliases.append('Royal Challengers Bangalore')
            elif opp_team == 'Royal Challengers Bangalore':
                opp_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['bowling_team'].isin(opp_aliases)]

        if venue and venue != 'All Venues' and 'venue' in filtered.columns:
            filtered = filtered[filtered['venue'] == venue]
            
        norm_bt = self._normalize_bowler_type(bowler_type)
        if norm_bt:
            if isinstance(norm_bt, list):
                filtered = filtered[filtered['bowlerType'].isin(norm_bt)]
            else:
                filtered = filtered[filtered['bowlerType'] == norm_bt]
        if phase:
            filtered = filtered[filtered['phase'] == phase]
        if over_range and len(over_range) == 2 and 'over' in filtered.columns:
            filtered = filtered[(filtered['over'] >= over_range[0]) & (filtered['over'] <= over_range[1])]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        elif 'dataSource' in filtered.columns:
            real_subset = filtered[filtered['dataSource'] == 'hawkeye']
            if len(real_subset) > 0:
                filtered = real_subset
        
        filtered = filtered.dropna(subset=['pitchX', 'pitchY'])
        
        if len(filtered) == 0:
            return None
        
        # Sort by latest seasons / matchId / over to showcase latest deliveries
        if 'season' in filtered.columns:
            filtered = filtered.assign(season_num=pd.to_numeric(filtered['season'], errors='coerce').fillna(2015))
            match_col = 'matchId' if 'matchId' in filtered.columns else filtered.columns[0]
            over_col = 'over' if 'over' in filtered.columns else filtered.columns[0]
            filtered = filtered.sort_values(by=['season_num', match_col, over_col], ascending=False)
        
        # Preserve 100% of ALL WICKETS so wickets are never dropped during sampling
        if len(filtered) > max_samples:
            w_rows = filtered[filtered['is_wicket'] == 1]
            nw_rows = filtered[filtered['is_wicket'] == 0]
            num_nw = max(0, max_samples - len(w_rows))
            filtered = pd.concat([w_rows, nw_rows.head(num_nw)], ignore_index=True)
            if 'season_num' in filtered.columns:
                filtered = filtered.sort_values(by=['season_num', match_col, over_col], ascending=False)
        
        result = []
        for _, row in filtered.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            is_wicket = bool(row.get('is_wicket', False))
            
            if is_wicket:
                color = 'red'; size = 12
            elif runs >= 6:
                color = 'purple'; size = 14
            elif runs == 4:
                color = 'green'; size = 10
            elif runs >= 1:
                color = 'blue'; size = 6
            else:
                color = 'gray'; size = 4
            
            src = row.get('dataSource', 'hawkeye')
            
            result.append({
                'x': float(row['pitchX']),
                'y': float(row['pitchY']),
                'runs': runs,
                'wicket': int(is_wicket),
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown')),
                'ball_speed': float(row.get('ball_speed_kmh', 0)) if pd.notna(row.get('ball_speed_kmh', np.nan)) else 0,
                'source': src,
            })
        
        return result

    def get_stumps_view_data(self, team=None, batter=None, bowler_type=None, phase=None, venue=None, source=None, max_samples=400, over_range=None, *args, **kwargs):
        """Fetch real Hawk-Eye stumps view data (stumpsX line & creaseZ height at stumps)."""
        if not self.has_data():
            return None
        
        over_range = over_range or kwargs.get('over_range')
        opp_team = kwargs.get('opp_team')
        filtered = self.df.copy()
        if team:
            team_aliases = [team]
            if team == 'Royal Challengers Bengaluru':
                team_aliases.append('Royal Challengers Bangalore')
            elif team == 'Royal Challengers Bangalore':
                team_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['batting_team'].isin(team_aliases)]

        if opp_team:
            opp_aliases = [opp_team]
            if opp_team == 'Royal Challengers Bengaluru':
                opp_aliases.append('Royal Challengers Bangalore')
            elif opp_team == 'Royal Challengers Bangalore':
                opp_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['bowling_team'].isin(opp_aliases)]

        if batter:
            filtered = filtered[filtered['batter'] == batter]
        if venue and venue != 'All Venues' and 'venue' in filtered.columns:
            filtered = filtered[filtered['venue'] == venue]
        norm_bt = self._normalize_bowler_type(bowler_type)
        if norm_bt:
            if isinstance(norm_bt, list):
                filtered = filtered[filtered['bowlerType'].isin(norm_bt)]
            else:
                filtered = filtered[filtered['bowlerType'] == norm_bt]
        if phase:
            filtered = filtered[filtered['phase'] == phase]
        if over_range and len(over_range) == 2 and 'over' in filtered.columns:
            filtered = filtered[(filtered['over'] >= over_range[0]) & (filtered['over'] <= over_range[1])]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        elif 'dataSource' in filtered.columns:
            real_subset = filtered[filtered['dataSource'] == 'hawkeye']
            if len(real_subset) > 0:
                filtered = real_subset
        
        sx_col = 'stumpsX' if 'stumpsX' in filtered.columns else ('pitchX' if 'pitchX' in filtered.columns else None)
        sz_col = 'stumpsY' if 'stumpsY' in filtered.columns and filtered['stumpsY'].notna().any() else ('creaseZ' if 'creaseZ' in filtered.columns else None)
        
        if not sx_col:
            return None
            
        if sx_col and sz_col:
            filtered = filtered.dropna(subset=[sx_col, sz_col])
            filtered = filtered[
                (filtered[sx_col] >= -2.0) & (filtered[sx_col] <= 2.0) &
                (filtered[sz_col] >= 0.05) & (filtered[sz_col] <= 2.5)
            ]
        else:
            filtered = filtered.dropna(subset=[sx_col])

        if len(filtered) == 0:
            return None

        # Sort by latest seasons / matchId / over
        if 'season' in filtered.columns:
            filtered = filtered.assign(season_num=pd.to_numeric(filtered['season'], errors='coerce').fillna(2015))
            match_col = 'matchId' if 'matchId' in filtered.columns else filtered.columns[0]
            over_col = 'over' if 'over' in filtered.columns else filtered.columns[0]
            filtered = filtered.sort_values(by=['season_num', match_col, over_col], ascending=False)
        
        # Preserve 100% of ALL WICKETS
        if len(filtered) > max_samples:
            w_rows = filtered[filtered['is_wicket'] == 1]
            nw_rows = filtered[filtered['is_wicket'] == 0]
            num_nw = max(0, max_samples - len(w_rows))
            filtered = pd.concat([w_rows, nw_rows.head(num_nw)], ignore_index=True)
            if 'season_num' in filtered.columns:
                filtered = filtered.sort_values(by=['season_num', match_col, over_col], ascending=False)

        result = []
        for _, row in filtered.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            is_wicket = bool(row.get('is_wicket', False))
            
            if is_wicket:
                color = 'red'; size = 10
            elif runs >= 6:
                color = 'purple'; size = 12
            elif runs == 4:
                color = 'green'; size = 8
            elif runs >= 1:
                color = 'blue'; size = 6
            else:
                color = 'gray'; size = 4
                
            x_val = float(row[sx_col])
            y_val = float(row[sz_col]) if sz_col and pd.notna(row[sz_col]) else 1.25
            
            # Clamp within realistic stumps view viewport bounds (-2.5m to +2.5m, 0.1m to 2.8m)
            x_val = max(-2.5, min(2.5, x_val))
            y_val = max(0.1, min(2.8, y_val))
            
            result.append({
                'x': x_val,
                'y': y_val,
                'runs': runs,
                'wicket': int(is_wicket),
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown')),
                'source': row.get('dataSource', 'hawkeye')
            })
            
        return result
    
    def get_wagon_wheel_data(self, team=None, batter=None, bowler_type=None, phase=None, venue=None, source=None, boundary_radius=None, max_samples=400, over_range=None, *args, **kwargs):
        if not self.has_data():
            return None
        
        over_range = over_range or kwargs.get('over_range')
        opp_team = kwargs.get('opp_team')
        filtered = self.df.copy()
        if team:
            team_aliases = [team]
            if team == 'Royal Challengers Bengaluru':
                team_aliases.append('Royal Challengers Bangalore')
            elif team == 'Royal Challengers Bangalore':
                team_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['batting_team'].isin(team_aliases)]

        if opp_team:
            opp_aliases = [opp_team]
            if opp_team == 'Royal Challengers Bengaluru':
                opp_aliases.append('Royal Challengers Bangalore')
            elif opp_team == 'Royal Challengers Bangalore':
                opp_aliases.append('Royal Challengers Bengaluru')
            filtered = filtered[filtered['bowling_team'].isin(opp_aliases)]

        if batter:
            filtered = filtered[filtered['batter'] == batter]
        if venue and venue != 'All Venues' and 'venue' in filtered.columns:
            filtered = filtered[filtered['venue'] == venue]
        norm_bt = self._normalize_bowler_type(bowler_type)
        if norm_bt:
            if isinstance(norm_bt, list):
                filtered = filtered[filtered['bowlerType'].isin(norm_bt)]
            else:
                filtered = filtered[filtered['bowlerType'] == norm_bt]
        if phase:
            filtered = filtered[filtered['phase'] == phase]
        if over_range and len(over_range) == 2 and 'over' in filtered.columns:
            filtered = filtered[(filtered['over'] >= over_range[0]) & (filtered['over'] <= over_range[1])]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        elif 'dataSource' in filtered.columns:
            real_subset = filtered[filtered['dataSource'] == 'hawkeye']
            if len(real_subset) > 0:
                filtered = real_subset
        
        filtered = filtered[filtered['runs_off_bat'] > 0]
        filtered = filtered.dropna(subset=['fieldX', 'fieldY'])
        
        if len(filtered) == 0:
            return None
        
        # Sort by latest seasons / matchId / over to showcase latest deliveries
        if 'season' in filtered.columns:
            filtered = filtered.assign(season_num=pd.to_numeric(filtered['season'], errors='coerce').fillna(2015))
            match_col = 'matchId' if 'matchId' in filtered.columns else filtered.columns[0]
            over_col = 'over' if 'over' in filtered.columns else filtered.columns[0]
            filtered = filtered.sort_values(by=['season_num', match_col, over_col], ascending=False)

        if len(filtered) > max_samples:
            filtered = filtered.head(max_samples)
        
        # Striker pitch crease origin in 2D field grid space (fieldX=50.0, fieldY=34.0)
        X0, Y0 = 50.0, 34.0
        
        # Boundary radius target (meters) from venue stadium size
        b_radius = float(boundary_radius) if boundary_radius and float(boundary_radius) > 0 else 65.0
        
        def classify_scoring_zone(angle_deg):
            """Classify scoring zone sector based on angle relative to striker crease"""
            if 67.5 <= angle_deg <= 112.5:
                return "Straight / Long-On / Long-Off"
            elif 22.5 <= angle_deg < 67.5:
                return "Mid-Wicket / Cow Corner"
            elif -22.5 <= angle_deg < 22.5:
                return "Square Leg / Mid-Wicket"
            elif -67.5 <= angle_deg < -22.5:
                return "Fine Leg / Backward Square Leg"
            elif 112.5 < angle_deg <= 157.5:
                return "Extra Cover / Cover Drive"
            elif angle_deg > 157.5 or angle_deg < -157.5:
                return "Point / Cover"
            else:
                return "Third Man / Backward Point"

        result = []
        for _, row in filtered.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            fx = float(row['fieldX'])
            fy = float(row['fieldY'])
            
            if runs == 6:
                color = 'red'; size = 14
            elif runs == 4:
                color = 'red'; size = 11
            elif runs == 3:
                color = 'blue'; size = 8
            elif runs == 2:
                color = 'orange'; size = 7
            else:
                color = 'green'; size = 6
            
            # Displacement relative to striker crease
            dx = fx - X0
            dy = fy - Y0
            raw_r = np.sqrt(dx*dx + dy*dy)
            
            if raw_r < 0.01:
                vx, vy = 0.0, 0.0
                angle_deg = 90.0
            else:
                angle_rad = np.arctan2(dy, dx)
                angle_deg = float(np.degrees(angle_rad))
                
                # Batter origin offset in stadium 3D space is z_bat = -10.06m
                z_bat = -10.06
                cos_a = np.cos(angle_rad)
                sin_a = np.sin(angle_rad)
                
                # Exact distance t_rope from batter to stadium boundary circle (b_radius) at angle_rad
                disc = z_bat**2 * cos_a**2 + (b_radius**2 - z_bat**2)
                t_rope = -z_bat * cos_a + np.sqrt(max(disc, 0.0))
                
                # Dynamic variation factor per delivery based on actual HawkEye raw distance
                variation = min(max(raw_r / 50.0, 0.85), 1.15)
                
                if runs >= 6:
                    target_dist = t_rope * (1.04 + (variation - 0.85) * 0.4)
                elif runs == 4:
                    target_dist = t_rope * (0.98 + (variation - 0.85) * 0.07)
                elif runs == 3:
                    target_dist = t_rope * 0.78
                elif runs == 2:
                    target_dist = t_rope * 0.55
                else: # 1 run
                    target_dist = t_rope * 0.30

                vx = target_dist * sin_a
                vy = target_dist * cos_a

            zone = classify_scoring_zone(angle_deg)
            
            # Calculate 3D parabolic arc apex height (meters)
            if runs == 6:
                apex_y = round(16.0 + (target_dist / 65.0) * 8.0, 1)
            elif runs == 4:
                apex_y = round(2.5 + (target_dist / 65.0) * 2.0, 1)
            else:
                apex_y = round(0.5 + (target_dist / 65.0) * 1.2, 1)

            result.append({
                'x': round(vx, 2),
                'y': round(vy, 2),
                'apex_y': apex_y,
                'distance': round(float(target_dist), 1),
                'angle_deg': round(float(angle_deg), 1),
                'runs': runs,
                'color': color,
                'size': size,
                'zone': zone,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown')),
                'ball_speed': float(row.get('ball_speed_kmh', 0)) if pd.notna(row.get('ball_speed_kmh', np.nan)) else 0,
                'source': row.get('dataSource', 'hawkeye'),
            })
        
        return result
    
    def get_bowler_analysis(self, team=None):
        if not self.has_data():
            return None
        
        filtered = self.df.copy()
        if team:
            filtered = filtered[filtered['bowling_team'] == team]
        
        stats = filtered.groupby('bowler').agg(
            balls=('ball', 'count'),
            runs=('runs_off_bat', 'sum'),
            wickets=('is_wicket', 'sum'),
            avg_speed_kmh=('ball_speed_kmh', 'mean'),
            max_speed_kmh=('ball_speed_kmh', 'max'),
            pitchX_mean=('pitchX', 'mean'),
            pitchY_mean=('pitchY', 'mean'),
            avg_swing=('swing', 'mean'),
            avg_deviation=('deviation', 'mean'),
        ).reset_index()
        
        stats = stats[stats['balls'] >= 12]
        stats['economy'] = (stats['runs'] / (stats['balls'] / 6)).round(2)
        stats['avg_speed_kmh'] = stats['avg_speed_kmh'].round(1)
        stats['max_speed_kmh'] = stats['max_speed_kmh'].round(1)
        
        return stats.sort_values('economy')
    
    def get_swing_analysis(self, bowler_type=None, team=None, phase=None, source=None):
        """Analyze swing patterns per bowler type."""
        if not self.has_data() or 'swing' not in self.df.columns:
            return None
        
        filtered = self.df.dropna(subset=['swing']).copy()
        if bowler_type and bowler_type != 'All Types':
            if isinstance(bowler_type, list):
                filtered = filtered[filtered['bowlerType'].isin(bowler_type)]
            else:
                filtered = filtered[filtered['bowlerType'] == bowler_type]
        if team:
            filtered = filtered[filtered['bowling_team'] == team]
        if phase:
            filtered = filtered[filtered['phase'] == phase]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        
        if len(filtered) == 0:
            return None
        
        stats = filtered.groupby('bowlerType').agg(
            deliveries=('swing', 'count'),
            avg_swing=('swing', 'mean'),
            max_swing=('swing', 'max'),
            avg_deviation=('deviation', 'mean'),
            max_deviation=('deviation', 'max'),
        ).reset_index()
        
        return stats
    
    def get_length_analysis(self, bowler_type=None, team=None, source=None):
        """Pitch length distribution analysis using pitchY."""
        if not self.has_data():
            return None
        
        filtered = self.df.dropna(subset=['pitchY']).copy()
        if bowler_type and bowler_type != 'All Types':
            if isinstance(bowler_type, list):
                filtered = filtered[filtered['bowlerType'].isin(bowler_type)]
            else:
                filtered = filtered[filtered['bowlerType'] == bowler_type]
        if team:
            filtered = filtered[filtered['bowling_team'] == team]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        
        if len(filtered) == 0:
            return None
        
        def classify_length(y):
            if y < 2:
                return 'Yorker'
            elif y < 6:
                return 'Full'
            elif y < 12:
                return 'Length'
            else:
                return 'Short'
        
        filtered['length'] = filtered['pitchY'].apply(classify_length)
        
        stats = filtered.groupby(['bowlerType', 'length']).agg(
            count=('pitchY', 'count'),
        ).reset_index()
        
        total = stats.groupby('bowlerType')['count'].transform('sum')
        stats['percentage'] = (stats['count'] / total * 100).round(1)
        
        return stats
    
    def get_corridor_analysis(self, bowler_type=None, team=None, source=None):
        """Off-stump corridor analysis using stumpsX."""
        if not self.has_data():
            return None
        
        filtered = self.df.dropna(subset=['stumpsX']).copy()
        if bowler_type and bowler_type != 'All Types':
            if isinstance(bowler_type, list):
                filtered = filtered[filtered['bowlerType'].isin(bowler_type)]
            else:
                filtered = filtered[filtered['bowlerType'] == bowler_type]
        if team:
            filtered = filtered[filtered['bowling_team'] == team]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        
        if len(filtered) == 0:
            return None
        
        def classify_corridor(sx):
            if sx < -0.3:
                return 'Outside Off'
            elif sx < 0.1:
                return 'Off Stump'
            elif sx < 0.4:
                return 'Middle-Leg'
            else:
                return 'Down Leg'
        
        filtered['corridor'] = filtered['stumpsX'].apply(classify_corridor)
        
        stats = filtered.groupby(['bowlerType', 'corridor']).agg(
            count=('stumpsX', 'count'),
            avg_speed=('ball_speed_kmh', 'mean'),
            wickets=('is_wicket', 'sum'),
        ).reset_index()
        stats['wicket_pct'] = (stats['wickets'] / stats['count'] * 100).round(2)
        
        return stats
    
    def get_six_distance_analysis(self, team=None, batter=None, source=None):
        """Analyze six-hit distances."""
        if not self.has_data() or 'sixDistance' not in self.df.columns:
            return None
        
        filtered = self.df.dropna(subset=['sixDistance']).copy()
        if team:
            filtered = filtered[filtered['batting_team'] == team]
        if batter:
            filtered = filtered[filtered['batter'] == batter]
        if source and 'dataSource' in filtered.columns:
            filtered = filtered[filtered['dataSource'] == source]
        
        if len(filtered) == 0:
            return None
        
        return filtered[['batter', 'sixDistance', 'matchId', 'season', 'dataSource']]
    
    def get_crease_analysis(self, bowler_type=None, team=None):
        """Crease position analysis (height at popping crease)."""
        if not self.has_data() or 'creaseZ' not in self.df.columns:
            return None
        
        filtered = self.df.dropna(subset=['creaseZ']).copy()
        if bowler_type and bowler_type != 'All Types':
            if isinstance(bowler_type, list):
                filtered = filtered[filtered['bowlerType'].isin(bowler_type)]
            else:
                filtered = filtered[filtered['bowlerType'] == bowler_type]
        if team:
            filtered = filtered[filtered['bowling_team'] == team]
        
        if len(filtered) == 0:
            return None
        
        stats = filtered.groupby('bowlerType').agg(
            deliveries=('creaseZ', 'count'),
            avg_height=('creaseZ', 'mean'),
            max_height=('creaseZ', 'max'),
        ).reset_index()
        
        return stats
    
    def get_season_coverage(self):
        """Return number of deliveries per season and data source."""
        if not self.has_data():
            return {}
        
        if 'season' not in self.df.columns:
            return {}
        
        return self.df.groupby(['season', 'dataSource']).size().unstack(fill_value=0).to_dict()


@st.cache_resource
def get_hawkeye_processor():
    """Return a singleton HawkeyeProcessor (cached across reruns)."""
    hp = HawkeyeProcessor()
    hp.load()
    return hp
