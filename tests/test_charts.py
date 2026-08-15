"""
Unit tests for Plotly chart generators.
"""

import unittest
import pandas as pd
from ipl_analytics.charts.phase_analysis import create_phase_efficiency_matrix_chart, create_phase_overlay_worm_chart
from ipl_analytics.charts.batting import create_runs_distribution_chart, create_strike_rate_comparison
from ipl_analytics.charts.bowling import create_bowler_economy_chart


class TestChartGenerators(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {
                'match_id': 1, 'innings': 1, 'over': 1, 'ball': 1,
                'batting_team': 'Chennai Super Kings', 'bowling_team': 'Delhi Capitals',
                'batter': 'MS Dhoni', 'bowler': 'J Bumrah', 'runs_off_bat': 4,
                'total_runs': 4, 'is_wicket': 0, 'phase': 'Powerplay (1-6)',
                'venue': 'Wankhede Stadium', 'bowler_type': 'Right-arm fast'
            },
            {
                'match_id': 1, 'innings': 1, 'over': 1, 'ball': 2,
                'batting_team': 'Chennai Super Kings', 'bowling_team': 'Delhi Capitals',
                'batter': 'MS Dhoni', 'bowler': 'J Bumrah', 'runs_off_bat': 6,
                'total_runs': 6, 'is_wicket': 0, 'phase': 'Powerplay (1-6)',
                'venue': 'Wankhede Stadium', 'bowler_type': 'Right-arm fast'
            },
            {
                'match_id': 1, 'innings': 2, 'over': 1, 'ball': 1,
                'batting_team': 'Delhi Capitals', 'bowling_team': 'Chennai Super Kings',
                'batter': 'R Pant', 'bowler': 'R Jadeja', 'runs_off_bat': 1,
                'total_runs': 1, 'is_wicket': 1, 'phase': 'Powerplay (1-6)',
                'venue': 'Wankhede Stadium', 'bowler_type': 'Spin'
            }
        ])

    def test_create_phase_efficiency_matrix_chart(self):
        fig = create_phase_efficiency_matrix_chart(self.df, 'Chennai Super Kings', 'Delhi Capitals')
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.data) >= 1)

    def test_create_runs_distribution_chart(self):
        fig = create_runs_distribution_chart(self.df, 'Chennai Super Kings')
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.data) == 1)

    def test_create_bowler_economy_chart(self):
        fig = create_bowler_economy_chart(self.df, 'Delhi Capitals')
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main()
