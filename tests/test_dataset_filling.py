import unittest
import pandas as pd
import json
from pathlib import Path
from ipl_analytics.charts.bowling import calculate_bowler_telemetry_averages
from ipl_analytics.services.hawkeye import get_hawkeye_processor

BASE_DIR = Path(__file__).parent.parent


class TestDatasetFilling(unittest.TestCase):

    def test_hawkeye_bowler_styles_json(self):
        json_file = BASE_DIR / 'hawkeye_bowler_styles.json'
        self.assertTrue(json_file.exists(), "hawkeye_bowler_styles.json must exist")

        with open(json_file, 'r', encoding='utf-8') as f:
            styles = json.load(f)

        manual = styles.get('manual', {})
        self.assertIn("Suryakumar Yadav", manual)
        self.assertIn("SA Yadav", manual)

    def test_suryakumar_yadav_telemetry(self):
        hp = get_hawkeye_processor()
        self.assertTrue(hp.has_data(), "HawkeyeProcessor must have loaded data")

        # Test telemetry calculation for SA Yadav / Suryakumar Yadav
        stats = calculate_bowler_telemetry_averages(None, "Suryakumar Yadav")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['bowler'], "Suryakumar Yadav")
        self.assertTrue(stats['is_real_hawkeye'], "Suryakumar Yadav must have Hawk-Eye tracking data")
        self.assertGreater(stats['avg_speed'], 60.0, "Average release speed should be realistic (>60 km/h)")
        self.assertGreater(stats['total_deliveries'], 0, "Total deliveries should be > 0")

    def test_match_dataset_no_nans(self):
        csv_file = BASE_DIR / 'all_ipl_matches.csv'
        self.assertTrue(csv_file.exists(), "all_ipl_matches.csv must exist")

        df = pd.read_csv(csv_file, low_memory=False)
        self.assertFalse(df['runs_off_bat'].isna().any(), "runs_off_bat should have no NaNs")
        self.assertFalse(df['extras'].isna().any(), "extras should have no NaNs")
        self.assertFalse(df['is_wicket'].isna().any(), "is_wicket should have no NaNs")
        self.assertFalse(df['phase'].isna().any(), "phase should have no NaNs")


if __name__ == '__main__':
    unittest.main()
