"""
Unit tests for data cleaning pipeline edge cases.
"""

import pandas as pd
import numpy as np
from ipl_analytics.services.data_cleaner import build_clean_dataset, clean_teams, clean_venues


def test_clean_teams_mapping():
    df = pd.DataFrame({'batting_team': ['Delhi Daredevils', 'Kings XI Punjab', 'Chennai Super Kings']})
    cleaned_df, count = clean_teams(df)
    assert cleaned_df['batting_team'].iloc[0] == 'Delhi Capitals'
    assert cleaned_df['batting_team'].iloc[1] == 'Punjab Kings'
    assert count == 2


def test_empty_dataframe_cleaning():
    df = pd.DataFrame()
    cleaned_df, report = build_clean_dataset(df)
    assert cleaned_df.empty
    assert report['original_rows'] == 0


def test_duplicate_deliveries_removal():
    df = pd.DataFrame([
        {'match_id': 1, 'innings': 1, 'over': 1, 'ball': 1, 'batting_team': 'CSK', 'bowling_team': 'DC', 'venue': 'Wankhede'},
        {'match_id': 1, 'innings': 1, 'over': 1, 'ball': 1, 'batting_team': 'CSK', 'bowling_team': 'DC', 'venue': 'Wankhede'},
    ])
    cleaned_df, report = build_clean_dataset(df)
    assert len(cleaned_df) == 1
    assert report['duplicates_removed'] == 1
