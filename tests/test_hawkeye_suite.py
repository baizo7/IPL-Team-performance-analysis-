import unittest
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hawkeye_processor import HawkeyeProcessor
from hawkeye_simulator import HawkeyeSimulator
from hawkeye_pattern_engine import HawkeyePatternEngine
from ipl_analytics.analytics_engine import (
    calculate_win_probability,
    analyze_toss_venue_impact,
    calculate_player_impact_scores,
    get_season_over_season_comparison
)

class TestHawkeyeSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hp = HawkeyeProcessor()
        cls.hp.load()

    def test_hawkeye_processor_load(self):
        self.assertIsNotNone(self.hp.df)
        self.assertTrue(self.hp.has_data())
        summary = self.hp.get_data_summary()
        self.assertIn('total', summary)
        self.assertGreater(summary['total'], 0)

    def test_hawkeye_processor_team_info(self):
        teams = self.hp.get_teams()
        self.assertIsInstance(teams, list)
        self.assertGreater(len(teams), 0)

    def test_pitch_map_and_wagon_wheel(self):
        pitch_data = self.hp.get_pitch_map_data(team='Chennai Super Kings')
        if pitch_data:
            self.assertIsInstance(pitch_data, list)
            self.assertIn('x', pitch_data[0])
            self.assertIn('y', pitch_data[0])
            
        wagon_data = self.hp.get_wagon_wheel_data(team='Chennai Super Kings', boundary_radius=65.0)
        if wagon_data:
            self.assertIsInstance(wagon_data, list)
            self.assertIn('distance', wagon_data[0])

    def test_hawkeye_simulator(self):
        engine = HawkeyePatternEngine()
        sim = HawkeyeSimulator(pattern_engine=engine)
        self.assertIsNotNone(sim.engine)

    def test_hawkeye_pattern_engine(self):
        engine = HawkeyePatternEngine()
        coords = engine.generate_pitch_coords('fast', n=5)
        self.assertEqual(len(coords), 5)
        speeds = engine.generate_speed('fast', n=5)
        self.assertEqual(len(speeds), 5)

    def test_win_probability(self):
        res = calculate_win_probability(target=180, current_runs=120, overs_bowled=15.0, wickets_lost=3)
        self.assertIn('win_probability_batting', res)
        self.assertGreaterEqual(res['win_probability_batting'], 0.0)
        self.assertLessEqual(res['win_probability_batting'], 100.0)

    def test_player_impact_score(self):
        dummy_df = pd.DataFrame([{
            'striker': 'MS Dhoni',
            'runs_off_bat': 4,
            'ball': 1,
            'phase': 'Death',
            'batting_team': 'Chennai Super Kings',
            'bowling_team': 'Mumbai Indians',
            'bowler': 'Jasprit Bumrah',
            'is_wicket': 0
        }])
        impact = calculate_player_impact_scores(dummy_df, team='Chennai Super Kings')
        self.assertIsInstance(impact, list)
        self.assertGreater(len(impact), 0)

if __name__ == '__main__':
    unittest.main()
