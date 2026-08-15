"""
Hawk-Eye Pattern Engine - Learns trajectory distributions from real 2009-2021 Hawk-Eye data.
Provides realistic synthetic coordinate generation for newer seasons.
"""
import json
import numpy as np
import pandas as pd
import os

class HawkeyePatternEngine:
    def __init__(self, pattern_file=None):
        self.distributions = None
        self.field_distributions = None
        self.bowler_lookup = {}
        
        if pattern_file and os.path.exists(pattern_file):
            self.load_patterns(pattern_file)
    
    def load_patterns(self, pattern_file):
        with open(pattern_file) as f:
            data = json.load(f)
        self.distributions = data['bowler_types']
        self.field_distributions = data['field_positions']
    
    def learn_from_data(self, df):
        """Learn distributions from real Hawk-Eye DataFrame."""
        style_map = {
            'FAST_SEAM': 'fast', 'SEAM': 'medium', 'MEDIUM_SEAM': 'medium',
            'LEG_SPIN': 'spin', 'OFF_SPIN': 'spin', 'ORTHODOX': 'spin', 'UNORTHODOX': 'spin',
        }
        df = df.copy()
        df['bowlerType'] = df['bowlingStyle'].map(style_map)
        
        valid = df[df['pitchX'].notna() & df['pitchY'].notna()].copy()
        valid = valid[(valid['pitchX'] >= -2.5) & (valid['pitchX'] <= 2.5)]
        valid = valid[(valid['pitchY'] >= 0) & (valid['pitchY'] <= 22)]
        
        valid = valid[valid['stumpsX'].notna() & valid['stumpsY'].notna()]
        valid = valid[(valid['stumpsX'] >= -1.5) & (valid['stumpsX'] <= 1.5)]
        valid = valid[(valid['stumpsY'] >= -0.5) & (valid['stumpsY'] <= 2.0)]
        
        valid['speed_kmh'] = valid['ballSpeed'] * 3.6

        self.distributions = {}
        for bt, grp in valid.groupby('bowlerType'):
            self.distributions[bt] = {
                'pitchX_mu': float(grp['pitchX'].mean()),
                'pitchX_sigma': float(grp['pitchX'].std()),
                'pitchY_mu': float(grp['pitchY'].mean()),
                'pitchY_sigma': float(grp['pitchY'].std()),
                'stumpsX_mu': float(grp['stumpsX'].mean()),
                'stumpsX_sigma': float(grp['stumpsX'].std()),
                'stumpsY_mu': float(grp['stumpsY'].mean()),
                'stumpsY_sigma': float(grp['stumpsY'].std()),
                'speed_mu': float(grp['speed_kmh'].mean()),
                'speed_sigma': float(grp['speed_kmh'].std()),
                'count': len(grp),
            }

        self.field_distributions = {}
        fv = valid[valid['fieldX'].notna() & valid['fieldY'].notna()]
        for runs in [0, 1, 2, 3, 4, 6]:
            sub = fv[fv['runs'] == runs]
            if len(sub) > 10:
                self.field_distributions[str(runs)] = {
                    'fieldX_mu': float(sub['fieldX'].mean()),
                    'fieldX_sigma': float(sub['fieldX'].std()),
                    'fieldY_mu': float(sub['fieldY'].mean()),
                    'fieldY_sigma': float(sub['fieldY'].std()),
                    'count': len(sub),
                }
        
        self._build_bowler_lookup(df)
    
    def _build_bowler_lookup(self, df):
        """Build bowler name -> bowler type mapping from real data."""
        style_map = {
            'FAST_SEAM': 'fast', 'SEAM': 'medium', 'MEDIUM_SEAM': 'medium',
            'LEG_SPIN': 'spin', 'OFF_SPIN': 'spin', 'ORTHODOX': 'spin', 'UNORTHODOX': 'spin',
        }
        df = df.copy()
        df['bowlerType'] = df['bowlingStyle'].map(style_map)
        for name, grp in df.groupby('bowler'):
            types = grp['bowlerType'].mode()
            if len(types) > 0:
                self.bowler_lookup[name.upper()] = types.iloc[0]
    
    def get_bowler_type(self, bowler_name):
        """Get bowler type, defaulting to medium for unknown bowlers."""
        if not bowler_name or pd.isna(bowler_name):
            return 'medium'
        return self.bowler_lookup.get(bowler_name.upper(), 'medium')
    
    def generate_pitch_coords(self, bowler_type, n=1):
        """Generate synthetic pitchX, pitchY coordinates."""
        if not self.distributions:
            return np.zeros((n, 2))
        dist = self.distributions.get(bowler_type, self.distributions.get('medium'))
        if dist is None:
            return np.zeros((n, 2))
        
        pitchX = np.random.normal(dist['pitchX_mu'], dist['pitchX_sigma'], n)
        pitchY = np.random.normal(dist['pitchY_mu'], dist['pitchY_sigma'], n)
        
        pitchX = np.clip(pitchX, -2.5, 2.5)
        pitchY = np.clip(pitchY, 0, 22)
        
        return np.column_stack([pitchX, pitchY])
    
    def generate_stump_coords(self, bowler_type, n=1):
        """Generate synthetic stumpsX, stumpsY coordinates."""
        if not self.distributions:
            return np.zeros((n, 2))
        dist = self.distributions.get(bowler_type, self.distributions.get('medium'))
        if dist is None:
            return np.zeros((n, 2))
        
        sx = np.random.normal(dist['stumpsX_mu'], dist['stumpsX_sigma'], n)
        sy = np.random.normal(dist['stumpsY_mu'], dist['stumpsY_sigma'], n)
        
        sx = np.clip(sx, -1.5, 1.5)
        sy = np.clip(sy, -0.5, 2.0)
        
        return np.column_stack([sx, sy])
    
    def generate_speed(self, bowler_type, n=1):
        """Generate synthetic ball speed in km/h."""
        if not self.distributions:
            return np.full(n, 120.0)
        dist = self.distributions.get(bowler_type, self.distributions.get('medium'))
        if dist is None:
            return np.full(n, 120.0)
        
        speed = np.random.normal(dist['speed_mu'], dist['speed_sigma'], n)
        return np.clip(speed, 60, 160)
    
    def generate_field_coords(self, runs, n=1):
        """Generate synthetic fieldX, fieldY based on runs scored."""
        if not self.field_distributions:
            return np.zeros((n, 2))
        fd = self.field_distributions.get(str(runs))
        if fd is None:
            # Default: dot ball area
            fd = self.field_distributions.get('0', {'fieldX_mu': 24.5, 'fieldX_sigma': 24.4, 'fieldY_mu': 19.4, 'fieldY_sigma': 18.8})
        
        fx = np.random.normal(fd['fieldX_mu'], fd['fieldX_sigma'], n)
        fy = np.random.normal(fd['fieldY_mu'], fd['fieldY_sigma'], n)
        fx = np.clip(fx, 0, 100)
        fy = np.clip(fy, 0, 100)
        
        return np.column_stack([fx, fy])
    
    def generate_swing(self, bowler_type, n=1):
        """Generate synthetic swing amount (degrees/centimeters)."""
        dist = self.distributions.get(bowler_type, self.distributions.get('medium'))
        base_swing = {'fast': 1.2, 'medium': 0.8, 'spin': 2.5}.get(bowler_type, 1.0)
        sigma = {'fast': 0.8, 'medium': 0.6, 'spin': 1.2}.get(bowler_type, 0.7)
        swing = np.random.normal(base_swing, sigma, n)
        return np.clip(swing, 0, 6)
    
    def generate_deviation(self, bowler_type, n=1):
        """Generate synthetic deviation after pitching."""
        dist = self.distributions.get(bowler_type, self.distributions.get('medium'))
        base_dev = {'fast': 0.3, 'medium': 0.5, 'spin': 3.0}.get(bowler_type, 0.5)
        sigma = {'fast': 0.3, 'medium': 0.4, 'spin': 1.5}.get(bowler_type, 0.4)
        dev = np.random.normal(base_dev, sigma, n)
        return np.clip(dev, 0, 8)
    
    def generate_crease_z(self, n=1):
        """Generate crease z-coordinate (height at crease)."""
        return np.random.normal(0.8, 0.3, n)  # meters above ground
    
    def generate_six_distance(self, n=1):
        """Generate six hit distance in meters."""
        return np.random.normal(78, 12, n)
