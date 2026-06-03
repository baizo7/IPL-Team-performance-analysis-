"""
Analysis module for IPL performance metrics.
Includes phase analysis and matchup statistics.
"""

import pandas as pd
import numpy as np


class PhaseAnalyzer:
    """Analyze team performance across different match phases."""
    
    def __init__(self, df):
        """
        Initialize the analyzer with data.
        
        Args:
            df: DataFrame with IPL ball-by-ball data
        """
        self.df = df
    
    def calculate_phase_metrics(self, team_name):
        """
        Calculate run rate and other metrics for each phase.
        
        Args:
            team_name: Name of the team to analyze
            
        Returns:
            DataFrame with metrics by phase
        """
        team_data = self.df[self.df['batting_team'] == team_name].copy()
        
        if team_data.empty:
            return pd.DataFrame()
        
        # Group by phase
        phase_stats = []
        
        for phase in ['Powerplay', 'Middle', 'Death']:
            phase_data = team_data[team_data['phase'] == phase]
            
            if phase_data.empty:
                continue
            
            # Calculate metrics
            total_runs = phase_data['runs'].sum() + phase_data['extras'].sum()
            total_balls = len(phase_data)
            total_wickets = phase_data['is_wicket'].sum()
            boundaries = len(phase_data[phase_data['runs'].isin([4, 6])])
            fours = len(phase_data[phase_data['runs'] == 4])
            sixes = len(phase_data[phase_data['runs'] == 6])
            
            # Calculate rates
            run_rate = (total_runs / total_balls) * 6 if total_balls > 0 else 0
            strike_rate = (total_runs / total_balls) * 100 if total_balls > 0 else 0
            boundary_percentage = (boundaries / total_balls) * 100 if total_balls > 0 else 0
            
            phase_stats.append({
                'phase': phase,
                'total_runs': total_runs,
                'total_balls': total_balls,
                'total_wickets': total_wickets,
                'run_rate': round(run_rate, 2),
                'strike_rate': round(strike_rate, 2),
                'boundaries': boundaries,
                'fours': fours,
                'sixes': sixes,
                'boundary_percentage': round(boundary_percentage, 2)
            })
        
        return pd.DataFrame(phase_stats)
    
    def compare_teams(self, team1, team2):
        """
        Compare phase performance between two teams.
        
        Args:
            team1: First team name
            team2: Second team name
            
        Returns:
            Dictionary with comparison data for both teams
        """
        team1_metrics = self.calculate_phase_metrics(team1)
        team2_metrics = self.calculate_phase_metrics(team2)
        
        team1_metrics['team'] = team1
        team2_metrics['team'] = team2
        
        return {
            'team1': team1_metrics,
            'team2': team2_metrics,
            'combined': pd.concat([team1_metrics, team2_metrics], ignore_index=True)
        }


class MatchupAnalyzer:
    """Analyze batter vs bowler type matchups."""
    
    def __init__(self, df):
        """
        Initialize the analyzer with data.
        
        Args:
            df: DataFrame with IPL ball-by-ball data
        """
        self.df = df
    
    def calculate_batter_vs_bowler_type(self, batter_name=None, team_name=None):
        """
        Calculate strike rate and dismissals for batter(s) vs bowler types.
        
        Args:
            batter_name: Specific batter name (optional)
            team_name: Team name to analyze all batters from (optional)
            
        Returns:
            DataFrame with matchup statistics
        """
        # Filter data
        if batter_name:
            data = self.df[self.df['batter'] == batter_name].copy()
        elif team_name:
            data = self.df[self.df['batting_team'] == team_name].copy()
        else:
            data = self.df.copy()
        
        if data.empty or 'bowler_type' not in data.columns:
            return pd.DataFrame()
        
        # Group by batter and bowler type
        matchup_stats = []
        
        batters = data['batter'].unique()
        bowler_types = data['bowler_type'].unique()
        
        for batter in batters:
            batter_data = data[data['batter'] == batter]
            
            for bowler_type in bowler_types:
                matchup_data = batter_data[batter_data['bowler_type'] == bowler_type]
                
                if matchup_data.empty:
                    continue
                
                total_runs = matchup_data['runs'].sum()
                total_balls = len(matchup_data)
                dismissals = matchup_data['is_wicket'].sum()
                
                strike_rate = (total_runs / total_balls) * 100 if total_balls > 0 else 0
                dismissal_rate = (dismissals / total_balls) * 100 if total_balls > 0 else 0
                
                matchup_stats.append({
                    'batter': batter,
                    'bowler_type': bowler_type,
                    'balls_faced': total_balls,
                    'runs_scored': total_runs,
                    'dismissals': dismissals,
                    'strike_rate': round(strike_rate, 2),
                    'dismissal_rate': round(dismissal_rate, 2)
                })
        
        return pd.DataFrame(matchup_stats)
    
    def create_heatmap_data(self, team_name, metric='strike_rate'):
        """
        Create a pivot table for heatmap visualization.
        
        Args:
            team_name: Team name
            metric: Metric to display ('strike_rate' or 'dismissal_rate')
            
        Returns:
            Pivot table suitable for heatmap
        """
        matchup_df = self.calculate_batter_vs_bowler_type(team_name=team_name)
        
        if matchup_df.empty:
            return pd.DataFrame()
        
        # Filter batters with sufficient data (at least 10 balls)
        significant_batters = matchup_df.groupby('batter')['balls_faced'].sum()
        significant_batters = significant_batters[significant_batters >= 10].index.tolist()
        
        matchup_df = matchup_df[matchup_df['batter'].isin(significant_batters)]
        
        # Create pivot table
        if not matchup_df.empty:
            pivot = matchup_df.pivot_table(
                values=metric,
                index='batter',
                columns='bowler_type',
                aggfunc='mean',
                fill_value=0
            )
            return pivot
        
        return pd.DataFrame()
    
    def get_top_matchups(self, team_name, n=10):
        """
        Get top performing matchups for a team.
        
        Args:
            team_name: Team name
            n: Number of top matchups to return
            
        Returns:
            DataFrame with top matchups sorted by strike rate
        """
        matchup_df = self.calculate_batter_vs_bowler_type(team_name=team_name)
        
        if matchup_df.empty:
            return pd.DataFrame()
        
        # Filter for sufficient sample size
        matchup_df = matchup_df[matchup_df['balls_faced'] >= 6]
        
        # Sort by strike rate and return top n
        top_matchups = matchup_df.sort_values('strike_rate', ascending=False).head(n)
        
        return top_matchups


class PerformanceMetrics:
    """Calculate overall team and player performance metrics."""
    
    def __init__(self, df):
        """
        Initialize with data.
        
        Args:
            df: DataFrame with IPL ball-by-ball data
        """
        self.df = df
    
    def team_summary(self, team_name):
        """
        Get overall team performance summary.
        
        Args:
            team_name: Team name
            
        Returns:
            Dictionary with team statistics
        """
        team_data = self.df[self.df['batting_team'] == team_name]
        
        if team_data.empty:
            return {}
        
        total_runs = team_data['runs'].sum() + team_data['extras'].sum()
        total_balls = len(team_data)
        total_wickets = team_data['is_wicket'].sum()
        total_matches = team_data['match_id'].nunique() if 'match_id' in team_data.columns else 0
        
        return {
            'team': team_name,
            'total_matches': total_matches,
            'total_runs': total_runs,
            'total_balls': total_balls,
            'total_wickets': total_wickets,
            'overall_run_rate': round((total_runs / total_balls) * 6, 2) if total_balls > 0 else 0,
            'overall_strike_rate': round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0,
            'avg_runs_per_match': round(total_runs / total_matches, 2) if total_matches > 0 else 0
        }
    
    def top_batters(self, team_name, n=5):
        """
        Get top batters for a team.
        
        Args:
            team_name: Team name
            n: Number of top batters to return
            
        Returns:
            DataFrame with top batters
        """
        team_data = self.df[self.df['batting_team'] == team_name]
        
        if team_data.empty:
            return pd.DataFrame()
        
        batter_stats = team_data.groupby('batter').agg({
            'runs': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        
        batter_stats.columns = ['batter', 'runs', 'balls', 'dismissals']
        batter_stats['strike_rate'] = (batter_stats['runs'] / batter_stats['balls'] * 100).round(2)
        batter_stats['average'] = (batter_stats['runs'] / batter_stats['dismissals']).round(2)
        batter_stats['average'] = batter_stats['average'].replace([np.inf, -np.inf], batter_stats['runs'])
        
        top = batter_stats.sort_values('runs', ascending=False).head(n)
        
        return top
