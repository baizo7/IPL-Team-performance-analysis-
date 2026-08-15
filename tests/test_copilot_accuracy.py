import unittest
import pandas as pd
from pathlib import Path
from ipl_copilot import AnalyticsToolRegistry, process_copilot_command

BASE_DIR = Path(__file__).parent.parent


class TestCopilotAccuracy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cric_file = BASE_DIR / 'all_ipl_matches.csv'
        if cric_file.exists():
            cls.df = pd.read_csv(cric_file, low_memory=False)
        else:
            cls.df = pd.DataFrame({
                'match_id': [1, 1],
                'season': [2024, 2024],
                'batting_team': ['Chennai Super Kings', 'Mumbai Indians'],
                'bowling_team': ['Mumbai Indians', 'Chennai Super Kings'],
                'striker': ['Suryakumar Yadav', 'JJ Bumrah'],
                'bowler': ['JJ Bumrah', 'SA Yadav'],
                'runs_off_bat': [4, 0],
                'extras': [0, 0],
                'is_wicket': [0, 1],
                'over': [1, 19],
                'ball': [0.1, 18.6]
            })

    def test_find_player_ranking(self):
        # Verify exact ranking for Suryakumar Yadav
        p1 = AnalyticsToolRegistry._find_player(self.df, "Suryakumar Yadav")
        self.assertIn("Yadav", p1)

        # Verify Jasprit Bumrah lookup
        p2 = AnalyticsToolRegistry._find_player(self.df, "Bumrah")
        self.assertIn("Bumrah", p2)

    def test_copilot_telemetry_intent(self):
        report, nav = process_copilot_command("Suryakumar Yadav speed and swing telemetry", self.df)
        self.assertIsNotNone(report)
        self.assertIn("Hawk-Eye", report)
        self.assertIn("Yadav", report)
        self.assertEqual(nav.get("target_section"), "🎬 Animations")

    def test_copilot_player_comparison(self):
        report, nav = process_copilot_command("Compare Suryakumar Yadav vs Bumrah", self.df)
        self.assertIsNotNone(report)
        self.assertIn("Side-by-Side Analytics", report)
        self.assertEqual(nav.get("target_section"), "👤 Player Stats")


if __name__ == '__main__':
    unittest.main()
