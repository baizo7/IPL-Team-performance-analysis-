import unittest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ipl_analytics.services.data_cleaner import clean_teams, clean_venues, remove_duplicates, validate_deliveries


class TestDataCleaner(unittest.TestCase):
    def test_clean_teams(self):
        sample_df = pd.DataFrame({
            'batting_team': ['Delhi Daredevils', 'Kings XI Punjab', 'Mumbai Indians'],
            'bowling_team': ['Royal Challengers Bangalore', 'Deccan Chargers', 'Chennai Super Kings']
        })
        cleaned_df, modified_count = clean_teams(sample_df)
        self.assertEqual(cleaned_df['batting_team'].iloc[0], 'Delhi Capitals')
        self.assertEqual(cleaned_df['batting_team'].iloc[1], 'Punjab Kings')
        self.assertGreater(modified_count, 0)

    def test_clean_venues(self):
        sample_df = pd.DataFrame({
            'venue': ['M. Chinnaswamy Stadium, Bengaluru', 'Feroz Shah Kotla', 'Wankhede Stadium, Mumbai']
        })
        cleaned_df, modified_count = clean_venues(sample_df)
        self.assertEqual(cleaned_df['venue'].iloc[0], 'M Chinnaswamy Stadium')
        self.assertEqual(cleaned_df['venue'].iloc[1], 'Arun Jaitley Stadium')

    def test_remove_duplicates(self):
        sample_df = pd.DataFrame({
            'match_id': [1, 1, 1],
            'innings': [1, 1, 1],
            'over': [1, 1, 1],
            'ball': [1, 1, 2],
            'runs_off_bat': [4, 4, 1]
        })
        cleaned_df, stats = remove_duplicates(sample_df)
        self.assertEqual(len(cleaned_df), 2)
        self.assertEqual(stats['total_duplicates_removed'], 1)


if __name__ == "__main__":
    unittest.main()
