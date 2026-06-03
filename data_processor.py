"""
Data processing module for IPL ball-by-ball data.
Handles loading and cleaning data from Cricsheet CSV format.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json


class IPLDataProcessor:
    """Process IPL ball-by-ball data from Cricsheet format."""
    
    def __init__(self, data_path='data'):
        """
        Initialize the data processor.
        
        Args:
            data_path: Path to directory containing IPL CSV files
        """
        self.data_path = Path(data_path)
        self.df = None
        
    def load_csv_data(self, file_pattern='*.csv'):
        """
        Load IPL data from CSV files.
        
        Args:
            file_pattern: Glob pattern to match CSV files
            
        Returns:
            DataFrame with combined data from all matching files
        """
        csv_files = list(self.data_path.glob(file_pattern))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_path}")
        
        dfs = []
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        if dfs:
            self.df = pd.concat(dfs, ignore_index=True)
            self._clean_data()
            return self.df
        else:
            raise ValueError("No data could be loaded from CSV files")
    
    def _clean_data(self):
        """Clean and standardize the loaded data."""
        if self.df is None:
            return
        
        # Standardize column names (handle variations in Cricsheet format)
        column_mapping = {
            'batting_team': 'batting_team',
            'bowling_team': 'bowling_team',
            'ball': 'ball',
            'batsman': 'batter',
            'striker': 'batter',
            'bowler': 'bowler',
            'runs_off_bat': 'runs',
            'batsman_runs': 'runs',
            'extras': 'extras',
            'wicket_type': 'wicket_type',
            'player_dismissed': 'player_dismissed',
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in self.df.columns and new_name != old_name:
                self.df.rename(columns={old_name: new_name}, inplace=True)
        
        # Extract over number from ball (e.g., 0.1 -> over 1)
        if 'ball' in self.df.columns:
            self.df['over'] = self.df['ball'].apply(lambda x: int(float(x)) + 1)
        
        # Ensure numeric columns
        numeric_cols = ['runs', 'extras']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Add phase categorization
        if 'over' in self.df.columns:
            self.df['phase'] = self.df['over'].apply(self._categorize_phase)
        
        # Handle wickets
        if 'wicket_type' in self.df.columns:
            self.df['is_wicket'] = self.df['wicket_type'].notna()
        else:
            self.df['is_wicket'] = False
    
    @staticmethod
    def _categorize_phase(over):
        """Categorize over into match phase."""
        if over <= 6:
            return 'Powerplay'
        elif over <= 15:
            return 'Middle'
        else:
            return 'Death'
    
    def get_team_data(self, team_name):
        """
        Get all data for a specific team (batting).
        
        Args:
            team_name: Name of the team
            
        Returns:
            DataFrame filtered for the specified team
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv_data() first.")
        
        return self.df[self.df['batting_team'] == team_name].copy()
    
    def get_available_teams(self):
        """Get list of all teams in the dataset."""
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv_data() first.")
        
        return sorted(self.df['batting_team'].unique().tolist())
    
    def create_sample_data(self):
        """
        Create sample IPL data for testing when real data is not available.
        
        Returns:
            DataFrame with sample IPL ball-by-ball data
        """
        np.random.seed(42)
        
        teams = ['Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore', 
                 'Kolkata Knight Riders', 'Delhi Capitals', 'Punjab Kings']
        
        batters_by_team = {
            'Chennai Super Kings': ['MS Dhoni', 'Ruturaj Gaikwad', 'Devon Conway', 'Ravindra Jadeja'],
            'Mumbai Indians': ['Rohit Sharma', 'Ishan Kishan', 'Suryakumar Yadav', 'Tilak Varma'],
            'Royal Challengers Bangalore': ['Virat Kohli', 'Faf du Plessis', 'Glenn Maxwell', 'Dinesh Karthik'],
            'Kolkata Knight Riders': ['Shreyas Iyer', 'Venkatesh Iyer', 'Andre Russell', 'Nitish Rana'],
            'Delhi Capitals': ['David Warner', 'Prithvi Shaw', 'Rishabh Pant', 'Axar Patel'],
            'Punjab Kings': ['Shikhar Dhawan', 'Jonny Bairstow', 'Liam Livingstone', 'Jitesh Sharma']
        }
        
        bowlers = ['Jasprit Bumrah', 'Rashid Khan', 'Yuzvendra Chahal', 'Kagiso Rabada',
                   'Mohammed Siraj', 'Trent Boult', 'Kuldeep Yadav', 'Bhuvneshwar Kumar']
        
        bowler_types = {
            'Jasprit Bumrah': 'Fast',
            'Rashid Khan': 'Leg Spin',
            'Yuzvendra Chahal': 'Leg Spin',
            'Kagiso Rabada': 'Fast',
            'Mohammed Siraj': 'Fast Medium',
            'Trent Boult': 'Fast',
            'Kuldeep Yadav': 'Left-Arm Wrist Spin',
            'Bhuvneshwar Kumar': 'Fast Medium'
        }
        
        data = []
        match_id = 1
        
        # Generate data for multiple matches
        for _ in range(50):  # 50 matches
            team1, team2 = np.random.choice(teams, 2, replace=False)
            
            # First innings
            for over in range(1, 21):  # 20 overs
                for ball_num in range(1, 7):  # 6 balls per over
                    batter = np.random.choice(batters_by_team[team1])
                    bowler = np.random.choice(bowlers)
                    bowler_type = bowler_types[bowler]
                    
                    # Simulate runs (weighted towards singles and boundaries)
                    runs = np.random.choice([0, 1, 2, 3, 4, 6], p=[0.3, 0.35, 0.15, 0.05, 0.1, 0.05])
                    extras = np.random.choice([0, 1], p=[0.9, 0.1])
                    
                    # Simulate wickets (5% chance)
                    is_wicket = np.random.random() < 0.05
                    wicket_type = np.random.choice(['caught', 'bowled', 'lbw', 'stumped']) if is_wicket else None
                    
                    data.append({
                        'match_id': match_id,
                        'batting_team': team1,
                        'bowling_team': team2,
                        'over': over,
                        'ball': ball_num,
                        'batter': batter,
                        'bowler': bowler,
                        'bowler_type': bowler_type,
                        'runs': runs,
                        'extras': extras,
                        'is_wicket': is_wicket,
                        'wicket_type': wicket_type,
                        'player_dismissed': batter if is_wicket else None,
                        'phase': self._categorize_phase(over)
                    })
            
            # Second innings
            for over in range(1, 21):
                for ball_num in range(1, 7):
                    batter = np.random.choice(batters_by_team[team2])
                    bowler = np.random.choice(bowlers)
                    bowler_type = bowler_types[bowler]
                    
                    runs = np.random.choice([0, 1, 2, 3, 4, 6], p=[0.3, 0.35, 0.15, 0.05, 0.1, 0.05])
                    extras = np.random.choice([0, 1], p=[0.9, 0.1])
                    is_wicket = np.random.random() < 0.05
                    wicket_type = np.random.choice(['caught', 'bowled', 'lbw', 'stumped']) if is_wicket else None
                    
                    data.append({
                        'match_id': match_id,
                        'batting_team': team2,
                        'bowling_team': team1,
                        'over': over,
                        'ball': ball_num,
                        'batter': batter,
                        'bowler': bowler,
                        'bowler_type': bowler_type,
                        'runs': runs,
                        'extras': extras,
                        'is_wicket': is_wicket,
                        'wicket_type': wicket_type,
                        'player_dismissed': batter if is_wicket else None,
                        'phase': self._categorize_phase(over)
                    })
            
            match_id += 1
        
        self.df = pd.DataFrame(data)
        return self.df
